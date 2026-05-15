import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    pkg_gazebo = FindPackageShare('mycobot_gazebo').find('mycobot_gazebo')

    def crear_instancia_robot(nombre, x_pos, y_pos):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo, 'launch', 'mycobot.gazebo.launch.py')
            ),
            launch_arguments={
                'robot_name': nombre,
                'namespace': nombre,
                'prefix': nombre + '_', # Aquí le mandamos el prefijo que tu código ya esperaba
                'x': x_pos,
                'y': y_pos,
                'z': '0.1',
                'load_controllers': 'true',
                'use_rviz': 'false' 
            }.items()
        )

    return LaunchDescription([
        crear_instancia_robot('robot1', '0.0', '0.0'),
        crear_instancia_robot('robot2', '1.0', '0.0') # Separado por 1 metro en X
    ])