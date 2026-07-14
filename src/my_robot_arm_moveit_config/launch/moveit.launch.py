import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
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

    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            'ros2_control_hardware_type',
            default_value='mock_components',
            description='ros2_control hardware type',
        )
    )

    ros2_control_hardware_type = LaunchConfiguration('ros2_control_hardware_type')

    # Robot description via xacro
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
            ' ros2_control_hardware_type:=',
            ros2_control_hardware_type,
        ]
    )
    robot_description = {'robot_description': robot_description_content}

    # Semantic robot description (SRDF)
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

    # Kinematics
    kinematics_yaml = load_yaml(
        'my_robot_arm_moveit_config', 'config/kinematics.yaml'
    )
    robot_description_kinematics = {'robot_description_kinematics': kinematics_yaml}

    # Planning Pipeline configuration (OMPL)
    ompl_planning_yaml = load_yaml(
        'my_robot_arm_moveit_config', 'config/ompl_planning.yaml'
    )
    planning_pipelines = {
        'default_planning_pipeline': 'ompl',
        'planning_pipelines': ['ompl'],
        'ompl': ompl_planning_yaml,
    }

    # MoveIt controllers
    moveit_controllers = load_yaml(
        'my_robot_arm_moveit_config', 'config/moveit_controllers.yaml'
    )

    # Controllers config (ros2_control)
    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare('my_robot_arm_control'),
            'config',
            'ros2_controllers.yaml',
        ]
    )

    # Nodes
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description],
    )

    controller_manager_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[robot_controllers],
        output='screen',
        remappings=[('~/robot_description', '/robot_description')],
    )

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
            {'use_sim_time': False},
        ],
    )

    # RViz with MoveIt plugin
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
        ],
    )

    # joint_state_broadcaster spawner
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
    )

    panda_arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['panda_arm_controller', '--controller-manager', '/controller_manager'],
    )

    panda_hand_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['panda_hand_controller', '--controller-manager', '/controller_manager'],
    )

    return LaunchDescription(
        declared_arguments
        + [
            robot_state_publisher_node,
            controller_manager_node,
            move_group_node,
            rviz_node,
            joint_state_broadcaster_spawner,
            panda_arm_controller_spawner,
            panda_hand_controller_spawner,
        ]
    )
