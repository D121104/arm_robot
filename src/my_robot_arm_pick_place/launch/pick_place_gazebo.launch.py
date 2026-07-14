import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction
from launch.substitutions import (
    Command,
    FindExecutable,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import yaml


def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)
    with open(absolute_file_path) as f:
        return yaml.safe_load(f)


def generate_launch_description():

    # ----------------------------------------------------------------
    # 1. robot_description (xacro) — needed by move_group and rviz2
    #    Gazebo launch already runs robot_state_publisher, but
    #    move_group and rviz2 also need it as a node *parameter*.
    # ----------------------------------------------------------------
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name='xacro')]),
            ' ',
            PathJoinSubstitution(
                [
                    FindPackageShare('my_robot_arm_description'),
                    'urdf',
                    'my_robot_arm.urdf.xacro',
                ]
            ),
            ' ros2_control_hardware_type:=gz_ros2_control',
        ]
    )
    robot_description = {'robot_description': robot_description_content}

    # ----------------------------------------------------------------
    # 2. Semantic description (SRDF)
    # ----------------------------------------------------------------
    robot_description_semantic_content = open(
        os.path.join(
            get_package_share_directory('my_robot_arm_moveit_config'),
            'config',
            'panda.srdf',
        )
    ).read()
    robot_description_semantic = {
        'robot_description_semantic': robot_description_semantic_content
    }

    # ----------------------------------------------------------------
    # 3. Kinematics (KDL IK solver)
    # ----------------------------------------------------------------
    kinematics_yaml = load_yaml(
        'my_robot_arm_moveit_config', 'config/kinematics.yaml'
    )
    robot_description_kinematics = {'robot_description_kinematics': kinematics_yaml}

    # ----------------------------------------------------------------
    # 4. MoveIt controller manager config
    # ----------------------------------------------------------------
    moveit_controllers = load_yaml(
        'my_robot_arm_moveit_config', 'config/moveit_controllers.yaml'
    )

    # Planning Pipeline configuration (OMPL)
    ompl_planning_yaml = load_yaml(
        'my_robot_arm_moveit_config', 'config/ompl_planning.yaml'
    )
    planning_pipelines = {
        'default_planning_pipeline': 'ompl',
        'planning_pipelines': ['ompl'],
        'ompl': ompl_planning_yaml,
    }

    # ----------------------------------------------------------------
    # 5. Pick & place positions / gripper params
    # ----------------------------------------------------------------
    pick_place_params = load_yaml(
        'my_robot_arm_pick_place', 'config/pick_place_params.yaml'
    )

    global_params = os.path.join(
        get_package_share_directory('my_robot_arm_pick_place'),
        'config',
        'global_params.yaml'
    )

    # ----------------------------------------------------------------
    # 6. move_group node
    # ----------------------------------------------------------------
    move_group_node = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        output='screen',
        parameters=[
            robot_description,
            robot_description_semantic,
            robot_description_kinematics,
            planning_pipelines,
            moveit_controllers,
            global_params,
        ],
    )

    # ----------------------------------------------------------------
    # 7. pick_place_node — delayed 8s so Gazebo + move_group are ready
    # ----------------------------------------------------------------
    pick_place_node = TimerAction(
        period=8.0,
        actions=[
            Node(
                package='my_robot_arm_pick_place',
                executable='pick_place_node',
                name='pick_place_python_node',
                output='screen',
                parameters=[
                    robot_description,
                    robot_description_semantic,
                    robot_description_kinematics,
                    planning_pipelines,
                    moveit_controllers,
                    pick_place_params['pick_place_node']['ros__parameters'],
                    global_params,
                ],
            )
        ],
    )

    # ----------------------------------------------------------------
    # 8. RViz2 — use the system-verified moveit.rviz config
    # ----------------------------------------------------------------
    rviz_config = os.path.join(
        get_package_share_directory('my_robot_arm_moveit_config'),
        'rviz',
        'moveit.rviz',
    )
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[
            robot_description,
            robot_description_semantic,
            robot_description_kinematics,
            {'use_sim_time': True},
        ],
    )

    return LaunchDescription(
        [
            move_group_node,
            rviz_node,
            pick_place_node,
        ]
    )
