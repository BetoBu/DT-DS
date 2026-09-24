###Conectar la red
"""Bash
sudo ip link set enp3s0 up

sudo ip addr add 192.168.0.100/24 dev enp3s0

"""

Terminal 1 — Simulación Gazebo

ros2 launch xarm_gazebo triple_lite6_gazebo.launch.py load_controller:=true


Terminal 2 — Driver brazos físicos

ros2 launch xarm_api triple_lite6_driver.launch.py
Conectar la red
sudo ip link set enp3s0 up
sudo ip addr add 192.168.0.100/24 dev enp3s0

Dependencias
```bash
sudo apt install ros-jazzy-topic-tools
pip3 install xarm-python-sdk supabase
```

---

## Configuración inicial (solo una vez)

### 1. Clonar e instalar dependencias
```bash
cd ~/ros2_ws/src
git clone https://github.com/BetoBu/DT-DS.git xarm_ros2
cd ~/ros2_ws
colcon build --packages-select xarm_description xarm_gazebo xarm_api
source ~/.bashrc
```

### 2. Instalar dependencias Python
```bash
pip3 install xarm-python-sdk supabase
```

### 3. Crear alias de arranque
```bash
echo "alias shadow='~/start_digital_shadow.sh'" >> ~/.bashrc
source ~/.bashrc
```

### 4. Crear script de arranque
```bash
cat > ~/start_digital_shadow.sh << 'ENDOFFILE'
#!/bin/bash
echo "Iniciando Digital Shadow Triple Lite6..."

sudo ip link set enp3s0 up
sudo ip addr add 192.168.0.100/24 dev enp3s0 2>/dev/null || true
sudo ip route add 224.0.0.0/4 dev wlo1 2>/dev/null || true

gnome-terminal --title="1. Gazebo" -- bash -c "
  source ~/.bashrc
  ros2 launch xarm_gazebo triple_lite6_gazebo.launch.py load_controller:=true
  exec bash"

echo "Esperando Gazebo (20s)..."
sleep 20

gnome-terminal --title="2. Driver xArms" -- bash -c "
  source ~/.bashrc
  ros2 launch xarm_api triple_lite6_driver.launch.py
  exec bash"

echo "Esperando driver (10s)..."
sleep 10

gnome-terminal --title="3. Shadow Bridge" -- bash -c "
  source ~/.bashrc
  python3 ~/ros2_ws/src/xarm_ros2/xarm_gazebo/scripts/shadow_bridge.py
  exec bash"

gnome-terminal --title="4. Shadow Controller" -- bash -c "
  source ~/.bashrc
  python3 ~/ros2_ws/src/xarm_ros2/xarm_gazebo/scripts/shadow_controller.py
  exec bash"

echo "Esperando controllers (8s)..."
sleep 8

ros2 control set_controller_state joint_state_broadcaster inactive 2>/dev/null || true

echo "Digital Shadow listo!"
ENDOFFILE
chmod +x ~/start_digital_shadow.sh
```

---

## Uso diario

### Arrancar el Digital Shadow
```bash
shadow
```

### Arrancar telemetría a Supabase
```bash
python3 ~/ros2_ws/src/xarm_ros2/xarm_gazebo/scripts/telemetry_collector.py
```

---

## IPs de los robots

| Robot | Prefijo | IP |
|-----------|----|---------------|
| Izquierdo | A_ | 192.168.0.184 |
| Centro    | B_ | 192.168.0.181 |
| Derecho   | C_ | 192.168.0.150 |

---

## Base de datos — Supabase

La tabla `robot_telemetry` almacena cada 2 segundos:
- Ángulos de los 6 joints (radianes)
- Temperatura de cada servo (°C)
- Corriente de cada servo (A)
- Voltaje de cada servo (V)
- Posición cartesiana XYZ + RPY
- Estado, código de error y warning

---

## Notas importantes

- La interfaz de red `enp3s0` debe estar conectada al switch de los robots
- El script de arranque asigna automáticamente la IP `192.168.0.100` a esa interfaz
- Si el controller B falla al arrancar, correr manualmente:
```bash
ros2 control switch_controllers --activate B_lite6_traj_controller
```

---

## Tabla en Supabase Eliminada
Si borraste la tabla de Supabase y ahora el codigo no funciona, haz los siguientes pasos:
Entra al Apartado SQL y corre este codigo:

```bash
CREATE TABLE robot_telemetry (
  id bigserial PRIMARY KEY,
  timestamp timestamptz DEFAULT now(),
  robot_id text NOT NULL,
  joint1_angle float, joint2_angle float, joint3_angle float,
  joint4_angle float, joint5_angle float, joint6_angle float,
  joint1_temp float, joint2_temp float, joint3_temp float,
  joint4_temp float, joint5_temp float, joint6_temp float,
  joint1_current float, joint2_current float, joint3_current float,
  joint4_current float, joint5_current float, joint6_current float,
  joint1_voltage float, joint2_voltage float, joint3_voltage float,
  joint4_voltage float, joint5_voltage float, joint6_voltage float,
  pos_x float, pos_y float, pos_z float,
  roll float, pitch float, yaw float,
  state int, error_code int, warn_code int
);
```

Despues corre esto:
```
CREATE POLICY "Allow all inserts" ON robot_telemetry
FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow all selects" ON robot_telemetry
FOR SELECT USING (true);
```
