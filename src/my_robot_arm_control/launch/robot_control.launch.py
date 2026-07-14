import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            'ros2_control_hardware_type',
            default_value='mock_components',
            description='Type of ros2_control hardware interface (mock_components or gz_ros2_control)',
        )
    )

    ros2_control_hardware_type = LaunchConfiguration('ros2_control_hardware_type')

    # Get robot description via xacro
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

    # Controllers config path
    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare('my_robot_arm_control'),
            'config',
            'ros2_controllers.yaml',
        ]
    )

    # robot_state_publisher node
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description],
    )

    # controller_manager node
    controller_manager_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[robot_controllers],
        output='screen',
        remappings=[
            ('~/robot_description', '/robot_description'),
        ],
    )

    # Spawn joint_state_broadcaster
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
    )

    # Spawn arm controller (after joint_state_broadcaster is active)
    panda_arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['panda_arm_controller', '--controller-manager', '/controller_manager'],
    )

    # Spawn hand controller (after arm controller is active)
    panda_hand_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['panda_hand_controller', '--controller-manager', '/controller_manager'],
    )

    # Delay arm controller start until joint_state_broadcaster is active
    delay_arm_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[panda_arm_controller_spawner],
        )
    )

    # Delay hand controller start until arm controller is active
    delay_hand_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=panda_arm_controller_spawner,
            on_exit=[panda_hand_controller_spawner],
        )
    )

    return LaunchDescription(
        declared_arguments
        + [
            robot_state_publisher_node,
            controller_manager_node,
            joint_state_broadcaster_spawner,
            delay_arm_controller,
            delay_hand_controller,
        ]
    )
