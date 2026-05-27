#!/usr/bin/env python3
"""
rutinas_xarm.py — Movement routines for xArm Lite6 in Gazebo simulation
Usage:  python3 rutinas_xarm.py [robot A|B|C|all] [routine <name>]
"""

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import argparse
import time
import math


ROBOTS = {
    "A": "A_lite6_traj_controller",   # Left
    "B": "B_lite6_traj_controller",   # Center
    "C": "C_lite6_traj_controller",   # Right
}

JOINT_NAMES_TEMPLATE = [
    "{p}joint1", "{p}joint2", "{p}joint3",
    "{p}joint4", "{p}joint5", "{p}joint6",
]


def get_joint_names(prefix: str) -> list:
    p = f"{prefix}_" if prefix else ""
    return [t.format(p=p) for t in JOINT_NAMES_TEMPLATE]

# Each routine = list of (joint_positions_rad, time_sec)
# Lite6 approximate ranges: j1±360°, j2±118°, j3±225°, j4±360°, j5±97°, j6±360°

def routine_home():
    """Resting (home) position."""
    return [
        ([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 3.0),
    ]


def routine_greeting():
    """Waves the wrist side to side as a greeting."""
    pos_base = [0.0, -0.5, 1.2, 0.0, 0.8, 0.0]
    return [
        ([0.0, -0.5, 1.2, 0.0, 0.8,  0.8], 3.0),   # raise
        ([0.0, -0.5, 1.2, 0.0, 0.8, -0.8], 1.5),   # wrist left
        ([0.0, -0.5, 1.2, 0.0, 0.8,  0.8], 1.5),   # wrist right
        ([0.0, -0.5, 1.2, 0.0, 0.8, -0.8], 1.5),
        ([0.0, -0.5, 1.2, 0.0, 0.8,  0.8], 1.5),
        ([0.0,  0.0,  0.0, 0.0, 0.0,  0.0], 3.0),  # home
    ]


def routine_sweep():
    """Sweep left to right in an arc."""
    return [
        ([ 1.2, -0.3, 0.8, 0.0, 0.5, 0.0], 3.0),  # left
        ([ 0.6, -0.4, 1.0, 0.0, 0.6, 0.0], 2.0),
        ([ 0.0, -0.5, 1.2, 0.0, 0.7, 0.0], 2.0),  # center
        ([-0.6, -0.4, 1.0, 0.0, 0.6, 0.0], 2.0),
        ([-1.2, -0.3, 0.8, 0.0, 0.5, 0.0], 2.0),  # right
        ([ 0.0,  0.0, 0.0, 0.0, 0.0, 0.0], 3.0),  # home
    ]


def routine_pick_place():
    """Simulate a basic pick & place cycle."""
    return [
        # Approach object
        ([0.3, 0.2, 0.5, 0.0, -0.5, 0.0], 3.0),
        # Lower
        ([0.3, 0.5, 0.9, 0.0, -0.7, 0.0], 2.0),
        # "Grasp" (pause)
        ([0.3, 0.5, 0.9, 0.0, -0.7, 0.0], 1.5),
        # Lift with object
        ([0.3, 0.2, 0.5, 0.0, -0.5, 0.0], 2.0),
        # Move to destination
        ([-0.6, 0.2, 0.5, 0.0, -0.5, 0.0], 3.0),
        # Lower at destination
        ([-0.6, 0.5, 0.9, 0.0, -0.7, 0.0], 2.0),
        # "Release"
        ([-0.6, 0.5, 0.9, 0.0, -0.7, 0.0], 1.5),
        # Lift and return
        ([-0.6, 0.2, 0.5, 0.0, -0.5, 0.0], 2.0),
        ([0.0,  0.0, 0.0, 0.0,  0.0, 0.0], 3.0),  # home
    ]


def routine_circle():
    """Move joints in a sinusoidal pattern to create a circular effect."""
    steps = []
    n = 16  # circle points
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        j1 = 0.6 * math.sin(t)
        j2 = -0.3 + 0.2 * math.cos(t)
        j3 =  0.8 + 0.2 * math.sin(t + math.pi / 4)
        j4 =  0.3 * math.cos(t)
        j5 =  0.5 + 0.15 * math.sin(t)
        j6 =  0.4 * math.cos(t)
        steps.append(([j1, j2, j3, j4, j5, j6], 1.0))
    steps.append(([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 3.0))  # home
    return steps


def routine_inspection():
    """Move the arm as if inspecting a part from different angles."""
    return [
        # Front view
        ([0.0,  -0.3, 0.7, 0.0,  0.5, 0.0], 3.0),
        # Tilt left
        ([0.4,  -0.3, 0.7, 0.3,  0.5, 0.0], 2.0),
        # Tilt up
        ([0.0,  -0.6, 1.0, 0.0,  0.3, 0.0], 2.0),
        # Tilt right
        ([-0.4, -0.3, 0.7, -0.3, 0.5, 0.0], 2.0),
        # Rotate wrist
        ([0.0,  -0.3, 0.7, 0.0,  0.5, 1.5], 2.0),
        ([0.0,  -0.3, 0.7, 0.0,  0.5,-1.5], 2.0),
        # Home
        ([0.0,   0.0, 0.0, 0.0,  0.0, 0.0], 3.0),
    ]


ROUTINES = {
    "home":       routine_home,
    "greeting":   routine_greeting,
    "sweep":      routine_sweep,
    "pick_place": routine_pick_place,
    "circle":     routine_circle,
    "inspection": routine_inspection,
}


class XArmRoutineRunner(Node):
    def __init__(self, robot_keys: list, routine_name: str):
        super().__init__("xarm_routine_runner")
        self.publishers = {}

        for key in robot_keys:
            controller = ROBOTS[key]
            topic = f"/{controller}/joint_trajectory"
            pub = self.create_publisher(JointTrajectory, topic, 10)
            self.publishers[key] = (pub, get_joint_names(key))
            self.get_logger().info(f"Robot {key} → {topic}")

        self.routine_name = routine_name
        self.timer = self.create_timer(1.5, self.run_once)
        self._ran = False

    def run_once(self):
        if self._ran:
            return
        self._ran = True
        self.timer.cancel()

        if self.routine_name not in ROUTINES:
            self.get_logger().error(
                f"Routine '{self.routine_name}' does not exist. "
                f"Available: {list(ROUTINES.keys())}"
            )
            return

        steps = ROUTINES[self.routine_name]()
        self.get_logger().info(
            f"▶ Executing routine '{self.routine_name}' "
            f"({len(steps)} steps) on robots: {list(self.publishers.keys())}"
        )

        accum_time = 0.0
        for robot_key, (pub, joint_names) in self.publishers.items():
            traj = JointTrajectory()
            traj.joint_names = joint_names
            accum_time = 0.0

            for position, duration in steps:
                pt = JointTrajectoryPoint()
                pt.positions = [float(v) for v in position]
                pt.velocities = [0.0] * 6
                accum_time += duration
                pt.time_from_start = Duration(
                    sec=int(accum_time),
                    nanosec=int((accum_time % 1) * 1e9),
                )
                traj.points.append(pt)

            pub.publish(traj)
            self.get_logger().info(
                f"  ✓ Robot {robot_key}: trajectory published "
                f"({accum_time:.1f}s total)"
            )

        self.get_logger().info(
            f"Routine sent. Wait ~{accum_time:.0f}s to complete."
        )

def interactive_menu():
    print("\n" + "═" * 50)
    print("  xArm Lite6 — Simulation Routines")
    print("═" * 50)

    print("\nWhich robot(s) do you want to move?")
    print("  A = Left  |  B = Center  |  C = Right  |  all = All three")
    robot_input = input("Robot [all]: ").strip().upper() or "ALL"

    if robot_input == "ALL":
        robot_keys = list(ROBOTS.keys())
    elif robot_input in ROBOTS:
        robot_keys = [robot_input]
    else:
        print(f"Invalid option: {robot_input}")
        return None, None

    print("\nWhich routine?")
    for i, name in enumerate(ROUTINES.keys(), 1):
        print(f"  {i}. {name}")
    routine_input = input("Routine [greeting]: ").strip() or "greeting"

    # Accept number or name
    if routine_input.isdigit():
        idx = int(routine_input) - 1
        routine_name = list(ROUTINES.keys())[idx]
    elif routine_input in ROUTINES:
        routine_name = routine_input
    else:
        print(f"Invalid routine: {routine_input}")
        return None, None

    return robot_keys, routine_name


def main():
    parser = argparse.ArgumentParser(description="xArm Lite6 movement routines")
    parser.add_argument("robot", nargs="?", default=None,
                        help="A, B, C or all (default: interactive menu)")
    parser.add_argument("routine", nargs="?", default=None,
                        help=f"Routine name: {list(ROUTINES.keys())}")
    args = parser.parse_args()

    rclpy.init()

    # If no args provided, show interactive menu
    if args.robot is None and args.routine is None:
        robot_keys, routine_name = interactive_menu()
    else:
        r = (args.robot or "all").upper()
        robot_keys = list(ROBOTS.keys()) if r == "ALL" else [r]
        routine_name = args.routine or "greeting"

    if robot_keys is None:
        rclpy.shutdown()
        return

    node = XArmRoutineRunner(robot_keys, routine_name)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
