#!/usr/bin/env python3
# Digital Shadow - Triple xArm Lite6
# Ignition Fortress (ign gazebo) + ROS 2 Humble
#
# Uso:
#   ros2 launch xarm_gazebo triple_lite6_gazebo.launch.py
#   ros2 launch xarm_gazebo triple_lite6_gazebo.launch.py load_controller:=true
#   ros2 launch xarm_gazebo triple_lite6_gazebo.launch.py show_rviz:=true

import os
import yaml
import tempfile
from pathlib import Path
from ament_index_python import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch.conditions import IfCondition
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessExit, OnProcessStart
from uf_ros_lib.uf_robot_utils import get_xacro_content, add_prefix_to_ros2_control_params


# ---------------------------------------------------------------------------
# Helper: genera un archivo temporal de parámetros combinando 3 robots
# ---------------------------------------------------------------------------
def generate_triple_ros2_control_params(prefix_1, prefix_2, prefix_3, update_rate=1000):
    base_cfg = os.path.join(
        get_package_share_directory('xarm_controller'),
        'config', 'lite6_controllers.yaml'
    )

    def load_and_prefix(prefix):
        with open(base_cfg, 'r') as f:
            params = yaml.safe_load(f)
        params['controller_manager']['ros__parameters']['update_rate'] = update_rate
        params['controller_manager']['ros__parameters']['use_sim_time'] = True
        add_prefix_to_ros2_control_params(prefix, params)
        return params

    p1 = load_and_prefix(prefix_1)
    p2 = load_and_prefix(prefix_2)
    p3 = load_and_prefix(prefix_3)

    combined = {}
    combined.update(p1)
    combined.update(p2)
    combined.update(p3)
    # controller_manager solo debe aparecer una vez con las entradas de los 3
    combined['controller_manager'] = {'ros__parameters': {}}
    combined['controller_manager']['ros__parameters'].update(
        p1['controller_manager']['ros__parameters'])
    combined['controller_manager']['ros__parameters'].update(
        p2['controller_manager']['ros__parameters'])
    combined['controller_manager']['ros__parameters'].update(
        p3['controller_manager']['ros__parameters'])

    with tempfile.NamedTemporaryFile(mode='w', prefix='triple_ctrl_', suffix='.yaml', delete=False) as f:
        yaml.dump(combined, f, default_flow_style=False)
        return f.name


# ---------------------------------------------------------------------------
# Setup principal
# ---------------------------------------------------------------------------
def launch_setup(context, *args, **kwargs):
    prefix_1      = LaunchConfiguration('prefix_1',      default='A_').perform(context)
    prefix_2      = LaunchConfiguration('prefix_2',      default='B_').perform(context)
    prefix_3      = LaunchConfiguration('prefix_3',      default='C_').perform(context)
    load_controller = LaunchConfiguration('load_controller', default='false').perform(context)
    show_rviz     = LaunchConfiguration('show_rviz',     default='false').perform(context)

    # Posiciones de los 3 robots (metros). Ajusta a tu celda real.
    # Robot 1 izquierda | Robot 2 centro | Robot 3 derecha
    attach_xyz_1 = '0 -0.8 0'
    attach_xyz_2 = '0 0 0'
    attach_xyz_3 = '0 0.8 0'

    # -----------------------------------------------------------------------
    # 1. Generar parámetros de ros2_control para los 3 robots
    # -----------------------------------------------------------------------
    ros2_control_params_file = generate_triple_ros2_control_params(
        prefix_1, prefix_2, prefix_3, update_rate=1000
    )

    # -----------------------------------------------------------------------
    # 2. Generar robot_description (URDF combinado con los 3 brazos)
    # -----------------------------------------------------------------------
    xacro_file = Path(get_package_share_directory('xarm_description')) / \
                 'urdf' / 'triple_lite6_device.urdf.xacro'

    robot_description_content = get_xacro_content(
        context,
        xacro_file=xacro_file,
        ros2_control_plugin='ign_ros2_control/IgnitionSystem',
        ros2_control_params=ros2_control_params_file,
        prefix_1=prefix_1,
        prefix_2=prefix_2,
        prefix_3=prefix_3,
        attach_xyz_1=attach_xyz_1,
        attach_xyz_2=attach_xyz_2,
        attach_xyz_3=attach_xyz_3,
    )
    robot_description = {'robot_description': robot_description_content}

    # -----------------------------------------------------------------------
    # 3. Robot State Publisher
    # -----------------------------------------------------------------------
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'use_sim_time': True}, robot_description],
        remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
    )

    # -----------------------------------------------------------------------
    # 4. Ignition Gazebo (Fortress)
    # -----------------------------------------------------------------------
    gazebo_world = PathJoinSubstitution(
        [FindPackageShare('xarm_gazebo'), 'worlds', 'table_gz.world']
    )
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py']
            )
        ),
        launch_arguments={
            'gz_args': ' -r -v 3 {}'.format(gazebo_world.perform(context)),
        }.items(),
    )

    # -----------------------------------------------------------------------
    # 5. Spawn del robot (el URDF ya contiene los 3 brazos como una sola entidad)
    # -----------------------------------------------------------------------
    gazebo_spawn_node = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-name',  'TRIPLE_LITE6',
            '-x', '-0.2',
            '-y', '-0.5',
            '-z',  '1.021',
            '-Y',  '1.571',
        ],
        parameters=[{'use_sim_time': True}],
    )

    # -----------------------------------------------------------------------
    # 6. Bridge IGN -> ROS 2 (clock + joint states)
    # -----------------------------------------------------------------------
    ign_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        output='screen',
    )

    # -----------------------------------------------------------------------
    # 7. Controllers (joint_state_broadcaster + traj_controller x3)
    # -----------------------------------------------------------------------
    controllers = [
        'joint_state_broadcaster',
        '{}lite6_traj_controller'.format(prefix_1),
        '{}lite6_traj_controller'.format(prefix_2),
        '{}lite6_traj_controller'.format(prefix_3),
    ]

    controller_nodes = []
    if load_controller in ('True', 'true'):
        for ctrl in controllers:
            controller_nodes.append(Node(
                package='controller_manager',
                executable='spawner',
                output='screen',
                arguments=[ctrl, '--controller-manager', '/controller_manager'],
                parameters=[{'use_sim_time': True}],
            ))

    # -----------------------------------------------------------------------
    # 8. Ensamblar nodos con event handlers
    # -----------------------------------------------------------------------
    nodes = [
        RegisterEventHandler(
            event_handler=OnProcessStart(
                target_action=robot_state_publisher_node,
                on_start=gazebo_launch,
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessStart(
                target_action=robot_state_publisher_node,
                on_start=gazebo_spawn_node,
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessStart(
                target_action=robot_state_publisher_node,
                on_start=ign_bridge,
            )
        ),
        robot_state_publisher_node,
    ]

    if len(controller_nodes) > 0:
        nodes.append(RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=gazebo_spawn_node,
                on_exit=controller_nodes,
            )
        ))

    return nodes


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('prefix_1',       default_value='A_',    description='Prefijo robot 1'),
        DeclareLaunchArgument('prefix_2',       default_value='B_',    description='Prefijo robot 2'),
        DeclareLaunchArgument('prefix_3',       default_value='C_',    description='Prefijo robot 3'),
        DeclareLaunchArgument('load_controller',default_value='false', description='Cargar controllers al iniciar'),
        DeclareLaunchArgument('show_rviz',      default_value='false', description='Abrir RViz2'),
        OpaqueFunction(function=launch_setup),
    ])
