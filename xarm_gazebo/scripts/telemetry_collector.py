#!/usr/bin/env python3
import time
from xarm.wrapper import XArmAPI
from supabase import create_client

# Configuración Supabase
SUPABASE_URL = "https://snpmlhmqgsbnipwfiejf.supabase.co"
SUPABASE_KEY = "sb_publishable_x8q3q3ePjgbVUdRELkzfLA_EvcVwavg"

# Robots
ROBOTS = [
    {'id': 'A', 'ip': '192.168.0.184'},
    {'id': 'B', 'ip': '192.168.0.181'},
    {'id': 'C', 'ip': '192.168.0.150'},
]

INTERVAL = 2  # segundos entre cada lectura

def collect_and_send(supabase, arm, robot_id):
    try:
        _, angles  = arm.get_servo_angle()
        _, pose    = arm.get_position()
        temps      = arm.temperatures
        currents   = arm.currents
        voltages   = arm.voltages

        data = {
            'robot_id':       robot_id,
            'joint1_angle':   angles[0],  'joint2_angle': angles[1],
            'joint3_angle':   angles[2],  'joint4_angle': angles[3],
            'joint5_angle':   angles[4],  'joint6_angle': angles[5],
            'joint1_temp':    temps[0],   'joint2_temp':  temps[1],
            'joint3_temp':    temps[2],   'joint4_temp':  temps[3],
            'joint5_temp':    temps[4],   'joint6_temp':  temps[5],
            'joint1_current': currents[0],'joint2_current':currents[1],
            'joint3_current': currents[2],'joint4_current':currents[3],
            'joint5_current': currents[4],'joint6_current':currents[5],
            'joint1_voltage': voltages[0],'joint2_voltage':voltages[1],
            'joint3_voltage': voltages[2],'joint4_voltage':voltages[3],
            'joint5_voltage': voltages[4],'joint6_voltage':voltages[5],
            'pos_x':    pose[0], 'pos_y':  pose[1], 'pos_z':  pose[2],
            'roll':     pose[3], 'pitch':  pose[4], 'yaw':    pose[5],
            'state':      arm.state,
            'error_code': arm.error_code,
            'warn_code':  arm.warn_code,
        }

        supabase.table('robot_telemetry').insert(data).execute()
        print(f"✅ Robot {robot_id} — T:[{temps[0]},{temps[1]},{temps[2]}]°C  V:{voltages[0]:.1f}V")

    except Exception as e:
        print(f"❌ Robot {robot_id} error: {e}")

def main():
    print("🚀 Iniciando colector de telemetría...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    arms = {}
    for r in ROBOTS:
        try:
            arm = XArmAPI(r['ip'], is_radian=True, report_type='rich')
            time.sleep(1)
            arms[r['id']] = arm
            print(f"✅ Robot {r['id']} conectado ({r['ip']})")
        except Exception as e:
            print(f"❌ Robot {r['id']} no conectó: {e}")

    print(f"\n📡 Enviando datos cada {INTERVAL}s a Supabase...\n")

    try:
        while True:
            for robot_id, arm in arms.items():
                collect_and_send(supabase, arm, robot_id)
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\n⏹ Colector detenido")
        for arm in arms.values():
            arm.disconnect()

if __name__ == '__main__':
    main()
