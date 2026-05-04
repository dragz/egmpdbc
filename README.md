# egmpdbc

Reverse-engineered DBC (CAN database) files for the **E-GMP (Electric-Global Modular Platform)** used by Hyundai Motor Group electric vehicles.

## Supported Vehicles

These DBC files cover the following E-GMP platform vehicles:

| Model | Code | Years |
|-------|------|-------|
| Hyundai IONIQ 5 | NE | 2021+ |
| Hyundai IONIQ 6 | CE | 2023+ |
| KIA EV6 | CV | 2022+ |
| KIA EV9 | MV | 2024+ |
| Genesis GV60 | JW | 2022+ |
| Genesis GV70 EV | JK EV | 2023+ |
| Genesis GV80 Coupe EV | JX EV | 2024+ |

## CAN Bus Architecture

E-GMP vehicles use multiple CAN buses operating at different speeds:

| Bus | Speed | Description |
|-----|-------|-------------|
| C-CAN | 500 kbps | Chassis: ABS/ESC, MDPS, airbag |
| P-CAN | 500 kbps | Powertrain: BMS, inverter, VCU |
| M-CAN | 125 kbps | Body: BCM, lights, doors |
| A-CAN | CAN FD | ADAS: cameras, radar, LiDAR |
| E-CAN | 500 kbps | EV/Charging: OBC, ICCU, HVAC |

## DBC Files

### `egmp_bms.dbc` – Battery Management System

Contains signals for battery pack monitoring and control:

| Message | ID (dec) | Description |
|---------|----------|-------------|
| BMS_01 | 1264 (0x4F0) | BMS status, power limits, SOH |
| BMS_02 | 1266 (0x4F2) | Pack voltage, current, SOC, temperatures |
| BMS_03 | 1268 (0x4F4) | Cell voltage min/max/avg |
| BMS_04 | 1270 (0x4F6) | Thermal status, relay states, isolation |
| BMS_05 | 1272 (0x4F8) | Cumulative charge/discharge energy |
| BMS_06 | 1274 (0x4FA) | Available energy and capacity |
| BMS_07 | 1320 (0x528) | Individual cell voltages |
| BMS_08 | 1322 (0x52A) | Module temperatures |

Key signals:
- `BMS_SOC` – State of Charge (0–100%)
- `BMS_SOH` – State of Health (0–100%)
- `BMS_PackVoltage` – HV pack voltage (up to 800V)
- `BMS_PackCurrent` – Pack current (positive=discharge)
- `BMS_MaxCellVoltage` / `BMS_MinCellVoltage` – Cell voltage spread
- `BMS_MaxCellTemp` / `BMS_MinCellTemp` – Thermal window

### `egmp_vcu.dbc` – Vehicle Control Unit & Motors

Contains signals for powertrain control and motor status:

| Message | ID (dec) | Description |
|---------|----------|-------------|
| MOTOR_FRONT_01 | 512 (0x200) | Front motor speed, torque, temperatures |
| MOTOR_FRONT_02 | 514 (0x202) | Front motor power and electrical data |
| MOTOR_REAR_01 | 544 (0x220) | Rear motor (AWD models only) |
| MOTOR_REAR_02 | 546 (0x222) | Rear motor power (AWD models only) |
| VCU_01 | 576 (0x240) | Drive mode, pedals, gear, flags |
| VCU_02 | 578 (0x242) | Vehicle speed, odometer, trip |
| VCU_03 | 580 (0x244) | Torque split and power demand |
| VCU_04 | 582 (0x246) | Estimated range, aux consumption |

Key signals:
- `MOTOR_FR_Speed` / `MOTOR_RR_Speed` – Motor RPM (±32767)
- `MOTOR_FR_Torque` / `MOTOR_RR_Torque` – Motor torque in Nm
- `VCU_DriveMode` – Eco/Normal/Sport/Sport+/Snow/Sand/Mud/N
- `VCU_GearPosition` – P/R/N/D
- `VCU_AcceleratorPedal` / `VCU_BrakePedal` – Pedal positions
- `VCU_EstimatedRange` – Remaining range in km

### `egmp_obc.dbc` – On-Board Charger & Charging

Contains signals for all charging modes (AC, DC fast charge, V2L, V2H):

| Message | ID (dec) | Description |
|---------|----------|-------------|
| OBC_01 | 1440 (0x5A0) | AC charger status, input/output measurements |
| OBC_02 | 1442 (0x5A2) | AC charge power, cumulative energy, temperature |
| OBC_03 | 1444 (0x5A4) | Session info, target SOC, V2L output |
| DCFC_01 | 1446 (0x5A6) | DC fast charge input/output measurements |
| DCFC_02 | 1448 (0x5A8) | DC fast charge status, protocol, pilot |
| ICCU_01 | 1450 (0x5AA) | 12V battery and LDC (DC-DC converter) status |

Key signals:
- `OBC_ChargeStatus` – Charging session state machine
- `OBC_ACInputVoltage` – Grid voltage (120/230/400V)
- `OBC_ChargePower` – Instantaneous charge power in kW
- `DCFC_InputVoltage` – 800V architecture DC input
- `OBC_V2L_OutputVoltage` – Vehicle-to-Load (3.6 kW built-in)
- `ICCU_12VBattVoltage` – 12V auxiliary battery health

### `egmp_chassis.dbc` – Chassis & Dynamics

Contains signals for chassis control systems:

| Message | ID (dec) | Description |
|---------|----------|-------------|
| WHEEL_SPEEDS | 160 (0xA0) | Individual wheel speed sensors |
| WHEEL_SPEEDS_FLAGS | 162 (0xA2) | Validity flags, ABS/TCS/ESC status |
| ACCELERATION | 176 (0xB0) | IMU acceleration and yaw rate |
| STEERING | 688 (0x2B0) | Steering angle, rate, MDPS torque |
| BRAKE_01 | 901 (0x385) | Brake pressures, pedal position, regen portion |
| ESC_STATUS | 903 (0x387) | ESC comprehensive status and speed |

Key signals:
- `WHL_SpdFL/FR/RL/RR` – Four-wheel speed sensors (kph)
- `SteeringAngle` – ±3276.7° with 0.1° resolution
- `LongAcceleration` / `LatAcceleration` / `YawRate` – IMU data
- `RegenerativeBrakePortion` – Regen vs friction brake blend
- `ESC_Active` / `ABS_Active` / `TCS_Active` – Safety system status

## Disclaimer

These DBC files are based on **community reverse engineering** and may not be complete or fully accurate. Signal scaling, offsets, and enumerations have been derived from:
- Analysis of captured CAN bus traffic
- Cross-referencing with publicly available OBD-II PIDs for Hyundai/KIA EVs
- Community contributions from EV enthusiasts and developers

**Always verify signals against your vehicle's actual CAN traffic before relying on this data for any safety-critical applications.**

## Contributing

Contributions are welcome! If you have:
- Captured CAN logs from E-GMP vehicles
- Corrections to existing signal definitions
- New signals not yet documented

Please open an issue or submit a pull request with supporting evidence (CAN captures, OBD-II validation, etc.).

## Related Projects

- [commaai/opendbc](https://github.com/commaai/opendbc) – Open DBC database (ADAS signals for E-GMP)
- [JejuSoul/OBD-PIDs-for-HKMC-EVs](https://github.com/JejuSoul/OBD-PIDs-for-HKMC-EVs) – OBD-II PIDs for Hyundai/KIA EVs
- [dalathegreat/Battery-Emulator](https://github.com/dalathegreat/Battery-Emulator) – Battery reuse with BMS emulation
- [Esprit1st/Hyundai-Ioniq-5-Torque-Pro-PIDs](https://github.com/Esprit1st/Hyundai-Ioniq-5-Torque-Pro-PIDs) – Torque Pro PIDs for IONIQ 5

## License

This collection is provided under the [MIT License](LICENSE). All signal definitions are the result of independent reverse engineering and do not contain any proprietary information from Hyundai Motor Group.
