#!/usr/bin/env python3
"""
Pick and Place Node for Panda Arm.

This node uses MoveIt 2 Python API (moveit_commander) to:
1. Move arm to home position
2. Open gripper
3. Move above pick object (pre-grasp)
4. Move down to grasp position
5. Close gripper (grasp object)
6. Retreat upward
7. Move above place position (pre-place)
8. Move down to place position
9. Open gripper (release object)
10. Retreat upward
11. Return home
"""

import time

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from geometry_msgs.msg import Pose, PoseStamped
from moveit.core.robot_state import RobotState
from moveit.planning import MoveItPy, PlanningComponent
import numpy as np


class PickPlaceNode(Node):
    """Node that performs autonomous pick and place using MoveIt 2."""

    def __init__(self):
        super().__init__('pick_place_node')

        # Declare parameters with defaults
        self.declare_parameter('approach_height', 0.12)
        self.declare_parameter('retreat_height', 0.20)
        self.declare_parameter('place_approach_height', 0.15)
        self.declare_parameter('gripper_open', 0.035)
        self.declare_parameter('gripper_close', 0.018)
        self.declare_parameter('gripper_effort', 10.0)
        self.declare_parameter('pick_position.x', 0.5)
        self.declare_parameter('pick_position.y', 0.0)
        self.declare_parameter('pick_position.z', 0.455)
        self.declare_parameter('place_position.x', 0.5)
        self.declare_parameter('place_position.y', 0.3)
        self.declare_parameter('place_position.z', 0.455)
        self.declare_parameter('pick_orientation.x', 1.0)
        self.declare_parameter('pick_orientation.y', 0.0)
        self.declare_parameter('pick_orientation.z', 0.0)
        self.declare_parameter('pick_orientation.w', 0.0)
        self.declare_parameter('place_orientation.x', 1.0)
        self.declare_parameter('place_orientation.y', 0.0)
        self.declare_parameter('place_orientation.z', 0.0)
        self.declare_parameter('place_orientation.w', 0.0)
        self.declare_parameter('arm_group_name', 'panda_arm')
        self.declare_parameter('gripper_group_name', 'hand')
        self.declare_parameter('planning_time', 10.0)
        self.declare_parameter('num_planning_attempts', 5)
        self.declare_parameter('max_velocity_scaling_factor', 0.3)
        self.declare_parameter('max_acceleration_scaling_factor', 0.2)

        # Read parameters
        self.approach_h = self.get_parameter('approach_height').value
        self.retreat_h = self.get_parameter('retreat_height').value
        self.place_approach_h = self.get_parameter('place_approach_height').value
        self.gripper_open = self.get_parameter('gripper_open').value
        self.gripper_close = self.get_parameter('gripper_close').value

        self.pick_x = self.get_parameter('pick_position.x').value
        self.pick_y = self.get_parameter('pick_position.y').value
        self.pick_z = self.get_parameter('pick_position.z').value

        self.place_x = self.get_parameter('place_position.x').value
        self.place_y = self.get_parameter('place_position.y').value
        self.place_z = self.get_parameter('place_position.z').value

        self.pick_ox = self.get_parameter('pick_orientation.x').value
        self.pick_oy = self.get_parameter('pick_orientation.y').value
        self.pick_oz = self.get_parameter('pick_orientation.z').value
        self.pick_ow = self.get_parameter('pick_orientation.w').value

        self.arm_group = self.get_parameter('arm_group_name').value
        self.gripper_group = self.get_parameter('gripper_group_name').value
        self.planning_time = self.get_parameter('planning_time').value
        self.num_attempts = self.get_parameter('num_planning_attempts').value
        self.vel_scale = self.get_parameter('max_velocity_scaling_factor').value
        self.acc_scale = self.get_parameter('max_acceleration_scaling_factor').value

        # Initialize MoveItPy using MoveItConfigsBuilder
        self.get_logger().info('Initializing MoveItPy using MoveItConfigsBuilder...')
        
        import os
        from ament_index_python.packages import get_package_share_directory
        from moveit_configs_utils import MoveItConfigsBuilder
        
        # Determine hardware type based on simulation configuration
        use_sim_time = self.get_parameter('use_sim_time').value
        hardware_type = 'gz_ros2_control' if use_sim_time else 'mock_components'
        
        # Find absolute path of URDF xacro
        urdf_path = os.path.join(
            get_package_share_directory('my_robot_arm_description'),
            'urdf',
            'my_robot_arm.urdf.xacro'
        )
        
        # Build MoveIt parameters dictionary (using only OMPL pipeline)
        moveit_config = (
            MoveItConfigsBuilder("panda", package_name="my_robot_arm_moveit_config")
            .robot_description(file_path=urdf_path, mappings={"ros2_control_hardware_type": hardware_type})
            .moveit_cpp(file_path="config/moveit_cpp.yaml")
            .planning_pipelines(pipelines=["ompl"])
            .to_moveit_configs()
        )
        
        # Add use_sim_time and qos_overrides to MoveItPy C++ config if simulation is enabled
        config_dict = moveit_config.to_dict()
        if use_sim_time:
            config_dict['use_sim_time'] = True
            config_dict['qos_overrides./clock.subscription.durability'] = 'volatile'
            config_dict['qos_overrides./clock.subscription.reliability'] = 'best_effort'
            config_dict['qos_overrides./clock.subscription.depth'] = 1
            config_dict['qos_overrides./clock.subscription.history'] = 'keep_last'

        # Instantiate MoveItPy with built config
        self.moveit = MoveItPy(
            node_name='pick_place_moveit_py',
            config_dict=config_dict
        )
        self.arm = self.moveit.get_planning_component(self.arm_group)
        self.gripper = self.moveit.get_planning_component(self.gripper_group)
        self.robot_model = self.moveit.get_robot_model()

        self.get_logger().info('MoveItPy initialized. Ready for pick and place.')

        # Give time for everything to come up
        time.sleep(2.0)

        # Start pick and place sequence in a separate thread to allow the ROS 2 executor to spin in the main thread
        import threading
        self.thread = threading.Thread(target=self.run_pick_and_place, daemon=True)
        self.thread.start()

    # ------------------------------------------------------------------
    # Helper: move arm to named state (e.g. 'ready', 'home')
    # ------------------------------------------------------------------
    def move_arm_to_named_state(self, state_name: str) -> bool:
        self.get_logger().info(f'Moving arm to named state: {state_name}')
        self.arm.set_start_state_to_current_state()
        self.arm.set_goal_state(configuration_name=state_name)
        plan_result = self.arm.plan()
        if plan_result:
            robot_trajectory = plan_result.trajectory
            self.moveit.execute(robot_trajectory, controllers=[])
            return True
        self.get_logger().error(f'Failed to plan to named state: {state_name}')
        return False

    # ------------------------------------------------------------------
    # Helper: move arm to a Cartesian pose
    # ------------------------------------------------------------------
    def move_arm_to_pose(self, x: float, y: float, z: float,
                         ox: float, oy: float, oz: float, ow: float,
                         label: str = 'target') -> bool:
        self.get_logger().info(f'Moving arm to {label}: ({x:.3f}, {y:.3f}, {z:.3f})')

        pose_goal = PoseStamped()
        pose_goal.header.frame_id = 'panda_link0'
        pose_goal.pose.position.x = x
        pose_goal.pose.position.y = y
        pose_goal.pose.position.z = z
        pose_goal.pose.orientation.x = ox
        pose_goal.pose.orientation.y = oy
        pose_goal.pose.orientation.z = oz
        pose_goal.pose.orientation.w = ow

        self.arm.set_start_state_to_current_state()
        self.arm.set_goal_state(pose_stamped_msg=pose_goal, pose_link='panda_hand')

        plan_result = self.arm.plan()
        if plan_result:
            self.moveit.execute(plan_result.trajectory, controllers=[])
            time.sleep(0.5)
            return True

        self.get_logger().error(f'Planning failed for {label}')
        return False

    # ------------------------------------------------------------------
    # Helper: move gripper to named state ('open' or 'close')
    # ------------------------------------------------------------------
    def set_gripper(self, state_name: str) -> bool:
        self.get_logger().info(f'Setting gripper to: {state_name}')
        self.gripper.set_start_state_to_current_state()
        self.gripper.set_goal_state(configuration_name=state_name)
        plan_result = self.gripper.plan()
        if plan_result:
            self.moveit.execute(plan_result.trajectory, controllers=[])
            time.sleep(0.5)
            return True
        self.get_logger().error(f'Gripper planning failed for state: {state_name}')
        return False

    # ------------------------------------------------------------------
    # Reset Gazebo World
    # ------------------------------------------------------------------
    def reset_world(self):
        self.get_logger().info('Calling Gazebo Reset World (model_only)...')
        import subprocess
        try:
            # We call the gz service command to reset only model poses (retaining simulation time)
            cmd = [
                "gz", "service", "-s", "/world/pick_place_world/control",
                "--reqtype", "gz.msgs.WorldControl",
                "--reptype", "gz.msgs.Boolean",
                "--timeout", "3000",
                "--req", "reset: {model_only: true}"
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.get_logger().info('Gazebo Reset World service called successfully.')
        except Exception as e:
            self.get_logger().error(f'Failed to call Reset World: {e}')

        self.get_logger().info('Resetting pick_object pose to initial position...')
        try:
            cmd = [
                "gz", "service", "-s", "/world/pick_place_world/set_pose",
                "--reqtype", "gz.msgs.Pose",
                "--reptype", "gz.msgs.Boolean",
                "--timeout", "3000",
                "--req", f'name: "pick_object", position: {{x: {self.pick_x}, y: {self.pick_y}, z: {self.pick_z}}}, orientation: {{x: 0.0, y: 0.0, z: 0.0, w: 1.0}}'
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.get_logger().info('pick_object pose reset successfully.')
        except Exception as e:
            self.get_logger().error(f'Failed to reset pick_object pose: {e}')

    # ------------------------------------------------------------------
    # Reactivate ROS 2 Controllers
    # ------------------------------------------------------------------
    def reactivate_controllers(self):
        self.get_logger().info('Reactivating controllers...')
        from controller_manager_msgs.srv import SwitchController
        
        client = self.create_client(SwitchController, '/controller_manager/switch_controller')
        while not client.wait_for_service(timeout_sec=1.0):
            if not rclpy.ok():
                return
            self.get_logger().info('Waiting for /controller_manager/switch_controller service...')
            
        req = SwitchController.Request()
        req.activate_controllers = ['joint_state_broadcaster', 'panda_arm_controller', 'panda_hand_controller']
        req.strictness = SwitchController.Request.BEST_EFFORT
        req.activate_asap = True
        
        future = client.call_async(req)
        
        import time
        start_time = time.time()
        while not future.done():
            time.sleep(0.1)
            if time.time() - start_time > 5.0:
                self.get_logger().error('Timeout waiting for switch_controller service response')
                return
        
        res = future.result()
        if res and res.ok:
            self.get_logger().info('Controllers reactivated successfully.')
        else:
            self.get_logger().error(f'Failed to reactivate controllers: {res.message if res else "No response"}')

    # ------------------------------------------------------------------
    # Main pick and place sequence loop
    # ------------------------------------------------------------------
    def run_pick_and_place(self):
        # Give the main thread a moment to start spinning rclpy.spin
        time.sleep(1.0)
        while rclpy.ok():
            success = self.execute_sequence()
            if not success:
                self.get_logger().error('Pick and place sequence failed.')
            
            # Call reset world service if simulation is enabled
            if self.get_parameter('use_sim_time').value:
                self.reset_world()
                # Give a brief delay for Gazebo to complete resetting poses
                time.sleep(1.0)
                # Reactivate controllers since reset transitions them to inactive
                self.reactivate_controllers()
                # Give time for joint states to publish and propagate to MoveIt
                time.sleep(1.0)
            
            self.get_logger().info('Waiting 2 seconds before starting next cycle...')
            time.sleep(2.0)

    def execute_sequence(self) -> bool:
        self.get_logger().info('=' * 60)
        self.get_logger().info('Starting Pick and Place Sequence')
        self.get_logger().info(f'  Pick  position: ({self.pick_x}, {self.pick_y}, {self.pick_z})')
        self.get_logger().info(f'  Place position: ({self.place_x}, {self.place_y}, {self.place_z})')
        self.get_logger().info('=' * 60)

        # --- Step 1: Go to home/ready position ---
        self.get_logger().info('[1/11] Moving to home position...')
        if not self.move_arm_to_named_state('ready'):
            self.get_logger().error('FAILED at step 1. Aborting.')
            return False

        # --- Step 2: Open gripper ---
        self.get_logger().info('[2/11] Opening gripper...')
        self.set_gripper('open')

        # --- Step 3: Move above pick object (pre-grasp) ---
        pre_pick_z = self.pick_z + self.approach_h
        self.get_logger().info('[3/11] Moving to pre-grasp position above pick object...')
        if not self.move_arm_to_pose(
            self.pick_x, self.pick_y, pre_pick_z,
            self.pick_ox, self.pick_oy, self.pick_oz, self.pick_ow,
            label='pre-grasp'
        ):
            self.get_logger().error('FAILED at step 3. Aborting.')
            return False

        # --- Step 4: Move down to grasp position ---
        self.get_logger().info('[4/11] Moving down to grasp position...')
        if not self.move_arm_to_pose(
            self.pick_x, self.pick_y, self.pick_z,
            self.pick_ox, self.pick_oy, self.pick_oz, self.pick_ow,
            label='grasp'
        ):
            self.get_logger().error('FAILED at step 4. Aborting.')
            return False

        # --- Step 5: Close gripper (grasp) ---
        self.get_logger().info('[5/11] Closing gripper to grasp object...')
        self.set_gripper('close')
        time.sleep(0.5)

        # --- Step 6: Retreat upward (post-grasp) ---
        post_pick_z = self.pick_z + self.retreat_h
        self.get_logger().info('[6/11] Retreating upward with object...')
        if not self.move_arm_to_pose(
            self.pick_x, self.pick_y, post_pick_z,
            self.pick_ox, self.pick_oy, self.pick_oz, self.pick_ow,
            label='post-grasp retreat'
        ):
            self.get_logger().error('FAILED at step 6. Aborting.')
            return False

        # --- Step 7: Move above place position (pre-place) ---
        pre_place_z = self.place_z + self.place_approach_h
        self.get_logger().info('[7/11] Moving above place position...')
        if not self.move_arm_to_pose(
            self.place_x, self.place_y, pre_place_z,
            self.pick_ox, self.pick_oy, self.pick_oz, self.pick_ow,
            label='pre-place'
        ):
            self.get_logger().error('FAILED at step 7. Aborting.')
            return False

        # --- Step 8: Move down to place position ---
        self.get_logger().info('[8/11] Moving down to place position...')
        if not self.move_arm_to_pose(
            self.place_x, self.place_y, self.place_z,
            self.pick_ox, self.pick_oy, self.pick_oz, self.pick_ow,
            label='place'
        ):
            self.get_logger().error('FAILED at step 8. Aborting.')
            return False

        # --- Step 9: Open gripper (release) ---
        self.get_logger().info('[9/11] Opening gripper to release object...')
        self.set_gripper('open')
        time.sleep(0.5)

        # --- Step 10: Retreat upward ---
        post_place_z = self.place_z + self.retreat_h
        self.get_logger().info('[10/11] Retreating upward from place position...')
        self.move_arm_to_pose(
            self.place_x, self.place_y, post_place_z,
            self.pick_ox, self.pick_oy, self.pick_oz, self.pick_ow,
            label='post-place retreat'
        )

        # --- Step 11: Return to home ---
        self.get_logger().info('[11/11] Returning to home position...')
        self.move_arm_to_named_state('ready')

        self.get_logger().info('=' * 60)
        self.get_logger().info('Pick and Place Sequence COMPLETED SUCCESSFULLY!')
        self.get_logger().info('=' * 60)
        return True


def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
            self.place_x, self.place_y, self.place_z,
            self.pick_ox, self.pick_oy, self.pick_oz, self.pick_ow,
            label='place'
        ):
            self.get_logger().error('FAILED at step 8. Aborting.')
            return False

        # --- Step 9: Open gripper (release) ---
        self.get_logger().info('[9/11] Opening gripper to release object...')
        self.set_gripper('open')
        time.sleep(0.5)

        # --- Step 10: Retreat upward ---
        post_place_z = self.place_z + self.retreat_h
        self.get_logger().info('[10/11] Retreating upward from place position...')
        self.move_arm_to_pose(
            self.place_x, self.place_y, post_place_z,
            self.pick_ox, self.pick_oy, self.pick_oz, self.pick_ow,
            label='post-place retreat'
        )

        # --- Step 11: Return to home ---
        self.get_logger().info('[11/11] Returning to home position...')
        self.move_arm_to_named_state('ready')

        self.get_logger().info('=' * 60)
        self.get_logger().info('Pick and Place Sequence COMPLETED SUCCESSFULLY!')
        self.get_logger().info('=' * 60)
        return True


def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
