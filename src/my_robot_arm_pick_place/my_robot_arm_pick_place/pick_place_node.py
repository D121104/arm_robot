#!/usr/bin/env python3
"""
Physical-contact Gazebo pick-and-place task for five Panda objects.

This node is simulation-only. Gazebo owns object physics: the node never
teleports an object while picking or placing. A lift is permitted only after
both finger contact sensors report the currently selected object.
"""

from dataclasses import dataclass
import json
import math
import os
import random
import threading
import time
from typing import Callable

from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from moveit.core.robot_state import RobotState
from moveit.planning import MoveItPy
from moveit_configs_utils import MoveItConfigsBuilder
import numpy as np
import rclpy
from rclpy.node import Node
from ros_gz_interfaces.msg import Contacts


@dataclass(frozen=True)
class TaskObject:
    """Validated static description of a Gazebo object and its target pad."""

    object_id: str
    gazebo_model: str
    shape: str
    dimensions: tuple[float, ...]
    gripper_opening: float
    pick_pose: tuple[float, float, float]
    place_pose: tuple[float, float, float]
    grasp_yaw_deg: float


class PickPlaceNode(Node):
    """Plan and execute contact-validated top-down pick-and-place in Gazebo."""

    ARM_CONTROLLER = 'panda_arm_controller'
    HAND_CONTROLLER = 'panda_hand_controller'
    LEFT_CONTACT_TOPIC = '/panda/left_finger/contact'
    RIGHT_CONTACT_TOPIC = '/panda/right_finger/contact'

    def __init__(self) -> None:
        """Initialize MoveIt, validated task parameters, and contact streams."""
        super().__init__('pick_place_node')
        self._declare_parameters()
        self._load_parameters()
        self._stop_event = threading.Event()
        self._contact_lock = threading.Lock()
        self._finger_contacts: dict[str, tuple[set[str], float]] = {
            'left': (set(), 0.0),
            'right': (set(), 0.0),
        }
        self._last_contact_models: dict[str, set[str]] = {
            'left': set(),
            'right': set(),
        }
        self.create_subscription(
            Contacts,
            self.LEFT_CONTACT_TOPIC,
            lambda message: self._contact_callback('left', message),
            10,
        )
        self.create_subscription(
            Contacts,
            self.RIGHT_CONTACT_TOPIC,
            lambda message: self._contact_callback('right', message),
            10,
        )
        self._initialize_moveit()
        self._worker: threading.Thread | None = None
        if self.autorun:
            self._worker = threading.Thread(
                target=self.run,
                name='pick-place-worker',
                daemon=True,
            )
            self._worker.start()

    def _initialize_moveit(self) -> None:
        """Create MoveItPy with the backend matching the selected simulation mode."""
        hardware_type = (
            'gz_ros2_control' if self.use_sim_time else 'mock_components'
        )
        urdf_path = os.path.join(
            get_package_share_directory('my_robot_arm_description'),
            'urdf',
            'my_robot_arm.urdf.xacro',
        )
        moveit_config = (
            MoveItConfigsBuilder(
                'panda', package_name='my_robot_arm_moveit_config'
            )
            .robot_description(
                file_path=urdf_path,
                mappings={'ros2_control_hardware_type': hardware_type},
            )
            .moveit_cpp(file_path='config/moveit_cpp.yaml')
            .planning_pipelines(pipelines=['ompl'])
            .to_moveit_configs()
        )
        config_dict = moveit_config.to_dict()
        # MoveItPy owns a private C++ node. It must use Gazebo time so its
        # current-state monitor accepts simulation-stamped joint states. Jazzy
        # exposes TimeSource's clock QoS as parameters; set each valid value
        # explicitly to prevent an invalid inherited override at declaration.
        config_dict.update({
            'use_sim_time': self.use_sim_time,
            # Gazebo may report a finger position infinitesimally beyond its
            # 0.04 m upper bound. Accept only this small numerical error in
            # the planning start state; the physical URDF limit is unchanged.
            'start_state_max_bounds_error': 0.001,
            # A physical gripper intentionally stops short of its zero-width
            # target when it contacts an object.  Keep MoveIt from cancelling
            # that valid contact-limited close before the controller can
            # report its tolerance-based success.
            'trajectory_execution.allowed_execution_duration_scaling': 3.0,
            'trajectory_execution.allowed_goal_duration_margin': 5.0,
            # Gazebo physics causes small joint deviations while the arm holds
            # an object. The default 0.01 rad tolerance from
            # moveit_controllers.yaml is too strict and rejects valid
            # post-grasp trajectories.
            'trajectory_execution.allowed_start_tolerance': 0.05,
            'qos_overrides./clock.subscription.depth': 1,
            'qos_overrides./clock.subscription.durability': 'volatile',
            'qos_overrides./clock.subscription.history': 'keep_last',
            'qos_overrides./clock.subscription.reliability': 'reliable',
        })
        self.get_logger().info(
            'Initializing MoveItPy with use_sim_time=%s, start-state '
            'bounds tolerance=0.001, trajectory execution allowance '
            '(scaling=3.0, goal margin=5.0 s, start tolerance=0.05 rad), '
            'and ClockQoS (keep_last, depth=1, reliable, volatile).'
            % self.use_sim_time
        )
        self.moveit = MoveItPy(
            node_name='pick_place_moveit_py', config_dict=config_dict
        )
        self.arm = self.moveit.get_planning_component(self.arm_group)
        self.gripper = self.moveit.get_planning_component(self.gripper_group)

    def _declare_parameters(self) -> None:
        """Declare every task parameter with safe simulation defaults."""
        defaults = {
            'arm_group_name': 'panda_arm',
            'gripper_group_name': 'hand',
            'base_frame': 'panda_link0',
            'tool_link': 'panda_link8',
            'use_physical_contacts': True,
            'planning_only': False,
            'grasp_z_offset': 0.103,
            'place_z_offset': 0.103,
            'approach_height': 0.10,
            'lift_height': 0.12,
            'place_approach_height': 0.10,
            'retreat_height': 0.12,
            'planning_attempts': 5,
            'grasp_attempts': 2,
            'planning_retry_delay': 0.5,
            'contact_timeout': 2.0,
            'contact_settle_duration': 0.20,
            'contact_max_age': 1.0,
            # Close the physical gripper in finite, reachable increments and
            # stop as soon as both fingers contact the requested object.
            'gripper_close_step': 0.005,
            'gripper_close_settle_duration': 0.10,
            'startup_delay': 8.0,
            'random_seed': -1,
            'autorun': True,
            'run_forever': False,
            'object_catalog_json': '[]',
            'grasp_orientation': [1.0, 0.0, 0.0, 0.0],
            'place_orientation': [1.0, 0.0, 0.0, 0.0],
        }
        for name, value in defaults.items():
            self.declare_parameter(name, value)

    def _parameter_value(self, name: str):
        """Return a declared ROS parameter value."""
        return self.get_parameter(name).value

    def _load_parameters(self) -> None:
        """Load scalar parameters and validate the five-object JSON catalog."""
        value = self._parameter_value
        self.arm_group = str(value('arm_group_name'))
        self.gripper_group = str(value('gripper_group_name'))
        self.base_frame = str(value('base_frame'))
        self.tool_link = str(value('tool_link'))
        self.use_sim_time = bool(value('use_sim_time'))
        self.use_contacts = bool(value('use_physical_contacts'))
        self.planning_only = bool(value('planning_only'))
        self.autorun = bool(value('autorun'))
        self.run_forever = bool(value('run_forever'))
        self.grasp_z_offset = float(value('grasp_z_offset'))
        self.place_z_offset = float(value('place_z_offset'))
        self.approach_height = float(value('approach_height'))
        self.lift_height = float(value('lift_height'))
        self.place_approach_height = float(value('place_approach_height'))
        self.retreat_height = float(value('retreat_height'))
        self.planning_attempts = int(value('planning_attempts'))
        self.grasp_attempts = int(value('grasp_attempts'))
        self.planning_retry_delay = float(value('planning_retry_delay'))
        self.contact_timeout = float(value('contact_timeout'))
        self.contact_settle_duration = float(value('contact_settle_duration'))
        self.contact_max_age = float(value('contact_max_age'))
        self.gripper_close_step = float(value('gripper_close_step'))
        self.gripper_close_settle_duration = float(
            value('gripper_close_settle_duration')
        )
        self.startup_delay = float(value('startup_delay'))
        self.random_seed = int(value('random_seed'))
        self.grasp_orientation = tuple(float(x) for x in value('grasp_orientation'))
        self.place_orientation = tuple(float(x) for x in value('place_orientation'))
        self.objects = self._parse_catalog(str(value('object_catalog_json')))
        self._log_workspace_diagnostics()
        self._log_gripper_orientation_diagnostics()
        if not 0.0 < self.gripper_close_step <= 0.04:
            raise ValueError('gripper_close_step must be in (0.0, 0.04].')
        if self.gripper_close_settle_duration < 0.0:
            raise ValueError('gripper_close_settle_duration must be non-negative.')
        if self.use_contacts and not self.use_sim_time:
            raise ValueError('Physical contact validation requires backend:=gazebo.')

    def _log_workspace_diagnostics(self) -> None:
        """Log pick/place reach, transfer distance, and left-to-right direction."""
        self.get_logger().info(
            'Workspace diagnostics use base_frame=%s; horizontal radii are '
            'measured from the arm base.' % self.base_frame
        )
        for task_object in self.objects:
            pick_x, pick_y, _ = task_object.pick_pose
            place_x, place_y, _ = task_object.place_pose
            pick_radius = math.hypot(pick_x, pick_y)
            place_radius = math.hypot(place_x, place_y)
            transfer = math.hypot(place_x - pick_x, place_y - pick_y)
            direction = 'left-to-right' if place_y > pick_y else 'NOT left-to-right'
            self.get_logger().info(
                'Workspace %s: pick=(%.3f, %.3f), place=(%.3f, %.3f), '
                'base radii=(%.3f, %.3f) m, transfer=%.3f m, direction=%s.'
                % (
                    task_object.object_id,
                    pick_x,
                    pick_y,
                    place_x,
                    place_y,
                    pick_radius,
                    place_radius,
                    transfer,
                    direction,
                )
            )

    def _log_gripper_orientation_diagnostics(self) -> None:
        """Log configured TCP quaternions and the fixed hand yaw compensation."""
        self.get_logger().info(
            'Gripper orientation diagnostics: grasp quaternion xyzw=%s; place '
            'quaternion xyzw=%s; panda_hand has a fixed -45 deg yaw relative '
            'to panda_link8, so TCP [1, 0, 0, 0] leaves the fingers diagonal.'
            % (self.grasp_orientation, self.place_orientation)
        )

    @staticmethod
    def _parse_catalog(raw: str) -> list[TaskObject]:
        """Parse and validate the exactly-five-object task catalog."""
        records = json.loads(raw)
        if len(records) != 5:
            raise ValueError('object_catalog_json must contain exactly five objects.')
        objects: list[TaskObject] = []
        ids: set[str] = set()
        destinations: set[tuple[float, float, float]] = set()
        for item in records:
            object_id = str(item['id'])
            shape = str(item['shape'])
            dimensions = tuple(float(x) for x in item['dimensions'])
            pick = tuple(float(x) for x in item['pick_pose'])
            place = tuple(float(x) for x in item['place_pose'])
            valid_pose = len(pick) == 3 and len(place) == 3
            if object_id in ids or shape not in ('box', 'cylinder') or not valid_pose:
                raise ValueError(f'Invalid object catalog entry: {object_id}')
            opening = float(item['gripper_opening'])
            if any(value <= 0.0 for value in dimensions) or not 0.0 <= opening <= 0.04:
                raise ValueError(f'Invalid dimensions or gripper opening: {object_id}')
            if place in destinations:
                raise ValueError(f'Duplicate placement pose: {place}')
            ids.add(object_id)
            destinations.add(place)
            objects.append(
                TaskObject(
                    object_id,
                    str(item['gazebo_model']),
                    shape,
                    dimensions,
                    opening,
                    pick,
                    place,
                    float(item.get('grasp_yaw_deg', 45.0)),
                )
            )
        return objects

    def _contact_callback(self, finger: str, message: Contacts) -> None:
        """Store collision entity names and log only meaningful contact changes."""
        models: set[str] = set()
        for contact in message.contacts:
            for entity in (contact.collision1, contact.collision2):
                if entity.name:
                    models.add(entity.name)
        with self._contact_lock:
            changed = models != self._last_contact_models[finger]
            self._finger_contacts[finger] = (models, time.monotonic())
            self._last_contact_models[finger] = models
        if changed:
            entities = ', '.join(sorted(models)) if models else '<none>'
            self.get_logger().info(
                f'Contact update ({finger}): {len(message.contacts)} pair(s); '
                f'entities=[{entities}]'
            )

    def _has_dual_contact(self, task_object: TaskObject) -> bool:
        """Return whether both recent finger streams touch the selected model."""
        if not self.use_contacts:
            return self.planning_only
        now = time.monotonic()
        expected = task_object.gazebo_model
        with self._contact_lock:
            left = self._finger_contacts['left']
            right = self._finger_contacts['right']
        both_recent = (
            now - left[1] <= self.contact_max_age
            and now - right[1] <= self.contact_max_age
        )
        return (
            both_recent
            and any(expected in name for name in left[0])
            and any(expected in name for name in right[0])
        )

    def _log_grasp_contact_snapshot(
        self, task_object: TaskObject, stage: str
    ) -> bool:
        """Log exact finger contacts immediately before and after lifting."""
        now = time.monotonic()
        with self._contact_lock:
            left = self._finger_contacts['left']
            right = self._finger_contacts['right']
        valid = self._has_dual_contact(task_object)
        self.get_logger().info(
            'Grasp contact snapshot %s/%s: dual=%s; left age=%.3fs '
            'entities=%s; right age=%.3fs entities=%s.'
            % (
                task_object.object_id,
                stage,
                valid,
                now - left[1],
                sorted(left[0]),
                now - right[1],
                sorted(right[0]),
            )
        )
        return valid

    def _wait_for_dual_contact(self, task_object: TaskObject) -> bool:
        """Wait until valid dual contact remains stable for the configured duration."""
        deadline = time.monotonic() + self.contact_timeout
        stable_from: float | None = None
        while (
            rclpy.ok()
            and not self._stop_event.is_set()
            and time.monotonic() < deadline
        ):
            if self._has_dual_contact(task_object):
                stable_from = stable_from or time.monotonic()
                if time.monotonic() - stable_from >= self.contact_settle_duration:
                    return True
            else:
                stable_from = None
            self._stop_event.wait(0.02)
        now = time.monotonic()
        expected = task_object.gazebo_model
        with self._contact_lock:
            left = self._finger_contacts['left']
            right = self._finger_contacts['right']
        left_match = any(expected in name for name in left[0])
        right_match = any(expected in name for name in right[0])
        self.get_logger().warning(
            'Dual-contact timeout for %s: expected=%s; left age=%.3fs '
            'match=%s entities=%s; right age=%.3fs match=%s entities=%s'
            % (
                task_object.object_id,
                expected,
                now - left[1],
                left_match,
                sorted(left[0]),
                now - right[1],
                right_match,
                sorted(right[0]),
            )
        )
        return False

    @staticmethod
    def _execution_succeeded(result) -> bool:
        """Return true only for MoveItPy's explicit SUCCEEDED status."""
        status = getattr(result, 'status', None)
        return status is not None and 'SUCCEEDED' in str(status).upper()

    @staticmethod
    def _execution_status_text(result) -> str:
        """Format the MoveItPy status without treating a status object as truthy."""
        status = getattr(result, 'status', None)
        return str(status) if status is not None else repr(result)

    def _plan_and_execute(self, component, controller: str, label: str) -> bool:
        """Plan a stage and require an explicit successful controller outcome."""
        for attempt in range(1, self.planning_attempts + 1):
            component.set_start_state_to_current_state()
            plan = component.plan()
            if not plan:
                self.get_logger().warning(
                    f'Planning {label} failed ({attempt}/{self.planning_attempts}).'
                )
                self._stop_event.wait(self.planning_retry_delay)
                continue
            if self.planning_only:
                self.get_logger().info(f'Planning-only success: {label}')
                return True
            try:
                result = self.moveit.execute(
                    plan.trajectory, controllers=[controller]
                )
            except Exception as error:
                self.get_logger().error(f'Execution {label} raised: {error}')
                return False
            status = self._execution_status_text(result)
            if self._execution_succeeded(result):
                self.get_logger().info(f'Completed: {label}; MoveIt status={status}')
                return True
            self.get_logger().warning(
                f'Execution {label} failed ({attempt}/{self.planning_attempts}); '
                f'MoveIt status={status}. Will re-plan.'
            )
            self._stop_event.wait(self.planning_retry_delay)
        return False

    def _move_named(self, name: str) -> bool:
        """Move the arm to a named Panda arm configuration."""
        self.arm.set_start_state_to_current_state()
        self.arm.set_goal_state(configuration_name=name)
        return self._plan_and_execute(
            self.arm, self.ARM_CONTROLLER, f'arm {name}'
        )

    def _move_pose(
        self,
        position: tuple[float, float, float],
        orientation: tuple[float, ...],
        label: str,
    ) -> bool:
        """Plan a TCP pose in the configured base frame."""
        goal = PoseStamped()
        goal.header.frame_id = self.base_frame
        goal.pose.position.x, goal.pose.position.y, goal.pose.position.z = position
        (
            goal.pose.orientation.x,
            goal.pose.orientation.y,
            goal.pose.orientation.z,
            goal.pose.orientation.w,
        ) = orientation
        self.arm.set_start_state_to_current_state()
        self.arm.set_goal_state(pose_stamped_msg=goal, pose_link=self.tool_link)
        return self._plan_and_execute(self.arm, self.ARM_CONTROLLER, label)

    def _move_vertical_steps(
        self,
        start: tuple[float, float, float],
        target: tuple[float, float, float],
        orientation: tuple[float, ...],
        label: str,
        step_size: float = 0.025,
    ) -> bool:
        """Descend vertically through short pose goals to reduce lateral sweep."""
        distance = abs(target[2] - start[2])
        steps = max(1, math.ceil(distance / step_size))
        self.get_logger().info(
            f'{label}: vertical descent {distance:.3f} m in {steps} step(s).'
        )
        for index in range(1, steps + 1):
            ratio = index / steps
            waypoint = (
                target[0],
                target[1],
                start[2] + (target[2] - start[2]) * ratio,
            )
            if not self._move_pose(
                waypoint, orientation, f'{label} step {index}/{steps}'
            ):
                return False
        return True

    def _lift_with_contact_checks(
        self,
        task_object: TaskObject,
        start: tuple[float, float, float],
        target: tuple[float, float, float],
        orientation: tuple[float, ...],
        step_size: float = 0.020,
    ) -> bool:
        """Lift in short vertical increments while requiring dual contact."""
        distance = target[2] - start[2]
        steps = max(1, math.ceil(distance / step_size))
        self.get_logger().info(
            f'lift: vertical ascent {distance:.3f} m in {steps} step(s) '
            'with contact checks.'
        )
        for index in range(1, steps + 1):
            if not self._log_grasp_contact_snapshot(
                task_object, f'lift-{index}-before'
            ):
                return False
            ratio = index / steps
            waypoint = (start[0], start[1], start[2] + distance * ratio)
            if not self._move_pose(
                waypoint, orientation, f'lift step {index}/{steps}'
            ):
                return False
            if not self._wait_for_dual_contact(task_object):
                self.get_logger().error(
                    f'{task_object.object_id}: contact lost after lift step '
                    f'{index}/{steps}.'
                )
                return False
        return True

    @staticmethod
    def _top_down_orientation(yaw_deg: float) -> tuple[float, float, float, float]:
        """Return xyzw for a downward TCP with configurable world-Z yaw."""
        half_yaw = math.radians(yaw_deg) / 2.0
        return (math.cos(half_yaw), math.sin(half_yaw), 0.0, 0.0)

    def _gripper_named(self, state: str) -> bool:
        """Plan a named gripper state, used to fully open the fingers."""
        self.gripper.set_start_state_to_current_state()
        self.gripper.set_goal_state(configuration_name=state)
        return self._plan_and_execute(
            self.gripper, self.HAND_CONTROLLER, f'gripper {state}'
        )

    def _close_gripper_for(self, task_object: TaskObject) -> bool:
        """Close in finite steps and stop immediately on verified dual contact."""
        if self.planning_only:
            return True
        opening = 0.04
        while opening > task_object.gripper_opening:
            if self._has_dual_contact(task_object):
                self.get_logger().info(
                    f'{task_object.object_id}: dual contact detected before the '
                    f'next close step.'
                )
                return True
            opening = max(
                task_object.gripper_opening,
                opening - self.gripper_close_step,
            )
            target_state = RobotState(self.moveit.get_robot_model())
            target_state.set_joint_group_positions(
                self.gripper_group, np.array([opening, opening], dtype=float)
            )
            self.gripper.set_start_state_to_current_state()
            self.gripper.set_goal_state(robot_state=target_state)
            label = (
                f'gripper close step for {task_object.object_id} '
                f'to {opening:.4f} m'
            )
            self.get_logger().info(label)
            if not self._plan_and_execute(
                self.gripper, self.HAND_CONTROLLER, label
            ):
                # A collision-limited finite step can be canceled after contact
                # has already been reported. Never accept it without the same
                # intended-object dual-contact interlock used before lifting.
                if self._wait_for_dual_contact(task_object):
                    self.get_logger().info(
                        f'{task_object.object_id}: accepting contact-limited '
                        f'close at {opening:.4f} m.'
                    )
                    return True
                return False
            if self._stop_event.wait(self.gripper_close_settle_duration):
                return False
            if self._has_dual_contact(task_object):
                self.get_logger().info(
                    f'{task_object.object_id}: dual contact accepted at '
                    f'{opening:.4f} m per finger.'
                )
                return True
        self.get_logger().warning(
            f'{task_object.object_id}: reached the configured minimum opening '
            'without verified dual contact.'
        )
        return self._wait_for_dual_contact(task_object)

    def _pick_and_place(self, task_object: TaskObject) -> bool:
        """Run a retryable physical grasp and non-teleporting placement cycle."""
        object_height = (
            task_object.dimensions[2]
            if task_object.shape == 'box'
            else task_object.dimensions[1]
        )
        fingertip_below_link8 = 0.0984
        fingertip_center_relative_to_object = (
            self.grasp_z_offset - fingertip_below_link8
        )
        self.get_logger().info(
            'Grasp geometry %s: object height=%.4f m, link8 offset=%.4f m, '
            'estimated fingertip center relative to object center=%+.4f m; '
            'desired near 0.0000 m.'
            % (
                task_object.object_id,
                object_height,
                self.grasp_z_offset,
                fingertip_center_relative_to_object,
            )
        )
        object_orientation = self._top_down_orientation(task_object.grasp_yaw_deg)
        self.get_logger().info(
            '%s: selected object yaw=%.1f deg, quaternion xyzw=%s.'
            % (
                task_object.object_id,
                task_object.grasp_yaw_deg,
                object_orientation,
            )
        )
        grasp_pose = (
            task_object.pick_pose[0],
            task_object.pick_pose[1],
            task_object.pick_pose[2] + self.grasp_z_offset,
        )
        pick_above = (
            grasp_pose[0],
            grasp_pose[1],
            grasp_pose[2] + self.approach_height,
        )
        lift = (
            grasp_pose[0],
            grasp_pose[1],
            grasp_pose[2] + self.lift_height,
        )
        place_z = task_object.place_pose[2] + self.place_z_offset
        place_above = (
            task_object.place_pose[0],
            task_object.place_pose[1],
            place_z + self.place_approach_height,
        )
        place_target = (
            task_object.place_pose[0],
            task_object.place_pose[1],
            place_z,
        )
        retreat = (
            task_object.place_pose[0],
            task_object.place_pose[1],
            place_z + self.retreat_height,
        )
        for attempt in range(1, self.grasp_attempts + 1):
            stages: list[tuple[str, Callable[[], bool]]] = [
                ('open', lambda: self._gripper_named('open')),
                (
                    'pre-grasp',
                    lambda: self._move_pose(
                        pick_above, object_orientation, 'pre-grasp'
                    ),
                ),
                (
                    'approach',
                    lambda: self._move_vertical_steps(
                        pick_above, grasp_pose, object_orientation, 'approach'
                    ),
                ),
                ('close', lambda: self._close_gripper_for(task_object)),
                ('dual-contact', lambda: self._wait_for_dual_contact(task_object)),
                (
                    'pre-lift-contact-log',
                    lambda: self._log_grasp_contact_snapshot(
                        task_object, 'pre-lift'
                    ),
                ),
                (
                    'lift',
                    lambda: self._lift_with_contact_checks(
                        task_object, grasp_pose, lift, object_orientation
                    ),
                ),
                (
                    'retain-contact',
                    lambda: (
                        self._log_grasp_contact_snapshot(task_object, 'post-lift')
                        and self._wait_for_dual_contact(task_object)
                    )
                    or self.planning_only,
                ),
                (
                    'pre-place',
                    lambda: self._move_pose(
                        place_above, self.place_orientation, 'pre-place'
                    ),
                ),
                (
                    'lower',
                    lambda: self._move_vertical_steps(
                        place_above,
                        place_target,
                        object_orientation,
                        'lower',
                    ),
                ),
                ('release', lambda: self._gripper_named('open')),
                (
                    'retreat',
                    lambda: self._move_pose(
                        retreat, self.place_orientation, 'retreat'
                    ),
                ),
            ]
            for stage, operation in stages:
                if not operation():
                    self.get_logger().error(
                        f'{task_object.object_id}: failed at {stage}, '
                        f'grasp attempt {attempt}.'
                    )
                    self._gripper_named('open')
                    self._move_pose(
                        pick_above, self.grasp_orientation, 'grasp recovery'
                    )
                    break
            else:
                self.get_logger().info(
                    f'{task_object.object_id}: placed using physical contact.'
                )
                return True
        return False

    def run(self) -> None:
        """Shuffle and process exactly one complete five-object task cycle."""
        if self._stop_event.wait(self.startup_delay):
            return
        order = list(self.objects)
        seed = None if self.random_seed < 0 else self.random_seed
        random.Random(seed).shuffle(order)
        self.get_logger().info(
            'Pick order: ' + ', '.join(task.object_id for task in order)
        )
        if not self._move_named('ready'):
            return
        for task_object in order:
            if not self._pick_and_place(task_object):
                self.get_logger().error(
                    f'Task stopped at object {task_object.object_id}.'
                )
                return
        if self.run_forever:
            self.get_logger().warning(
                'run_forever is disabled for physical-contact tasks: resetting '
                'object poses would violate the no-teleport safety policy.'
            )

    def destroy_node(self) -> bool:
        """Stop the worker thread before destroying the ROS node."""
        self._stop_event.set()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=2.0)
        return super().destroy_node()


def main(args=None) -> None:
    """Initialize and spin the physical-contact pick-and-place node."""
    rclpy.init(args=args)
    node = PickPlaceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
