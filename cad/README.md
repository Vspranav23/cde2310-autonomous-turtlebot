# Mechanical

The mechanical payload sits on a TurtleBot3 Burger. It has three parts:

- **Hopper:** a gravity-fed, single-stack hopper that holds the ping-pong balls.
- **Launcher:** a cam-cantilever-spring mechanism that flicks one ball at a time upward.
- **Sensor mount:** a holder at the front of the robot for the AMG8833 thermal camera.

All custom parts were modelled in SolidWorks and 3D printed. The launcher parts are PETG.

## Specifications

| Item | Value |
|---|---|
| Size (L × W × H) | 300 × 221 × 206 mm |
| Weight | 1575 g unladen, 1600 g with 9 balls |
| Ball capacity | 9 (8 in the hopper, 1 in the launcher) |
| Estimated launch height | 1.0–1.5 m |
| Launcher stroke | 14 mm spring extension, 2 mm pre-load |
| Launcher drive | RE-260 DC motor (3.0–4.5 V) + Ta72004 worm gearbox at 336:1 |

## Launcher: cam-cantilever-spring

A lever pivots on a pin in the launcher mount. One end of the lever rests on a custom surface cam and the other end is attached to an extension spring.

1. The geared motor turns the cam.
2. As the cam turns from its lowest to its highest point, it lifts the lever and stretches the spring.
3. When the lever reaches the cam's step, it drops off.
4. The spring snaps the lever back, and the lever strikes the ball upward.

### Design changes made during testing

| Problem | Change |
|---|---|
| The mounting holes broke under a 20 mm stroke. | Reduced the cam step from 10 mm to 8 mm. Added 10 mm of material around the lever and mount pin holes and moved the holes 5 mm further apart vertically. This gave a 14 mm effective stroke. |
| The cam broke along the notch that holds the motor shaft's dowel pin. | Turned the notch perpendicular to the cam step and filleted every edge. |
| The launcher vibrated while the robot was moving. | Added a waffle-pattern support under the base and attached the base plate to the TurtleBot's plate supports. |
| Friction between the lever and the cam stalled the motor. | Greased all moving parts. |
| The printed pivot pin couldn't carry the spring load. | Drilled a 2 mm bore through the pin and inserted a steel spring dowel. Added a spacer between the lever and the mount. |

### Known issue

In the final run the cam could not "slip" past the lever, so the lever never flicked. The camshaft was coupled to the gearbox through a brass hex insert with a half-tightened set screw. Too tight and the cam can't slip; too loose and the gearbox can't turn the cam.

Fixes for a next version:

- **Clutch:** add a proper engage/disengage mechanism between the gearbox and the camshaft.
- **Lever angle:** mount the lever at an acute angle to the base instead of nearly horizontal.
- **Spring position:** centre the spring on the lever so the lever doesn't drift sideways.

## Hopper

- **v1** held two layers of balls. Balls jammed near the opening, and changes to fix that didn't work.
- **v2**, the final version, holds a single layer and is printed in two parts. Rough print surfaces made balls stick, so the high end of the hopper is raised on spacers to steepen the slope. It also has a mount that holds the launcher.

## Sensor mount

The final mount slots into a TurtleBot rivet hole (M4 equivalent). Its slot is deep and narrow enough to hold the AMG8833 firmly. The first version was bolted on, which was hard to reach under the waffle plate, and its slot was too loose for the sensor.

## Assembly

Build a stock TurtleBot3 Burger first, using the [ROBOTIS assembly manual](https://emanual.robotis.com/docs/en/platform/turtlebot3/hardware_setup/). Then:

1. Install the launcher on the hex supports. You may need to remove the top three waffle plates.
2. Install the L298N motor driver on the second waffle plate. Move the OpenCR board if it's in the way.
3. Fasten the two hopper sections and the launcher mount together.
4. Attach the hopper to the spacers, then fix the spacers to the third waffle plate. Spacers 1–4 are different lengths, so check that each one goes in the right place.
5. Fasten the launcher mount to the launcher.
6. Insert the AMG8833 into the sensor mount and fit the mount to the robot.

## Files

| Path | Contents |
|---|---|
| `SolidWorks_source/shooter - lever/lever_v2/` | **Final launcher.** The `shooter_mech.SLDASM` assembly with its cam, lever, pin, spring, mount, body and covers. |
| `SolidWorks_source/shooter - lever/` | Earlier version of the cam launcher. `.stl(2)/` has its print files. |
| `SolidWorks_source/Shooter - Friction Wheel/` | **Final hopper** (`Hopper_v2_part1/2`), `Launcher_mount` and `Spacer1`–`Spacer4`. This folder also holds the friction-wheel launcher concept, which was not built. |
| `SolidWorks_source/Shooter - Friction Wheel/v1 hopper/` | First, double-stack hopper (abandoned). |
| `SolidWorks_source/IR_sensor_holder.SLDPRT` | AMG8833 sensor mount. |
| `SolidWorks_source/Shooter/` | Solenoid launcher prototype (abandoned). |
| `Cannon_2.STL`, `Solenoid_holder.STL`, `Spring_rod_2a.STL`, `plate_2.STL`, `Gate.STL` | Print files for the solenoid prototype (abandoned). |
| `First/Second/Third/Forth Floor.step`, `XM430.step`, `LB-012.step`, `pr30_*`, fasteners | Stock TurtleBot3 Burger parts, used as reference when fitting the payload. |
