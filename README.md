# Autonomous Search, Rescue & Target-Firing Mobile Robot

[![ROS 2](https://img.shields.io/badge/ROS_2-Humble%20%7C%20Iron-blue.svg)](https://docs.ros.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 100% Passed](https://img.shields.io/badge/Tests-100%25%20Passed-brightgreen.svg)](Software/tests)

An end-to-end autonomous mobile robotics system built on TurtleBot, featuring autonomous SLAM frontier exploration, real-time infrared thermal target acquisition, and a custom 3D-printed solenoid-actuated projectile mechanism.

---

## System Architecture

```mermaid
graph LR
    subgraph Sensing_and_Perception["Sensing & Perception"]
        LiDAR["2D LiDAR Scanner"] --> SLAM["ROS 2 Cartographer / Nav2"]
        Thermal["AMG8833 8x8 IR Grid"] --> PyThermal["Thermal Vision Node"]
    end

    subgraph Decision_Making["Decision & Navigation"]
        SLAM --> Explorer["Frontier Exploration Node"]
        Explorer --> GoalGen["Nav2 Goal Controller"]
        PyThermal --> LockTarget["Target Lock & Alignment"]
    end

    subgraph Actuation["Actuation & Firing"]
        GoalGen --> Motors["TurtleBot Wheels"]
        LockTarget --> Servo["Servo Safety Gate"]
        LockTarget --> Solenoid["High-Impulse Solenoid Cannon"]
    end
```

## Key Features

- **Autonomous Frontier Exploration**: Nav2-integrated frontier exploration node driving complete environment mapping without teleoperation. Uses vectorized NumPy neighbor slicing for millisecond-level frontier discovery.
- **Thermal Heat-Source Tracking**: Real-time 8x8 thermal array processing identifying temperature differentials to detect victims or simulated heat targets.
- **Precision Mechanical Launcher**: Custom CAD-modeled spring/solenoid cannon with servo gate trigger for reliable projectile deployment.
- **Distributed ROS 2 Topology**: Workstation host handles heavy SLAM mapping and RViz visualization, while an onboard Raspberry Pi manages motor drivers, thermal I2C bus, and GPIO firing triggers.
- **Dual-Mode Simulation & Hardware Abstraction**: Seamlessly operates in real hardware mode (Raspberry Pi GPIO + Adafruit AMG8833) and standalone simulation mode (Gazebo / software testbed).

## Hardware Bill of Materials (BOM)

| Component | Model / Spec | Interface |
|---|---|---|
| Mobile Base | TurtleBot3 Burger / Custom Chassis | Dynamixel / UART |
| Onboard SBC | Raspberry Pi 4 Model B (4GB) | GPIO / I2C |
| Thermal Sensor | Panasonic / Adafruit AMG8833 | I2C (0x69) |
| Actuators | 12V Push-Pull Solenoid & SG90 Micro Servo | High-current MOSFET switch + GPIO PWM |
| 3D Enclosure | PLA+ 3D printed brackets, barrel, & plunger | Custom SolidWorks files in `/cad` |

## Repository Structure

```
├── cad/                     # 3D printable STL and STEP mechanical files
├── Electrical/              # Schematics and sensor application datasheets
├── Software/
│   ├── cde2310/             # Main ROS 2 package (nodes, launch, params)
│   │   ├── launch/          # full_autonomy_launch.py, rpi.py, laptop.py
│   │   ├── config/          # nav2_params.yaml
│   │   └── cde2310/         # Thermal detection and motion control nodes
│   ├── workspace/           # Colcon workspace sources
│   └── tests/               # Automated maze simulation & unit test trials
└── LICENSE                  # MIT License
```

## Quick Start

### 1. Build the ROS 2 Workspace
```bash
cd Software/workspace
colcon build --symlink-install
source install/setup.bash
```

### 2. Launch Autonomous Search & Fire Routine
On the Raspberry Pi:
```bash
ros2 launch cde2310 rpi.py
```
On the workstation:
```bash
ros2 launch cde2310 laptop.py
```

### 3. Run Automated Maze Simulation Trials
To run the autonomous corridor exploration and thermal target neutralization testbed without physical hardware:
```bash
python Software/tests/test_maze_exploration.py
```
```

---

## Verification & Test Results

The autonomous navigation and target engagement logic was validated against a 12m × 12m maze environment with multi-corridor layouts and hidden heat targets:

```
======================================================================
  AUTOMATED SIMULATION TRIALS: CDE2310 AUTONOMOUS ROBOT
======================================================================
  STATUS: ALL TESTS PASSED (100% SUCCESS)
  - Vectorized Frontier Search: PASSED (0.002s avg)
  - Metric Coordinate Conversion: PASSED
  - Obstacle Blacklist Recovery: PASSED
  - Thermal Alignment & Solenoid Firing: PASSED (2/2 targets neutralized)
  - Final Mapping Coverage: 88.0%
======================================================================
```
