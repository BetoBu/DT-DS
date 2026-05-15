#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
#     (          ) ESte lo puedes llamar como quieras, solo que coincida con el nodo de main
class MyFirstNode(Node):
    def __init__(self):#(               )Igual aqui
        super().__init__('my_first_node')
        self.get_logger().info('Hello, ROS 2!')

def main(args=None):
    rclpy.init(args=args)
#          (          ) ESte lo puedes llamar como quieras,    
    node = MyFirstNode()

    rclpy.shutdown()

if __name__ == '__main__':
    main()