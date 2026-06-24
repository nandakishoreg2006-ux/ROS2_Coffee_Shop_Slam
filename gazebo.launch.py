import os

from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_path = get_package_share_directory('mypkg')

    urdf_path = os.path.join(pkg_path, 'urdf', 'urdfbot_simple.urdf')
    world_path = os.path.join(pkg_path, 'worlds', 'coffee_shop.world')

    with open(urdf_path, 'r') as infp:
        robot_desc = infp.read()

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_desc}]
    )

    # Gazebo loads the coffee shop world
    gazebo = ExecuteProcess(
        cmd=[
            'gazebo', '--verbose',
            '-s', 'libgazebo_ros_factory.so',
            world_path
        ],
        output='screen'
    )

    # Spawn at entrance (west door gap, facing east into the shop)
    spawn_robot = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='gazebo_ros',
                executable='spawn_entity.py',
                arguments=[
                    '-entity', 'urdfbot_simple',
                    '-topic', 'robot_description',
                    '-x', '-4.5',
                    '-y', '0.0',
                    '-z', '0.15',
                    '-Y', '0.0'
                ],
                output='screen'
            )
        ]
    )

    return LaunchDescription([
        robot_state_publisher,
        gazebo,
        spawn_robot
    ])

