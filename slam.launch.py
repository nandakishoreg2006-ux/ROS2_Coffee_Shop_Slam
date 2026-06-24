"""
slam.launch.py
==============
Launches:
  1. Gazebo with the coffee_shop world
  2. Robot State Publisher (URDF)
  3. Spawns the robot at the entrance (x=-5, y=0)
  4. SLAM Toolbox (online_async) — builds the map live
  5. RViz2 pre-configured to show LaserScan + Map + Robot

Drive the robot around with teleop to build the map, then save it:
  ros2 run nav2_map_server map_saver_cli -f ~/ros_ws4/src/mypkg/map/coffee_shop_map

"""

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_path = get_package_share_directory('mypkg')

    urdf_path = os.path.join(pkg_path, 'urdf', 'urdfbot_simple.urdf')
    world_path = os.path.join(pkg_path, 'worlds', 'coffee_shop.world')
    slam_params = os.path.join(pkg_path, 'config', 'slam_params.yaml')

    with open(urdf_path, 'r') as f:
        robot_desc = f.read()

    # ── 1. Robot State Publisher ──────────────────────────────────────
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_desc}]
    )

    # ── 2. Gazebo with coffee shop world ─────────────────────────────
    gazebo = ExecuteProcess(
        cmd=[
            'gazebo', '--verbose',
            '-s', 'libgazebo_ros_factory.so',
            world_path
        ],
        output='screen'
    )

    # ── 3. Spawn robot at entrance (door side, west wall) ─────────────
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

    # ── 4. SLAM Toolbox (online async mapping) ────────────────────────
    slam_toolbox = TimerAction(
        period=8.0,
        actions=[
            Node(
                package='slam_toolbox',
                executable='async_slam_toolbox_node',
                name='slam_toolbox',
                output='screen',
                parameters=[slam_params],
            )
        ]
    )

    # ── 5. RViz2 ──────────────────────────────────────────────────────
    rviz = TimerAction(
        period=10.0,
        actions=[
            Node(
                package='rviz2',
                executable='rviz2',
                name='rviz2',
                output='screen',
                arguments=['-d', os.path.join(pkg_path, 'config', 'slam.rviz')]
            )
        ]
    )

    return LaunchDescription([
        robot_state_publisher,
        gazebo,
        spawn_robot,
        slam_toolbox,
        rviz,
    ])
