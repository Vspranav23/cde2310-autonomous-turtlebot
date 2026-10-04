# Software

The software runs on ROS 2 Humble and is split across two machines:

- **Raspberry Pi (on the robot):** TurtleBot bringup, the thermal detection node and the frontier explorer, which also triggers the launcher.
- **Laptop:** SLAM Toolbox, the Nav2 stack and RViz.

## How it fits together

```
 AMG8833 ──I2C──> [thermal] ──/thermal_data──┐
                                             v
 LiDAR ──> slam_toolbox ──/map──────────> [explorer] ──NavigateToPose──> Nav2 ──> wheels
 OpenCR ─────────────────────/odom───────────┘    └──GPIO PWM──> L298N ──> launcher cam motor
```

The explorer node runs its decision loop every 2 s:

1. **Heat seen:** if the latest `/thermal_data` message isn't `N`, it follows the heat source:

   | Code | Meaning | Explorer action |
   |---|---|---|
   | `N` | No heat in view (under 5% of pixels above threshold) | Keep exploring frontiers |
   | `L` / `R` | Heat is to the left or right | Rotate 45° toward it |
   | `F<n>` | Heat is ahead, with `n` hot pixels in the centre columns | Drive forward 0.5 m (n ≤ 8), 0.25 m (n ≤ 32) or 0.1 m (n > 32) |
   | `S` | At least 50% of pixels are hot, so the target is in range | Fire the launcher, remember this position, resume exploring |

2. **No heat, not moving:** it picks the nearest unvisited frontier at least 0.3 m away and sends it to Nav2 as a `NavigateToPose` goal. A frontier is a free cell next to unknown space. If Nav2 rejects the goal, that frontier is blacklisted and the explorer picks another.

## Packages

| Package | Path | Executable | What it does |
|---|---|---|---|
| `cde2310` | `workspace/src/cde2310/` | `thermal` | Reads the AMG8833 8×8 grid once a second and publishes the codes above on `/thermal_data`. The `threshold` parameter defaults to 30.0 °C. Set `use_sim:=true`, or run without the sensor, and it republishes whatever arrives on `/sim_thermal_command`. |
| `custom_explorer` | `workspace/src/Autonomous-Explorer-and-Mapper-ros2-nav2/` | `explorer` | Frontier exploration, heat following and firing. Based on [AniArka/Autonomous-Explorer-and-Mapper-ros2-nav2](https://github.com/AniArka/Autonomous-Explorer-and-Mapper-ros2-nav2). Subscribes to `/map`, `/odom` and `/thermal_data`. Set `is_sim:=true` to skip GPIO. |

The Nav2 tuning (costmaps, inflation radius, planner) lives in `workspace/src/cde2310/config/nav2_params.yaml`. That's the file the launch files load. `Software/nav2_params.yaml` is an older copy and is different.

### Launch files (`cde2310/launch/`)

| File | Run on | Starts |
|---|---|---|
| `rpi.py` | Raspberry Pi | TurtleBot3 bringup, then after 10 s the `explorer` and `thermal` nodes |
| `laptop.py` | Laptop | SLAM Toolbox, Nav2 (with the params above) and RViz |
| `full_autonomy_launch.py` | One machine, simulation | SLAM Toolbox, Nav2, `explorer` and `thermal`, all with `use_sim_time:=true` |

## Build and run

```bash
cd Software/workspace
colcon build --symlink-install
source install/setup.bash

# On the Raspberry Pi
ros2 launch cde2310 rpi.py

# On the laptop (same ROS_DOMAIN_ID)
ros2 launch cde2310 laptop.py
```

Dependencies:

- ROS 2 Humble, `turtlebot3_bringup`, `slam_toolbox`, `nav2_bringup`
- `numpy`, `tf_transformations`
- On the Pi only: `RPi.GPIO` and `adafruit-circuitpython-amg88xx`, with I²C enabled

## Standalone scripts

These scripts were used to check one piece of hardware at a time on the Pi. None of them is part of the ROS packages.

| File | Purpose |
|---|---|
| `test_firing.py` | Fires the launcher three times with the competition timing (2 s, then 4 s). It runs the cam motor at 1 kHz PWM, 20% duty, for 5 s per shot, on GPIO 18 (IN1) with GPIO 27 (IN2) held low. |
| `thermal.py` | Prints the raw 8×8 AMG8833 temperature grid every second, to check the sensor works. |
| `tfake_thermal.py` | ROS node that publishes a fixed `N` on `thermal_data`. Use it to test exploration without the sensor. |
| `servo.py` | Sweeps an SG90 servo on GPIO 13. Left over from the servo-gated launcher designs. |
| `launch.py` | Opens Gazebo (TurtleBot3 world) and RViz in separate terminals. |
| `oldNav.py` | First version of the explorer node, before heat following was added. |
| `abandoned/plunger.py` | Solenoid launcher test (abandoned; see `abandoned/README.md`). |

## Simulation test

`tests/test_maze_exploration.py` runs the real `ExplorerNode` frontier logic without ROS. It uses a simulated 12 m × 12 m maze with a ray-cast LiDAR and two heat targets.

```bash
python Software/tests/test_maze_exploration.py   # numpy only
python Software/tests/render_sim_map.py          # + matplotlib, writes docs/sim_map.png
```

The robot jumps straight to each chosen frontier and nothing checks for collisions. So the test checks frontier selection and the thermal-to-fire logic, not navigation.

## Testing results on the robot

| Part | Result |
|---|---|
| Thermal node | Worked. Direction codes were accurate and published reliably. |
| Nav2 with goals set in RViz | Worked. |
| Frontier exploration | Worked. Frontiers were found from the SLAM map and reached. |
| SLAM Toolbox | Worked. Maps were accurate and loop closure kept drift low. |
| Launcher triggered by a fake `S` | Worked through GPIO. |
| **Full integration (thermal + exploration)** | **Failed in the final run.** The thermal node published `N` every second, and each `N` made the explorer call `explore()` again even while it was already navigating. The robot kept picking new frontiers and dropping them, so it only inched forward or jittered. |

The current `check_heat_source()` only calls `explore()` when `is_navigating` is false, which should stop that loop. This fix hasn't been tested on the robot.
