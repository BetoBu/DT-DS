import rclpy
from rclpy.node import Node
from xarm_msgs.srv import MoveCartesian

class SimLineController(Node):
    def __init__(self):
        super().__init__('sim_line_controller')
        # Creamos clientes para los servicios de cada brazo en la simulación
        self.clients = {
            'arm1': self.create_client(MoveCartesian, '/xarm1/move_cartesian'),
            'arm2': self.create_client(MoveCartesian, '/xarm2/move_cartesian'),
            'arm3': self.create_client(MoveCartesian, '/xarm3/move_cartesian')
        }

    def send_movement(self, arm_name, x_inch, y_inch, z_inch):
        client = self.clients[arm_name]
        while not client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(f'Esperando servicio de {arm_name}...')
        
        req = MoveCartesian.Request()
        # Conversión de Pulgadas a Metros
        req.pose = [x_inch * 0.0254, y_inch * 0.0254, z_inch * 0.0254, 3.14, 0.0, 0.0]
        req.speed = 200.0
        req.acc = 2000.0
        
        return client.call_async(req)

def main():
    rclpy.init()
    controller = SimLineController()
    
    # Ejemplo: Mover el brazo 2 a 15 pulgadas en X, 0 en Y, 10 en Z
    controller.send_movement('arm2', 15.0, 0.0, 10.0)
    
    rclpy.spin(controller)
    rclpy.shutdown()