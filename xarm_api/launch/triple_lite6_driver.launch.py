#!/usr/bin/env python3
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    robots = [
        {'prefix': 'A_', 'ip': '192.168.0.184'},  # izquierdo
        {'prefix': 'B_', 'ip': '192.168.0.181'},  # centro
        {'prefix': 'C_', 'ip': '192.168.0.150'},  # derecha
    ]
    nodes = []
    for r in robots:
        nodes.append(Node(
            package='xarm_api',
            executable='xarm_driver_node',
            name='xarm_driver_{}'.format(r['prefix'].replace('_','')),
            namespace=r['prefix'].replace('_','').lower(),
            parameters=[{
                'robot_ip': r['ip'],
                'report_type': 'normal',
            }],
            output='screen',
        ))
    return LaunchDescription(nodes)
