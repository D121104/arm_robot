import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    package_path = get_package_share_directory(
        'my_robot_description'
    )

    urdf_path = os.path.join(
        package_path,
        'urdf',
        'my_robot.urdf'
    )

    rviz_config_path = os.path.join(
        package_path,
        'rviz',
        'display.rviz'
    )

    return LaunchDescription([

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[
                {
                    'robot_description': open(urdf_path).read()
                }
            ]
        ),

        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui'
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_path]
        )

    ])
