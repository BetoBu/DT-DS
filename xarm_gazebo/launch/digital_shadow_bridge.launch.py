#!/usr/bin/env python3
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    nodes = []
    for real_ns in ['a', 'b', 'c']:
        nodes.append(Node(
            package='topic_tools',
            executable='relay',
            name='shadow_relay_{}'.format(real_ns),
            arguments=[
                '/{}/xarm/joint_states'.format(real_ns),
                '/joint_states',
            ],
            output='screen',
        ))
    return LaunchDescription(nodes)
