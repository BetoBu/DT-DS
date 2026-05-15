###Conectar la red
"""Bash
sudo ip link set enp3s0 up

sudo ip addr add 192.168.0.100/24 dev enp3s0

"""

Terminal 1 — Simulación Gazebo

ros2 launch xarm_gazebo triple_lite6_gazebo.launch.py load_controller:=true


Terminal 2 — Driver brazos físicos

ros2 launch xarm_api triple_lite6_driver.launch.py
