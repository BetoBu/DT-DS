#!/usr/bin/env python3
"""
Launch Gazebo simulation with TWO myCobot robots, each individually controllable.
"""

import os
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    GroupAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    package_name_gazebo = 'mycobot_gazebo'
    package_name_description = 'mycobot_description'
    package_name_moveit = 'mycobot_moveit_config'

    default_robot_name = 'mycobot_280'
    default_world_file = 'pick_and_place_demo.world'
    gazebo_worlds_path = 'worlds'
    gazebo_models_path = 'models'
    ros_gz_bridge_config_file_path = 'config/ros_gz_bridge.yaml'

    pkg_ros_gz_sim = FindPackageShare(package='ros_gz_sim').find('ros_gz_sim')
    pkg_share_gazebo = FindPackageShare(package=package_name_gazebo).find(package_name_gazebo)
    pkg_share_description = FindPackageShare(
        package=package_name_description).find(package_name_description)
    pkg_share_moveit = FindPackageShare(package=package_name_moveit).find(package_name_moveit)

    gazebo_models_full_path = os.path.join(pkg_share_gazebo, gazebo_models_path)
    default_ros_gz_bridge_config_file_path = os.path.join(
        pkg_share_gazebo, ros_gz_bridge_config_file_path)

    # ── Argumentos globales ──────────────────────────────────────────────────
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name='use_sim_time', default_value='true',
        description='Use simulation (Gazebo) clock if true')

    declare_use_rviz_cmd = DeclareLaunchArgument(
        name='use_rviz', default_value='true',
        description='Flag to enable RViz')

    declare_use_camera_cmd = DeclareLaunchArgument(
        name='use_camera', default_value='false',
        description='Flag to enable RGBD camera')

    declare_world_cmd = DeclareLaunchArgument(
        name='world_file', default_value=default_world_file,
        description='World file name')

    declare_load_controllers_cmd = DeclareLaunchArgument(
        name='load_controllers', default_value='true',
        description='Flag to enable loading ROS 2 controllers')

    use_sim_time   = LaunchConfiguration('use_sim_time')
    use_rviz       = LaunchConfiguration('use_rviz')
    use_camera     = LaunchConfiguration('use_camera')
    world_file     = LaunchConfiguration('world_file')
    load_controllers = LaunchConfiguration('load_controllers')

    world_path = PathJoinSubstitution([
        pkg_share_gazebo, gazebo_worlds_path, world_file
    ])

    # Ruta al YAML de controladores (el que SÍ existe, sin subcarpeta de robot)
    robot_controllers_path = os.path.join(
        pkg_share_moveit, 'config', 'mycobot_280', 'ros2_controllers.yaml')

    # ── Gazebo ───────────────────────────────────────────────────────────────
    set_env_vars_resources = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH', gazebo_models_full_path)

    start_gazebo_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments=[('gz_args', [' -r -v 4 ', world_path])])

    start_gazebo_ros_bridge_cmd = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': default_ros_gz_bridge_config_file_path}],
        output='screen'
    )

    # ── Helper: genera el grupo completo para un robot ───────────────────────
    def make_robot_group(namespace: str, x: str, y: str, yaw: str):
        """
        Devuelve un GroupAction con namespace propio para un robot.
        Cada robot tiene su robot_state_publisher, controladores y spawner.
        """
        robot_name = f'{default_robot_name}_{namespace}'

        rsp = IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                os.path.join(pkg_share_description, 'launch',
                             'robot_state_publisher.launch.py')
            ]),
            launch_arguments={
                'jsp_gui':             'false',
                'use_camera':          use_camera,
                'use_gazebo':          'true',
                'use_rviz':            use_rviz,
                'use_sim_time':        use_sim_time,
                # Pasamos el namespace para que el RSP publique en /<ns>/robot_description
                'namespace':           namespace,
            }.items(),
        )

        controllers = IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                os.path.join(pkg_share_moveit, 'launch',
                             'load_ros2_controllers.launch.py')
            ]),
            launch_arguments={
                'use_sim_time':    use_sim_time,
                'controllers_file': robot_controllers_path,
                'robot_name':       robot_name,
                'namespace':        namespace,
            }.items(),
            condition=IfCondition(load_controllers),
        )

        spawner = Node(
            package='ros_gz_sim',
            executable='create',
            output='screen',
            arguments=[
                '-topic',           f'/{namespace}/robot_description',
                '-name',            robot_name,
                '-allow_renaming',  'true',
                '-x', x,
                '-y', y,
                '-z', '0.05',
                '-R', '0.0',
                '-P', '0.0',
                '-Y', yaw,
            ]
        )

        return GroupAction(actions=[
            PushRosNamespace(namespace),
            rsp,
            controllers,
            spawner,
        ])

    robot1_group = make_robot_group(namespace='robot1', x='0.0',  y='0.0',  yaw='0.0')
    robot2_group = make_robot_group(namespace='robot2', x='1.0',  y='0.0',  yaw='0.0')

    # ── Ensamblar LaunchDescription ──────────────────────────────────────────
    ld = LaunchDescription()

    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_use_rviz_cmd)
    ld.add_action(declare_use_camera_cmd)
    ld.add_action(declare_world_cmd)
    ld.add_action(declare_load_controllers_cmd)

    ld.add_action(set_env_vars_resources)
    ld.add_action(start_gazebo_cmd)
    ld.add_action(start_gazebo_ros_bridge_cmd)

    ld.add_action(robot1_group)
    ld.add_action(robot2_group)

    return ld