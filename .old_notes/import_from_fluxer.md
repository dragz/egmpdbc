# 0x038, 0x039, Ioniq 5
Frame ID 0x038 byte 0 tracks power state with some lag. 0x01=awake but off, 0x04=ready
Frame ID 0x039 byte 0 goes to 0x09 when the car is going up in power state.

Tyler — 7/18/2026, 11:06 AM
0x039 runs at 20Hz when the car is awake and fires with 0x09 on byte 0 4x when going up in power state.

Tyler — 7/19/2026, 5:31 PM
The same byte also has short bursts of 05 or 07, possibly related to wake-ups from opening doors.


# 0x652, EV6
So, I found the info for the setup button!

I don't fully understand this, still learning, but there are 2 frames.1
ID: 0x652, Data: 0xFF 0xFC 0xFF 0xFF 0x07 0x00 0x00 0x00
ID: 0x652, Data: 0xFF 0xFD 0xFF 0xFF 0x07 0x00 0x00 0x00

So, with the two frames. You need to enable the first one and then the second one.

Enabling only the first frame (second byte 0xFC)does nothing.
Enabling only the second frame(second byte 0xFD) only pops up the screen with the SW Info/Update.
Enabling both frames gets you into the main settings menu.

There was another frame, second byte 0xFF, but it didn't seem to do anything.

# 0x652, brute force

brute forced all the 0x652 buttons: (D1 = first byte, D2 = second byte, etc)
652:
D1, 01: media (both?)
D1, 04: start radio (???)
D1, 10: nav (both?)
D1, 40: map (both?)
D2, 01: setup (ev6)
D2, 04: star (both?)
D2, 10: seek right (ev6)
D2, 40: seek left (ev6)
D3, 10: call (???)
D3, 40: home (???)

#  0x652, EV6

Seek left
ID: 0x652
FF 7F FF FF 07 00 00 00
FF 3F FF FF 07 00 00 00

SuaveEV — 7/10/2026, 3:56 PM
Seek Right
ID: 0x652
FF DF FF FF 07 00 00 00
FF CF FF FF 07 00 00 00

# 0x652, EV6

This is the mode switch button, best I can tell, 0x652 only appears on a clean recording once I push the button.

My default I set on my car is to always be on climate, when I push the button, it goes to media, then times back out to climate.

So, 5F to 4F to 7F to FF should be going from climate to Media.

BF to FF should be going from Media to Climate. The head unit beeps, but nothing happens.

FF FF FF 5F 07 00 00 00
FF FF FF 4F 07 00 00 00
FF FF FF 7F 07 00 00 00
FF FF FF FF 07 00 00 00
FF FF FF FF 07 00 00 00
FF FF FF FF 07 00 00 00
FF FF FF BF 07 00 00 00
FF FF FF BF 07 00 00 00
FF FF FF BF 07 00 00 00
FF FF FF FF 07 00 00 00
FF FF FF FF 07 00 00 00
FF FF FF FF 07 00 00 00


# EV6, climate stuff

Climate Stuff:

Driver Only: ID: 0x465 D7: 0x04 to 0x0C is what's important, right?
6C FF 98 00 00 00 04 00
6C FF 98 00 00 00 04 00
6C FF 98 00 00 00 04 00
7C 3D 99 00 00 00 0C 00
7C 3D 99 00 00 00 0C 00
7C 3D 99 00 00 00 0C 00
CA 70 9A 00 00 00 04 00
CA 70 9A 00 00 00 04 00
CA 70 9A 00 00 00 04 00
DA B2 9B 00 00 00 0C 00
DA B2 9B 00 00 00 0C 00
DA B2 9B 00 00 00 0C 00

ok yeah, i'm fairly certain 0x465 only carries data related to a climate button being pressed, and does not actually cause the change to the climate settings

# 0x380, Ioniq 5 

0x380 is temperature status: first three bytes counter, next 4 bytes left/right temp, last byte ???

0x4A0 is sync activation. D4 0B->0F is on. D4 07->0F is off.
0x49f is temperature (up/down!) control, when activated by the head unit. D1 70->F0 is up. D1 B0->F0 is down, D1 E0->F0 is right side down, D1 D0->F0 is right side up. 0x49f also has AC toggle/auto toggle
0x41D is driver only. D5 0D->0F is on, D5 0C->0F is off; heat toggle is also on 41D
i am not sure if 4A0/49F/41D will be the control messages when using the climate bar buttons on EV6 to activate these, but the head unit generates the above messages to control these climate functions

# 0x4A2, Ioniq 5

0x4A2 is heated seat. D5 8->F is high, 7->F is medium, 6->F is low, 2->F is off. high nibble is driver's side, low nibble is passenger's

# 0x4A2, EV6

Can confirm those worked for me! Those must be Ioniq only, because that ID doesn't show when I press the center console buttons.

D5: 5/4/3 are for ventilated high/med/low.

D5: 2 Clears both heat/ventilated

# remote activation signals

Another thing I found on StarPilot, just putting this here. Someone made it so the Comma would power on if it detected the car was turned on remotely.

Tested on a Kia EV9 and 2023 Kia EV6. EV9 remote climate active used 0x384 byte 3 equal to 0x01; EV6 remote climate active used 0x0a. Both stopped/off states observed byte 3 equal to 0x00.

# 360 degree camera

Camera off -> Camera On
ID: 0x476 Data: 0x01 0x00 0x42 0x00 0x00 0x00 0x00 0x03
ID: 0x477 Data: 0x41 0x01 0x20 0x01 0xB3 0x11 0x0C 0x04
ID: 0x477 Data: 0x42 0x01 0x20 0x01 0xB3 0x11 0x0C 0x04
ID: 0x476 Data: 0x01 0x00 0x52 0x00 0x00 0x00 0x00 0x03
ID: 0x477 Data: 0x42 0x3D 0x20 0x01 0xB3 0x11 0x0C 0x04

Camera On -> Camera Off

ID: 0x476 Data: 0x01 0x00 0x52 0x00 0x00 0x00 0x00 0x03
ID: 0x477 Data: 0x42 0x3D 0x20 0x01 0xB3 0x11 0x0C 0x04
ID: 0x476 Data: 0x01 0x00 0x42 0x00 0x00 0x00 0x00 0x03
ID: 0x477 Data: 0x41 0x3D 0x20 0x01 0xB3 0x11 0x0C 0x04

# EV6, many CAN frames

162 (0x0A2) - WHEEL_SPEEDS (Length: 8)
Wheel_Speed_1Start Bit: 0 | Length: 16 | Type: UnsignedFactor: 0.03125 | Offset: 0 | Range: 0 to 2047.96 kphWheel_Speed_2Start Bit: 16 | Length: 16 | Type: UnsignedFactor: 0.03125 | Offset: 0 | Range: 0 to 2047.96 kphWheel_Speed_3Start Bit: 32 | Length: 16 | Type: UnsignedFactor: 0.03125 | Offset: 0 | Range: 0 to 2047.96 kphWheel_Speed_4Start Bit: 48 | Length: 16 | Type: UnsignedFactor: 0.03125 | Offset: 0 | Range: 0 to 2047.96 kph
428 (0x1AC) - CLUSTER_INFO (Length: 8)
Speed_kphStart Bit: 0 | Length: 8 | Type: UnsignedFactor: 1 | Offset: 0 | Range: 0 to 255 kph
550 (0x226) - AMBIENT_TEMPERATURE (Length: 8)
Outdoor_TemperatureStart Bit: 24 | Length: 8 | Type: UnsignedFactor: 1 | Offset: -40 | Range: -40 to 215 C
551 (0x227) - ODOMETER (Length: 8)
OdometerStart Bit: 8 | Length: 24 | Type: UnsignedFactor: 0.1 | Offset: 0 | Range: 0 to 1677721 km
764 (0x2FC) - BATTERY_INFO (Length: 8)
State_Of_ChargeStart Bit: 56 | Length: 8 | Type: UnsignedFactor: 0.5 | Offset: 0 | Range: 0 to 100 %
795 (0x31B) - CLIMATE_STATUS (Length: 8)
• Climate_Fan_Speed
  • Start Bit: 24 | Length: 4 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 15
  • Values: 0: Off, 2-9: Speeds 1 to 8
• Climate_Airflow_Direction
  • Start Bit: 28 | Length: 4 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 15
  • Values: 0: Auto, 1: Body, 2: Body&Legs, 3: Legs, 4: Legs&Defog
• Climate_Recirculation_State
  • Start Bit: 34 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
  • Values: 0: Off, 1: On
896 (0x380) - CLIMATE_TEMPERATURE (Length: 8)
• Driver_Temp_Raw
  • Start Bit: 24 | Length: 8 | Type: Unsigned
  • Factor: 0.5 | Offset: 14 | Range: 14 to 32 C
  • Values: 0: Off
• Passenger_Temp_Raw
  • Start Bit: 32 | Length: 8 | Type: Unsigned
  • Factor: 0.5 | Offset: 14 | Range: 14 to 32 C
  • Values: 0: Off
• Rear_Temp_1_Raw
  • Start Bit: 40 | Length: 8 | Type: Unsigned
  • Factor: 0.5 | Offset: 14 | Range: 14 to 32 C
  • Values: 0: Off
• Rear_Temp_2_Raw
  • Start Bit: 48 | Length: 8 | Type: Unsigned
  • Factor: 0.5 | Offset: 14 | Range: 14 to 32 C
  • Values: 0: Off
938 (0x3AA) - CHARGE_PORT_DOOR (Length: 8)
• Port_Open
  • Start Bit: 33 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
1041 (0x411) - BODY_STATUS (Length: 8)
• Doors_Unlocked
  • Start Bit: 22 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Driver_Door_Open
  • Start Bit: 24 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Passenger_Door_Open
  • Start Bit: 34 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Passenger_Seatbelt_Fastened
  • Start Bit: 36 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Driver_Seatbelt_Fastened
  • Start Bit: 42 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Hood_Open
  • Start Bit: 44 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Rear_Left_Door_Open
  • Start Bit: 52 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Rear_Right_Door_Open
  • Start Bit: 56 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
1042 (0x412) - BRAKE_PEDAL_STATUS (Length: 8)
• Brake_Pedal
  • Start Bit: 48 | Length: 8 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 255
  • Values: 0: Not Pressed, 4: Pressed
1044 (0x414) - TRUNK_STATUS (Length: 8)
• Trunk_Open
  • Start Bit: 24 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
1077 (0x435) - POWER_CAN_STATUS (Length: 8)
• Power_State
  • Start Bit: 56 | Length: 8 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 255
  • Values: 0: Car On, 255: Car Off
1096 (0x448) - STEERING_WHEEL_BUTTONS (Length: 8)
• Steering_Wheel_Speak_Button
  • Start Bit: 16 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Steering_Wheel_Call_Button
  • Start Bit: 18 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Steering_Wheel_Mode_Button
  • Start Bit: 22 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Steering_Wheel_Mute_Button
  • Start Bit: 24 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Steering_Wheel_Skip_Down_Button
  • Start Bit: 26 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Steering_Wheel_Skip_Up_Button
  • Start Bit: 28 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Steering_Wheel_Vol_Down_Button
  • Start Bit: 30 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Steering_Wheel_Vol_Up_Button
  • Start Bit: 32 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Steering_Wheel_Star_Button
  • Start Bit: 44 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Steering_Wheel_Menu_Down_Button
  • Start Bit: 48 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Steering_Wheel_Menu_Up_Button
  • Start Bit: 50 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
• Steering_Wheel_Menu_Press_Button
  • Start Bit: 52 | Length: 1 | Type: Unsigned
  • Factor: 1 | Offset: 0 | Range: 0 to 1
**1141 (`0x475`) - PASSENGER_SEAT_HEATING (Length: 8)**
- `Passenger_Seat_Heating_State`
  - Start Bit: 0 | Length: 8 | Type: Unsigned
  - Factor: 1 | Offset: 0 | Range: 0 to 255
  - Values: 18: Off, 50: Low, 58: Medium, 66: High

**1174 (`0x496`) - DRIVER_SEAT_HEATING (Length: 8)**
- `Driver_Seat_Heating_State`
  - Start Bit: 0 | Length: 8 | Type: Unsigned
  - Factor: 1 | Offset: 0 | Range: 0 to 255
  - Values: 18: Off, 50: Low, 58: Medium, 66: High

**782 (`0x30E`) - CHARGING_POWER (Length: 8)**
- `Charging_Power_kW`
  - Start Bit: 48 | Length: 8 | Type: Unsigned
  - Factor: 1 | Offset: 0 | Range: 0 to 255 kW

# EV6, cabin temperature

0x2CF does climate temp up/down

Driver Up
0F 01 FF 00 00 00 00 00 x3
1F 01 FF 00 00 00 00 00 x3
2F 01 FF 00 00 00 00 00 x3
Driver Down
0F 80 FF 00 00 00 00 00 x3
1F 80 FF 00 00 00 00 00 x3
2F 80 FF 00 00 00 00 00 x3

Passenger Up
0F FF 01 00 00 00 00 00 x3
1F FF 01 00 00 00 00 00 x3
2F FF 01 00 00 00 00 00 x3
Passenger Down
0F FF 80 00 00 00 00 00 x3
1F FF 80 00 00 00 00 00 x3
2F FF 80 00 00 00 00 00 x3

SuaveEV — 8/6/2026, 3:39 PM
Let me clarify, D1 needs to cycle for it to do another step up/down, otherwise it'll stay on the same temp.

SuaveEV — 8/6/2026, 4:17 PM
This is UI only for Driver temp, didn't get a chance to check passenger.

0x380

49 15 3B 06 06 06 06 01 // 62°F
90 2F 3C 07 07 06 06 01 // 63°F
A9 27 3D 08 08 06 06 01 // 64°F
1D 12 3E 09 09 06 06 01 // 65°F
AC 43 3F 0A 0A 06 06 01 // 66°F
A3 D7 40 0B 0B 06 06 01 // 67°F
75 41 41 0C 0C 06 06 01 // 68°F
C1 74 42 0D 0D 06 06 01 // 69°F
70 25 43 0E 0E 06 06 01 // 70°F
A9 1F 44 0F 0F 06 06 01 // 71°F
6F 3A 45 10 10 06 06 01 // 72°F
DB 0F 46 11 11 06 06 01 // 73°F
6A 5E 47 12 12 06 06 01 // 74°F
69 7A 48 13 13 06 06 01 // 75°F
BF EC 49 14 14 06 06 01 // 76°F
0B D9 4A 15 15 06 06 01 // 77°F
BA 88 4B 16 16 06 06 01 // 78°F
63 B2 4C 17 17 06 06 01 // 79°F
5A BA 4D 18 18 06 06 01 // 80°F
EE 8F 4E 19 19 06 06 01 // 81°F
5F DE 4F 1A 1A 06 06 01 // 82°F

# EV6, charge limits

Max Charge Percentage
ID: 0x4C5

DC Charge:
50%: D6 64->FF
60%: D6 78->FF
70%: D6 8C->FF
80%: D6 A0->FF
90%: D6 B4->FF
100%: D6 C8->FF

AC Charge:
50%: D5 64->FF
60%: D5 78->FF
70%: D5 8C->FF
80%: D5 A0->FF
90%: D5 B4->FF
100%: D5 C8->FF

# EV6, active sound design

Active Sound Design
ID: 0x658

Largest Change: D2 FD->FF
Moderate Change: D1 FD->FF & D2 FD->FF
Smallest Change: D2 FC->FF
Off: D1 7F->FF & D2 FC->FF

Sound Style:
Stylish: D1 87->FF
Dynamic: D1 8B->FF
Cyber: D1 8F->FF
Custom: D1 FB->FF

--Custom Settings--

Sound Style:
Stylish: D2 87->FF
Dynamic: D2 8B->FF
Cyber: D2 8F->FF

Response:
Slow: D3 9F->FF
Normal: D3 AF->FF
Fast: D3 BF->FF

Master Vol 0-20:
0: D2 7F->FF & D3 F0->FF
1: D3 F0->FF
2: D2 7F->FF & D3 F1->FF
3: D3 F1->FF
4: D2 7F->FF & D3 F2->FF
5: D3 F2->FF
6: D2 7F->FF & D3 F3->FF
7: D3 F3->FF
8: D2 7F->FF & D3 F4->FF
9: D3 F4->FF
10: D2 7F->FF & D3 F5->FF
11: D3 F5->FF
12: D2 7F->FF & D3 F6->FF
13: D3 F6->FF
14: D2 7F->FF & D3 F7->FF
15: D3 F7->FF
16: D2 7F->FF & D3 F8->FF
17: D3 F8->FF
18: D2 7F->FF & D3 F9->FF
19: D3 F9->FF
20: D2 7F->FF & D3 FA->FF

# EV6, 0x442

0x442 Sunroof (Status?) D6/D7

30 30 = Cover Closed
30 50 = Cover Moving
30 60 = Cover Opened

10 60 = Glass Closed/Transition
50 60 = Glass Sliding
60 60 = Glass Opened

10 50 = Glass Closing
00 60 = Glass Tilted or Windbreak
10 60 = Glass Tilting

# EV6, 0x4F2

Display Brightness
ID: 0x4F2, 91 different values
D7 & D8 are the values.
D7 was alternating 00 & 80.
Range:
00 19 -> 00 FA

# EV6, 0x474

Cluster/Dash Brightness Button
ID: 0x474, D8
Idle:    0A
Up:      4A
Down: 8A



