"""Launch Panda pick-and-place with either mock or Gazebo backend."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition, UnlessCondition
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
import yaml


def load_yaml(package_name: str, file_path: str) -> dict:
    """Load a packaged YAML file into a launch parameter dictionary."""
    absolute_path = os.path.join(
        get_package_share_directory(package_name), file_path
    )
    with open(absolute_path, encoding='utf-8') as file:
        return yaml.safe_load(file)


def generate_launch_description() -> LaunchDescription:
    backend = LaunchConfiguration('backend')
    headless = LaunchConfiguration('headless')
    start_rviz = LaunchConfiguration('start_rviz')
    autorun = LaunchConfiguration('autorun')
    run_forever = LaunchConfiguration('run_forever')
    planning_only = LaunchConfiguration('planning_only')
    hardware_type = PythonExpression([
        "'gz_ros2_control' if '", backend,
        "' == 'gazebo' else 'mock_components'",
    ])
    use_sim_time = PythonExpression(["'", backend, "' == 'gazebo'"])

    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]), ' ',
        PathJoinSubstitution([
            FindPackageShare('my_robot_arm_description'), 'urdf',
            'my_robot_arm.urdf.xacro',
        ]),
        ' ros2_control_hardware_type:=', hardware_type,
    ])
    robot_description = {'robot_description': robot_description_content}
    semantic_path = os.path.join(
        get_package_share_directory('my_robot_arm_moveit_config'),
        'config', 'panda.srdf',
    )
    with open(semantic_path, encoding='utf-8') as file:
        robot_description_semantic = {
            'robot_description_semantic': file.read(),
        }
    robot_description_kinematics = {'robot_description_kinematics': load_yaml(
        'my_robot_arm_moveit_config', 'config/kinematics.yaml'
    )}
    planning_pipelines = {
        'default_planning_pipeline': 'ompl',
        'planning_pipelines': ['ompl'],
        'ompl': load_yaml('my_robot_arm_moveit_config', 'config/ompl_planning.yaml'),
    }
    moveit_controllers = load_yaml(
        'my_robot_arm_moveit_config', 'config/moveit_controllers.yaml'
    )
    robot_controllers = PathJoinSubstitution([
        FindPackageShare('my_robot_arm_control'), 'config',
        'ros2_controllers.yaml',
    ])
    common_moveit_parameters = [
        robot_description,
        robot_description_semantic,
        robot_description_kinematics,
        planning_pipelines,
        moveit_controllers,
        {'use_sim_time': use_sim_time},
    ]

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare('my_robot_arm_gazebo'), 'launch', 'gazebo.launch.py',
        ])),
        condition=IfCondition(PythonExpression(["'", backend, "' == 'gazebo'"])),
        launch_arguments={'headless': headless}.items(),
    )
    mock_robot_state_publisher = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        output='screen', parameters=[robot_description],
        condition=UnlessCondition(PythonExpression(["'", backend, "' == 'gazebo'"])),
    )
    mock_controller_manager = Node(
        package='controller_manager', executable='ros2_control_node',
        output='screen', parameters=[robot_controllers],
        remappings=[('~/robot_description', '/robot_description')],
        condition=UnlessCondition(PythonExpression(["'", backend, "' == 'gazebo'"])),
    )
    mock_joint_state_broadcaster = Node(
        package='controller_manager', executable='spawner', output='screen',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        condition=UnlessCondition(PythonExpression(["'", backend, "' == 'gazebo'"])),
    )
    mock_arm_controller = Node(
        package='controller_manager', executable='spawner', output='screen',
        arguments=['panda_arm_controller', '--controller-manager', '/controller_manager'],
        condition=UnlessCondition(PythonExpression(["'", backend, "' == 'gazebo'"])),
    )
    mock_hand_controller = Node(
        package='controller_manager', executable='spawner', output='screen',
        arguments=['panda_hand_controller', '--controller-manager', '/controller_manager'],
        condition=UnlessCondition(PythonExpression(["'", backend, "' == 'gazebo'"])),
    )
    move_group = Node(
        package='moveit_ros_move_group', executable='move_group', output='screen',
        parameters=common_moveit_parameters,
    )
    rviz = Node(
        package='rviz2', executable='rviz2', name='rviz2', output='screen',
        arguments=['-d', os.path.join(
            get_package_share_directory('my_robot_arm_moveit_config'),
            'rviz', 'moveit.rviz',
        )],
        parameters=[
            robot_description, robot_description_semantic,
            robot_description_kinematics, {'use_sim_time': use_sim_time},
        ],
        condition=IfCondition(start_rviz),
    )
    # Gazebo starts controller spawners after the robot is inserted.  Defer the
    # MoveItPy task until their activation and /joint_states publication settle.
    pick_place = TimerAction(
        period=15.0,
        actions=[Node(
            package='my_robot_arm_pick_place', executable='pick_place_node',
            name='pick_place_node', output='screen',
            # MoveItPy builds its own private MoveIt configuration inside the
            # task process. Do not pass move_group's robot and planning
            # parameters through ROS global arguments into that C++ executor.
            parameters=[
                load_yaml(
                    'my_robot_arm_pick_place',
                    'config/pick_place_params.yaml',
                )['pick_place_node']['ros__parameters'],
                {
                    'autorun': autorun,
                    'run_forever': run_forever,
                    'planning_only': planning_only,
                    'use_physical_contacts': use_sim_time,
                    'use_sim_time': use_sim_time,
                },
            ],
        )],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'backend', default_value='mock',
            choices=['mock', 'gazebo'],
            description='Execution backend: mock hardware or Gazebo Sim.',
        ),
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='Run Gazebo server without its GUI.',
        ),
        DeclareLaunchArgument(
            'start_rviz', default_value='true',
            description='Start RViz with the MoveIt configuration.',
        ),
        DeclareLaunchArgument(
            'autorun', default_value='true',
            description='Start one pick-and-place sequence automatically.',
        ),
        DeclareLaunchArgument(
            'run_forever', default_value='false',
            description='Repeat successful sequences; only resets world on Gazebo.',
        ),
        DeclareLaunchArgument(
            'planning_only', default_value='false',
            description='Plan stages without controller execution; contact checks are bypassed.',
        ),
        gazebo,
        mock_robot_state_publisher,
        mock_controller_manager,
        mock_joint_state_broadcaster,
        mock_arm_controller,
        mock_hand_controller,
        move_group,
        rviz,
        pick_place,
    ])
