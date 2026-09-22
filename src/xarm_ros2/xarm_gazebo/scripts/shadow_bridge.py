#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from sensor_msgs.msg import JointState

class ShadowBridge(Node):
    def __init__(self):
        super().__init__('shadow_bridge')
        qos = QoSProfile(
            depth=10,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE
        )
        self.pub = self.create_publisher(JointState, '/joint_states', qos)
        self.latest = {}
        for ns in ['a', 'b', 'c']:
            self.create_subscription(
                JointState,
                '/{}/xarm/joint_states'.format(ns),
                lambda msg, n=ns: self.callback(msg, n),
                10
            )
        self.create_timer(0.04, self.publish_combined)
        self.get_logger().info('Shadow Bridge iniciado para A, B, C')

    def callback(self, msg, ns):
        prefix = {'a': 'A_', 'b': 'B_', 'c': 'C_'}[ns]
        self.latest[ns] = (prefix, msg)

    def publish_combined(self):
        if not self.latest:
            return
        out = JointState()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = ''
        names = []
        positions = []
        velocities = []
        efforts = []
        for ns in ['a', 'b', 'c']:
            if ns in self.latest:
                prefix, msg = self.latest[ns]
                names     += ['{}{}'.format(prefix, n) for n in msg.name[:6]]
                positions += list(msg.position[:6])
                velocities+= list(msg.velocity[:6])
                efforts   += list(msg.effort[:6])
        out.name     = names
        out.position = positions
        out.velocity = velocities
        out.effort   = efforts
        self.pub.publish(out)

def main():
    rclpy.init()
    node = ShadowBridge()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
