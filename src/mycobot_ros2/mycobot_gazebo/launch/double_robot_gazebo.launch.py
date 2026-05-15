import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    pkg_mycobot_gazebo = FindPackageShare(package='mycobot_gazebo').find('mycobot_gazebo')
    
    # Función para crear una instancia de robot
    def spawn_robot(name, x_pos, y_pos):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                os.path.join(pkg_mycobot_gazebo, 'launch', 'mycobot.gazebo.launch.py')
            ]),
            launch_arguments={
                'robot_name': name,
                'namespace': name,
                'x': x_pos,
                'y': y_pos,
                'z': '0.05',
                'use_rviz': 'false', # Solo un RViz para evitar lag
                'load_controllers': 'true'
            }.items()
        )

    return LaunchDescription([
        spawn_robot('robot1', '0.0', '0.0'),
        spawn_robot('robot2', '1.0', '0.0') # Separado 1 metro
    ])