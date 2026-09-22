#!/bin/bash
echo "🤖 Iniciando Digital Shadow Triple Lite6..."

# Red
sudo ip link set enp3s0 up
sudo ip addr add 192.168.0.100/24 dev enp3s0 2>/dev/null || true
sudo ip route add 224.0.0.0/4 dev wlo1 2>/dev/null || true

# Terminal 1 - Gazebo
gnome-terminal --title="1. Gazebo" -- bash -c "
  source ~/.bashrc
  ros2 launch xarm_gazebo triple_lite6_gazebo.launch.py load_controller:=true
  exec bash"

echo "⏳ Esperando Gazebo (20s)..."
sleep 20

# Terminal 2 - Driver físicos
gnome-terminal --title="2. Driver xArms" -- bash -c "
  source ~/.bashrc
  ros2 launch xarm_api triple_lite6_driver.launch.py
  exec bash"

echo "⏳ Esperando driver (10s)..."
sleep 10

# Terminal 3 - Shadow Bridge
gnome-terminal --title="3. Shadow Bridge" -- bash -c "
  source ~/.bashrc
  python3 ~/ros2_ws/src/xarm_ros2/xarm_gazebo/scripts/shadow_bridge.py
  exec bash"

# Terminal 4 - Shadow Controller
gnome-terminal --title="4. Shadow Controller" -- bash -c "
  source ~/.bashrc
  python3 ~/ros2_ws/src/xarm_ros2/xarm_gazebo/scripts/shadow_controller.py
  exec bash"

echo "⏳ Esperando controllers (8s)..."
sleep 8

# Desactivar joint_state_broadcaster
ros2 control set_controller_state joint_state_broadcaster inactive 2>/dev/null || true

# Modo manual en los 3 robots
echo "🔧 Configurando modo manual..."
ros2 service call /ufactory/set_mode xarm_msgs/srv/SetInt16 "{data: 2}" 2>/dev/null || true
ros2 service call /ufactory/set_state xarm_msgs/srv/SetInt16 "{data: 0}" 2>/dev/null || true

echo "✅ Digital Shadow listo!"
