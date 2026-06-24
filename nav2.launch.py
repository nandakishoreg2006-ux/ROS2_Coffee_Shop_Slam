"""
nav2.launch.py
==============
Launches full Nav2 autonomous navigation on the saved coffee shop map.
The map is loaded directly from the src/mypkg/map/ directory so you do NOT
need to rebuild the package every time you save a new map.

AMCL initial pose is pre-set to the spawn point (-4.5, 0.0).
In RViz you can also click '2D Pose Estimate' to correct it if needed,
then use '2D Goal Pose' to send navigation goals.
"""

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_path = get_package_share_directory('mypkg')

    urdf_path   = os.path.join(pkg_path, 'urdf',   'urdfbot_simple.urdf')
    world_path  = os.path.join(pkg_path, 'worlds',  'coffee_shop.world')
    nav2_params = os.path.join(pkg_path, 'config',  'nav2_params.yaml')
    rviz_config = os.path.join(pkg_path, 'config',  'nav2.rviz')

    # Map lives in src so we read from there — no rebuild needed after map_saver
    map_yaml = os.path.join(
        os.path.expanduser('~'),
        'ros_ws4', 'src', 'mypkg', 'map', 'coffee_shop_map.yaml'
    )

    if not os.path.exists(map_yaml):
        raise FileNotFoundError(
            f"\n\n[nav2.launch] Map not found at:\n  {map_yaml}\n\n"
            "Run SLAM first:\n"
            "  ros2 launch mypkg slam.launch.py\n"
            "Then save:\n"
            "  ros2 run nav2_map_server map_saver_cli "
            "-f ~/ros_ws4/src/mypkg/map/coffee_shop_map\n"
        )

    with open(urdf_path, 'r') as f:
        robot_desc = f.read()

    # ── 1. Robot State Publisher ──────────────────────────────────────
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_desc,
            'use_sim_time': True
        }]
    )

    # ── 2. Gazebo + coffee shop world ────────────────────────────────
    gazebo = ExecuteProcess(
        cmd=[
            'gazebo', '--verbose',
            '-s', 'libgazebo_ros_factory.so',
            world_path
        ],
        output='screen'
    )

    # ── 3. Spawn robot at mapping start pose ─────────────────────────
    spawn_robot = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='gazebo_ros',
                executable='spawn_entity.py',
                arguments=[
                    '-entity', 'urdfbot_simple',
                    '-topic', 'robot_description',
                    '-x', '-4.5', '-y', '0.0', '-z', '0.15', '-Y', '0.0'
                ],
                output='screen'
            )
        ]
    )

    # ── 4. Map Server ────────────────────────────────────────────────
    map_server = TimerAction(
        period=7.0,
        actions=[
            Node(
                package='nav2_map_server',
                executable='map_server',
                name='map_server',
                output='screen',
                parameters=[{
                    'use_sim_time': True,
                    'yaml_filename': map_yaml
                }]
            )
        ]
    )

    # ── 5. AMCL ──────────────────────────────────────────────────────
    amcl = TimerAction(
        period=7.0,
        actions=[
            Node(
                package='nav2_amcl',
                executable='amcl',
                name='amcl',
                output='screen',
                parameters=[nav2_params]
            )
        ]
    )

    # ── 6. Lifecycle Manager: localization ───────────────────────────
    lifecycle_localization = TimerAction(
        period=9.0,
        actions=[
            Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_localization',
                output='screen',
                parameters=[{
                    'use_sim_time': True,
                    'autostart': True,
                    'node_names': ['map_server', 'amcl']
                }]
            )
        ]
    )

    # ── 7. Controller Server (Regulated Pure Pursuit) ─────────────────
    controller_server = TimerAction(
        period=7.0,
        actions=[
            Node(
                package='nav2_controller',
                executable='controller_server',
                name='controller_server',
                output='screen',
                parameters=[nav2_params],
                remappings=[('cmd_vel', 'cmd_vel')]
            )
        ]
    )

    # ── 8. Smoother Server ───────────────────────────────────────────
    smoother_server = TimerAction(
        period=7.0,
        actions=[
            Node(
                package='nav2_smoother',
                executable='smoother_server',
                name='smoother_server',
                output='screen',
                parameters=[nav2_params]
            )
        ]
    )

    # ── 9. Planner Server (NavFn) ────────────────────────────────────
    planner_server = TimerAction(
        period=7.0,
        actions=[
            Node(
                package='nav2_planner',
                executable='planner_server',
                name='planner_server',
                output='screen',
                parameters=[nav2_params]
            )
        ]
    )

    # ── 10. Behavior Server ──────────────────────────────────────────
    behavior_server = TimerAction(
        period=7.0,
        actions=[
            Node(
                package='nav2_behaviors',
                executable='behavior_server',
                name='behavior_server',
                output='screen',
                parameters=[nav2_params]
            )
        ]
    )

    # ── 11. BT Navigator ─────────────────────────────────────────────
    bt_navigator = TimerAction(
        period=7.0,
        actions=[
            Node(
                package='nav2_bt_navigator',
                executable='bt_navigator',
                name='bt_navigator',
                output='screen',
                parameters=[nav2_params]
            )
        ]
    )

    # ── 12. Waypoint Follower ────────────────────────────────────────
    waypoint_follower = TimerAction(
        period=7.0,
        actions=[
            Node(
                package='nav2_waypoint_follower',
                executable='waypoint_follower',
                name='waypoint_follower',
                output='screen',
                parameters=[nav2_params]
            )
        ]
    )

    # ── 13. Velocity Smoother ────────────────────────────────────────
    velocity_smoother = TimerAction(
        period=7.0,
        actions=[
            Node(
                package='nav2_velocity_smoother',
                executable='velocity_smoother',
                name='velocity_smoother',
                output='screen',
                parameters=[nav2_params],
                remappings=[
                    ('cmd_vel', 'cmd_vel_nav'),
                    ('cmd_vel_smoothed', 'cmd_vel')
                ]
            )
        ]
    )

    # ── 14. Lifecycle Manager: navigation ────────────────────────────
    lifecycle_navigation = TimerAction(
        period=10.0,
        actions=[
            Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_navigation',
                output='screen',
                parameters=[{
                    'use_sim_time': True,
                    'autostart': True,
                    'node_names': [
                        'controller_server',
                        'smoother_server',
                        'planner_server',
                        'behavior_server',
                        'bt_navigator',
                        'waypoint_follower',
                    ]
                }]
            )
        ]
    )

    # ── 15. RViz2 ─────────────────────────────────────────────────────
    # LIBGL_ALWAYS_SOFTWARE=1: forces Mesa llvmpipe (software) renderer.
    # This is the only guaranteed fix (without root) for the GLSL 120
    # "active samplers with a different type refer to the same texture
    # image unit" bug that makes costmap inflation colors render as black.
    # llvmpipe correctly handles the sampler unit assignment and renders
    # the full blue→pink costmap gradient.
    rviz = TimerAction(
        period=13.0,
        actions=[
            Node(
                package='rviz2',
                executable='rviz2',
                name='rviz2',
                output='screen',
                arguments=['-d', rviz_config],
                parameters=[{'use_sim_time': True}],
                additional_env={
                    'LIBGL_ALWAYS_SOFTWARE': '1',
                    'GALLIUM_DRIVER':        'llvmpipe'
                }
            )
        ]
    )

    return LaunchDescription([
        robot_state_publisher,
        gazebo,
        spawn_robot,
        map_server,
        amcl,
        lifecycle_localization,
        controller_server,
        smoother_server,
        planner_server,
        behavior_server,
        bt_navigator,
        waypoint_follower,
        lifecycle_navigation,
        rviz,
    ])
