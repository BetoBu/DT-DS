Conectar la red
sudo ip link set enp3s0 up
sudo ip addr add 192.168.0.100/24 dev enp3s0

Terminal 1 — Simulación Gazebo
ros2 launch xarm_gazebo triple_lite6_gazebo.launch.py load_controller:=true


Terminal 2 — Driver brazos físicos
ros2 launch xarm_api triple_lite6_driver.launch.py

Terminal 3 — Shadow Bridge
python3 ~/ros2_ws/src/xarm_ros2/xarm_gazebo/scripts/shadow_bridge.py

Terminal 4 — Activar controllers (si B falla)
ros2 control load_controller --set-state active joint_state_broadcaster
ros2 control switch_controllers --activate B_lite6_traj_controller
