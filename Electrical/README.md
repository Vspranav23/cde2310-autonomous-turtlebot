# Electrical

The electrical payload adds three things to the stock TurtleBot3 Burger:

- an **AMG8833 thermal camera** for finding heat sources
- an **L298N motor driver** that runs the launcher's cam motor
- a **custom PCB hat** on the Raspberry Pi that connects them

Everything runs on the TurtleBot's battery. The PCB takes its power from the OpenCR board's 5 V output.

## System overview

```
3S LiPo (11.1 V, 1800 mAh) ──> OpenCR ──5 V──> PCB hat ──> Raspberry Pi 4 (GPIO header)
                                                  ├──I2C──> AMG8833 thermal camera
                                                  └──GPIO─> L298N motor driver ──> RE-260 motor + gearbox (launcher cam)
```

| Signal | Raspberry Pi pin (BCM) | Used by |
|---|---|---|
| AMG8833 SDA / SCL | GPIO 2 / GPIO 3 (I²C-1, address 0x69) | `thermal` node |
| L298N IN1 (PWM, 1 kHz) | GPIO 18 | `startFiring()` in the explorer node, `Software/test_firing.py` |
| L298N IN2 (held low) | GPIO 27 | same |
| Set HIGH at startup | GPIO 17 | explorer node (presumably the L298N enable pin) |

The L298N was added late in the project (week 12), after the solenoid design was dropped. It isn't on the PCB, so it's wired to the Pi header with jumper wires.

## Specifications

| Item | Value |
|---|---|
| Battery | 3S1P LiPo, 11.1 V nominal, 1800 mAh (19.98 Wh) |
| TurtleBot power draw | 6.7 W idle; 10.7 W at max speed (11.3 W peak) |
| Launcher motor + L298N | about 5 W (5.5 W peak) |
| Estimated run time | 0.6–1.0 h (mission length is 25 min) |
| AMG8833 | 8×8 IR array, 60° field of view, 0–80 °C range, ±2.5 °C accuracy, 3–5 V supply |
| L298N | 5–35 V motor supply, 20 W max |
| PCB hat | 5 V input, max 4 A (limited by the OpenCR's 5 V output), 71 × 56 × 31 mm, 30 g |

## The onboard Raspberry Pi PCB

The PCB hat was designed with a lot of help from Mr. Eugene to make the wiring tidier and more reliable.

- **Connections:** it passes through the Pi's GPIO and I²C pins. Pin 24 (GPIO 8) is the exception (see Known issues).
- **MOSFET outputs:** two IRL3803 MOSFETs switch the `5VSOLENOID` and `12VSOLENOID` headers. These were for the solenoid launcher, which was abandoned. The final launcher doesn't use them.
- **Manufacture:** five boards were ordered from JLCPCB, which ran a flying-probe electrical test on them. One was assembled in-house at the E2 Electronics Lab.
- **Testing:** the assembled board was checked with a 5 V supply and a 3.3 V signal to confirm a Pi GPIO pin can switch the MOSFETs. It was then integrated with a backup Raspberry Pi to confirm AMG8833 data can be read through it.

### Known issues

1. **Pin 24 (GPIO 8) is not soldered.** A via sits too close to it and could short.
2. **Hard-to-reach pins:** the design didn't allow for the gap between the TurtleBot waffle plates. M3×10 mm hex extenders on the M3×45 mm supports give more room.
3. **Header doesn't fully seat:** the Pi's Ethernet port is in the way, so the header can't press all the way down. The back of the board is taped over so the port's metal casing can't short the pins.
4. **No mechanical fastening:** the board can work loose when the robot vibrates.
5. **Exposed wiring:** the L298N is not on the PCB, so its jumper wires are left exposed.

For a next version: plan for the space between the waffle plates and the Ethernet port, screw the board down, and put the motor driver on the PCB.

### Schematics
![image](https://github.com/user-attachments/assets/fc26c7e2-d6d2-4aa7-8678-e5d6c1d73ada)

### Bill of materials

<table>
<tr><td><b>Qty</b></td><td><b>Value</b></td><td><b>Device</b></td><td><b>Footprint Name</b></td><td><b>Parts</b></td><td><b>Detailed Description</b></td><td><b>CATEGORY</b></td><td><b>CREATED_BY</b></td><td><b>DATASHEET</b></td><td><b>DESCRIPTION</b></td><td><b>DIGIKEY_PART_NUMBER</b></td><td><b>DIGI_KEY_PART_NUMBER</b></td><td><b>DRAIN_CURRENT</b></td><td><b>IC_MAX</b></td><td><b>MANUFACTURER</b></td><td><b>MPN</b></td><td><b>OPERATING_TEMPERATURE</b></td><td><b>PACKAGE_SIZE</b></td><td><b>PACKAGE_TYPE</b></td><td><b>PART_STATUS</b></td><td><b>PITCH</b></td><td><b>POPULARITY</b></td><td><b>ROHS</b></td><td><b>SERIES</b></td><td><b>SUBCATEGORY</b></td><td><b>TEMPERATURE_COEFFICIENT</b></td><td><b>THERMALLOSS</b></td><td><b>TOLERANCE</b></td><td><b>TYPE</b></td><td><b>VCEO_MAX</b></td></tr>
<tr><td>2</td><td>10k</td><td>R_AXIAL-7.2MM-PITCH</td><td>RESAD724W46L381D178B</td><td>R6, R8</td><td>Resistor Fixed - Generic</td><td>Resistors</td><td></td><td></td><td>Axial Resistor 7.24 mm pitch 3.81 mm body length 1.78 mm body diameter</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>AXIAL</td><td>THT</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td>2</td><td>1N4148DO35-10</td><td>1N4148DO35-10</td><td>DO35-10</td><td>D3, D4</td><td>DIODE</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>21</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td>2</td><td>1k</td><td>R_AXIAL-7.2MM-PITCH</td><td>RESAD724W46L381D178B</td><td>R5, R7</td><td>Resistor Fixed - Generic</td><td>Resistors</td><td></td><td></td><td>Axial Resistor 7.24 mm pitch 3.81 mm body length 1.78 mm body diameter</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>AXIAL</td><td>THT</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td>1</td><td>2828XX-4282834-4</td><td>2828XX-4282834-4</td><td>TERMBLK_254-4N</td><td>5V,12VTERBLK</td><td>4 Position Wire to Board Terminal Block Horizontal with Board</td><td>Fixed Terminal Blocks</td><td></td><td>https://www.te.com/usa-en/product-282834-4.datasheet.pdf</td><td>4 Position Wire to Board Terminal Block Horizontal with Board 0.100" (2.54mm) Through Hole</td><td></td><td></td><td></td><td></td><td>TE Connectivity AMP Connectors</td><td>282834-4</td><td>-40�C ~ 105�C</td><td>NA</td><td>THT</td><td>ACTIVE</td><td>0.100" (2.54mm) </td><td></td><td>COMPLIANT</td><td>Buchanan</td><td>Terminal Blocks</td><td></td><td></td><td></td><td>Through Hole Screw - Rising Cage Clamp Side wire entry Horizontal with Board</td><td></td></tr>
<tr><td>2</td><td>61300211121</td><td>61300211121</td><td>61300211121</td><td>5VSOLENOID, 12VSOLENOID</td><td>CONN HEADER VERT 2POS 2.54MM</td><td></td><td>PCBLayout.com</td><td></td><td></td><td></td><td>732-5315-ND</td><td></td><td></td><td>Wurth Electronics Inc.</td><td>61300211121</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td>1</td><td>61300311121</td><td>61300311121</td><td>61300311121</td><td>SERVO</td><td>CONN HEADER VERT 3POS 2.54MM</td><td></td><td>PCBLayout.com</td><td></td><td></td><td></td><td>732-5316-ND</td><td></td><td></td><td>Wurth Electronics Inc.</td><td>61300311121</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td>1</td><td>61300511121</td><td>61300511121</td><td>61300511121</td><td>AMG8833</td><td>CONN HEADER VERT 5POS 2.54MM</td><td></td><td>PCBLayout.com</td><td></td><td></td><td></td><td>732-5318-ND</td><td></td><td></td><td>Wurth Electronics Inc.</td><td>61300511121</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td>2</td><td>61302011121</td><td>61302011121</td><td>61302011121</td><td>GPIO_EVEN, GPIO_ODD</td><td>CONN HEADER VERT 20POS 2.54MM</td><td></td><td>PCBLayout.com</td><td></td><td></td><td>732-5329-ND</td><td></td><td></td><td></td><td>Wurth Electronics Inc.</td><td>61302011121</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td>2</td><td>NMOSFET_TO220</td><td>NMOSFET_TO220</td><td>TO220BV</td><td>Q1, Q2</td><td>N-Channel MOSFET - Generic</td><td>Transistor</td><td></td><td>https://www.diodes.com/assets/Package-Files/TO220-3.pdf</td><td>Generic N Channel MOSFET TO220 Package Through Hole</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>TO220</td><td>THT</td><td></td><td></td><td></td><td></td><td></td><td>MOSFET</td><td></td><td></td><td></td><td>N-Channel</td><td></td></tr>
<tr><td>1</td><td>PINHD-1X2/90</td><td>PINHD-1X2/90</td><td>1X02/90</td><td>JP1</td><td>PIN HEADER</td><td>Headers</td><td></td><td></td><td>Header-Right Angle-2 Position</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>THT</td><td></td><td>0.100" (2.54mm)</td><td></td><td></td><td></td><td>Headers-Male Pins</td><td></td><td></td><td></td><td>Board to Board or Cable-Unshrouded-Through Hole-Right Angle</td><td></td></tr>
</table>

You may also need a female 2×20 header with 2.54 mm pitch to connect the PCB to the Raspberry Pi.

### 3D model
![image](https://github.com/user-attachments/assets/a2e77d31-ac5e-45ef-9e9c-d4dd6226e882)

![image](https://github.com/user-attachments/assets/377173ea-6520-4430-87da-c48feaca628f)

> [!NOTE]
> The Gerber files are in [`PCB schematic v36_2025-03-21.zip`](PCB%20schematic%20v36_2025-03-21.zip).

## Datasheets

- [Panasonic AMG8833 datasheet](panasonic%20AMG8833%20datasheet.pdf)
- [Adafruit AMG8833 application note](Adafruit%20AMG8833%20Application%20note.pdf)
- [L298N motor driver datasheet](https://components101.com/sites/default/files/component_datasheet/L298N-Motor-Driver-Datasheet.pdf)
