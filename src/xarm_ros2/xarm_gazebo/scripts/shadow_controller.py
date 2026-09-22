#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

class ShadowController(Node):
    def __init__(self):
        super().__init__('shadow_controller')
        self.pubs = {
            'a': self.create_publisher(JointTrajectory, '/A_lite6_traj_controller/joint_trajectory', 10),
            'b': self.create_publisher(JointTrajectory, '/B_lite6_traj_controller/joint_trajectory', 10),
            'c': self.create_publisher(JointTrajectory, '/C_lite6_traj_controller/joint_trajectory', 10),
        }
        for ns in ['a', 'b', 'c']:
            self.create_subscription(
                JointState,
                '/{}/xarm/joint_states'.format(ns),
                lambda msg, n=ns: self.callback(msg, n),
                10
            )
        self.get_logger().info('Shadow Controller iniciado')

    def callback(self, msg, ns):
        prefix = {'a': 'A_', 'b': 'B_', 'c': 'C_'}[ns]
        traj = JointTrajectory()
        traj.joint_names = ['{}{}'.format(prefix, n) for n in msg.name[:6]]
        point = JointTrajectoryPoint()
        point.positions = list(msg.position[:6])
        point.time_from_start = Duration(sec=0, nanosec=100000000)
        traj.points = [point]
        self.pubs[ns].publish(traj)

def main():
    rclpy.init()
    node = ShadowController()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
