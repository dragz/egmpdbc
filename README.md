# egmpdbc
DBC files for the E-GMP platform (Hyundai/KIA)

**WARNING** Meddling with your canbus can harm your car or void your warranty!

## The 29-bit extended ID scheme (2023+ ccNC cars: Ioniq 6, GV60, ...)

The classic 11-bit car-bus frames are re-addressed onto **29-bit extended IDs
that encode the original 11-bit id**. The encoding is exact; it was recovered
from an Ioniq 6 capture and verified against byte-identical payloads in the
Ioniq 5 and GV60 logs.

```
prefix = 4 * (base >> 4)
ext    = (prefix << 20) | (base << 8) | index

base   = min(id11 of the family) - 1     # the family base
index  = 1..N within the family
id11   = base + index
```

Decoding an extended id seen on the bus:

```python
prefix = (ext >> 20) & 0xFFF
base   = (ext >>  8) & 0xFFF
index  =  ext        & 0xFF
id11   = base + index          # if index == 0 the frame is not a remap
```

Worked example — `BMS_Precond_Status` is 11-bit `0x2AD` (family
`0x2AB..0x2AE`, base `0x2AA`, index 3):

```
prefix = 4 * (0x2AA >> 4) = 4 * 42 = 168 = 0x0A8
ext    = (0x0A8 << 20) | (0x2AA << 8) | 3 = 0x0A82AA03
```

which is the `BMS_Precond_Status_Ioniq6` already recorded in
`ioniq6-2023-2025.dbc` (`BO_ 2323819011` = bit31 | `0x0A82AA03`). **DBC
convention for these frames: `BO_` = 0x80000000 | the 29-bit id.**

### Prefix table — `prefix == 4 * (base >> 4)` holds for every family seen

| family base | `0x035` | `0x08E` | `0x0A0` | `0x10A` | `0x1BA` | `0x1E5` | `0x20A` | `0x250` |
|---|---|---|---|---|---|---|---|---|
| prefix | `0x00C` | `0x020` | `0x028` | `0x040` | `0x06C` | `0x078` | `0x080` | `0x094` |

| family base | `0x287`/`0x288` | `0x2AA` | `0x2B5` | `0x2C0` | `0x2E0` | `0x37F` | `0x395` |
|---|---|---|---|---|---|---|---|
| prefix | `0x0A0` | `0x0A8` | `0x0AC` | `0x0B0` | `0x0B8` | `0x0DC` | `0x0E4` |

### Verified equivalents (Ioniq 6 ext id vs Ioniq 5 11-bit payload)

| ext (Ioniq 6) | 11-bit | Ioniq 5 payload | Ioniq 6 payload |
|---|---|---|---|
| `0x00C03502` | `0x037` | `00 00 00 10 00 40 00 00` | identical |
| `0x00C03503` | `0x038` | `04 00 00 00 60 39 96 D4` (READY) | `01 00 00 00 00 00 06 00` (awake) |
| `0x0280A002` | `0x0A2` | `00 00 00 00 00 00 00 00` | identical |
| `0x04010A02` | `0x10C` | `FF F9 E7 1F 32 2F 31 31` | `FF 01 00 00 3A 39 39 39` |
| `0x0A82AA02` | `0x2AC` | `00 FF FF 00 00 40 00 50` | identical |
| `0x0A82AA03` | `0x2AD` | `00 01 00 40 FF FF FF 0F` | identical (byte 1 = state) |
| `0x0B82E002` | `0x2E2` | `00 00 00 00 00 7E 00 00` | `00 00 00 00 00 7E 00 04` |
| `0x0B82E003` | `0x2E3` | `00 00 00 00 00 00 72 01` | identical |
| `0x0B82E004` | `0x2E4` | `0F 00 00 00 00 00 00 00` | identical |
| `0x0E439502` | `0x397` | `1C 00 00 00 00 00 00 00` | identical |
| `0x0E439503` | `0x398` | `00 00 00 00 00 00 00 00` | identical |

`0x00C03503` is the neat one to sanity-check by eye: it is `Power_Status`
(11-bit `0x038`), and byte 0's low nibble reads `0x04` = READY on the Ioniq 5
against `0x01` = awake-but-off on the Ioniq 6 capture.

### Consequences

- Only the **car bus** of the ccNC cars uses this scheme; the head-unit bus
  keeps plain 11-bit ids.
- The 11-bit ids themselves are preserved, so `0x152` (`BMS_10_100ms_2`,
  family base `0x150`, index 2) becomes **`0x05415002`**. That id is *not*
  transmitted in the short Ioniq 6 capture in
  `../Ioniq5_CAN/CAN_logs/other_cars/Ioniq 6.csv` — the whole `0x150` family is
  absent there, so a capture with the car READY is needed to confirm it on the
  wire.
- Ioniq 6 frames therefore appear under **two** forms: 11-bit for what stayed
  on the old numbering and 29-bit for the remapped set. Seeing a familiar
  11-bit id in an Ioniq 6 log does *not* mean the car kept the old frame plan.

