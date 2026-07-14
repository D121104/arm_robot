import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
    TimerAction,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            'world',
            default_value=PathJoinSubstitution(
                [
                    FindPackageShare('my_robot_arm_gazebo'),
                    'worlds',
                    'pick_place_world.sdf',
                ]
            ),
            description='Path to Gazebo world SDF file',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'headless',
            default_value='false',
            description='Run Gazebo in headless mode (server only, no GUI) to save CPU/GPU resources',
        )
    )

    # Controllers config — defined BEFORE robot_description so it can be referenced
    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare('my_robot_arm_control'),
            'config',
            'ros2_controllers.yaml',
        ]
    )

    # Get robot description via xacro (using gz_ros2_control hardware)
    # Pass parameters_file so gz_ros2_control plugin knows which controllers to load
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
            ' parameters_file:=',
            robot_controllers,
        ]
    )
    robot_description = {'robot_description': robot_description_content}

    # Launch Gazebo
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare('ros_gz_sim'),
                    'launch',
                    'gz_sim.launch.py',
                ]
            )
        ),
        launch_arguments={
            'gz_args': PythonExpression(
                [
                    "'-s -r ' + '",
                    LaunchConfiguration('world'),
                    "' if '",
                    LaunchConfiguration('headless'),
                    "' == 'true' else '-r ' + '",
                    LaunchConfiguration('world'),
                    "'",
                ]
            )
        }.items(),
    )

    # Bridge to forward clock from Gazebo to ROS
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen',
    )

    # robot_state_publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description, {'use_sim_time': True}],
    )

    # Spawn robot into Gazebo
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'panda',
            '-topic', 'robot_description',
            '-z', '0.0',
        ],
        output='screen',
    )

    # NOTE: When using gz_ros2_control, the controller_manager is created
    # automatically by the GazeboSimSystem plugin inside Gazebo.
    # Do NOT launch a separate ros2_control_node — it will conflict.
    # The robot_controllers yaml is loaded via the plugin param in the URDF.

    # Spawners — use long timeout so they wait for Gazebo plugin to init
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '60',
        ],
        output='screen',
    )

    panda_arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'panda_arm_controller',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '60',
        ],
        output='screen',
    )

    panda_hand_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'panda_hand_controller',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '60',
        ],
        output='screen',
    )

    # Delay spawners by 5s to give Gazebo time to load the gz_ros2_control plugin
    # and create the /controller_manager service
    delayed_joint_state_broadcaster = TimerAction(
        period=5.0,
        actions=[joint_state_broadcaster_spawner],
    )

    delay_arm_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[panda_arm_controller_spawner],
        )
    )

    delay_hand_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=panda_arm_controller_spawner,
            on_exit=[panda_hand_controller_spawner],
        )
    )

    return LaunchDescription(
        declared_arguments
        + [
            gz_sim,
            clock_bridge,
            robot_state_publisher_node,
            spawn_robot,
            delayed_joint_state_broadcaster,
            delay_arm_controller,
            delay_hand_controller,
        ]
    )
