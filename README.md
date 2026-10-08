# egmpdbc
DBC files for the E-GMP platform (Hyundai/KIA).

## Naming scheme

We name files by car model and a single year based on the most-tested car. It's unlikely that CAN signals change within a model year group before a refresh. There are also many commonalities between cars, and we haven't done a great job of validating these commonalities, so it's worth trying other cars' DBC files if you're looking for a new signal.

**WARNING** Meddling with your canbus can harm your car or void your warranty!

# Branches

We maintain `main` and `testing` branches. `main` is well-validated signals, while testing is bleeding-edge reverse engineering that may contain wild misinterpretations. At the moment, we don't have a validation pipeline, so `testing` is far ahead of `main`.

## 11-bit to 29-bit ID translation for CCU cars

Ioniq 5 and EV6 CAN frame IDs are strictly 11-bit. Cars with a CCU (Ioniq 6, GV60 and later) have 29-bit IDs, and there appears to be a translation scheme between them.  This scheme was worked out by a large language model (DeepSeek V4.1 Flash, an open-weight model that can be run locally when hardware isn't so expensive), so the remaining description is still heavily sloppy.

11-bit frames are re-addressed onto **29-bit extended IDs
that encode the original 11-bit id**. The encoding is exact; it was recovered
from an Ioniq 6 capture and verified against byte-identical payloads in the
Ioniq 5 and GV60 logs.

This is an **ICU CAN hub -> CCU CAN hub** change, not a ccNC head-unit
feature: it predates ccNC head units.

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

Verified on **129 extended ids with 0 mismatches** (85 in the GV60 captures,
44 in the Ioniq 6 capture). The Oct 2026 `Battery conditioning test.csv`
capture adds **192 more extended ids in 71 families**, again with 0 mismatches
and with every family's indices contiguous from 1.

| family base | `0x035` | `0x08E` | `0x0A0` | `0x10A` | `0x1BA` | `0x1E5` | `0x20A` | `0x250` |
|---|---|---|---|---|---|---|---|---|
| prefix | `0x00C` | `0x020` | `0x028` | `0x040` | `0x06C` | `0x078` | `0x080` | `0x094` |

| family base | `0x287`/`0x288` | `0x2AA` | `0x2B5` | `0x2C0` | `0x2E0` | `0x37F` | `0x395` |
|---|---|---|---|---|---|---|---|
| prefix | `0x0A0` | `0x0A8` | `0x0AC` | `0x0B0` | `0x0B8` | `0x0DC` | `0x0E4` |

| family base | `0x150` | `0x2FA` |
|---|---|---|
| prefix | `0x054` | `0x0BC` |

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
| `0x05415002` | `0x152` | `07 07 07 00 2E 00 00 00` (parked, 7 C) | `0E 0E 0E 00 00 00 34 6C` (14 C, byte 1 climbs to `0x11`) |
| `0x0BC2FA02` | `0x2FC` | `00 00 08 0A 00 00 8F 9D` (78.5 % SOC) | `03 00 0E 0E 00 00 8F C6` (99.0 % SOC) |

`0x00C03503` is the neat one to sanity-check by eye: it is `Power_Status`
(11-bit `0x038`), and byte 0's low nibble reads `0x04` = READY on the Ioniq 5
against `0x01` = awake-but-off on the Ioniq 6 capture.

The last two rows are the ones that are *not* byte-identical, and they are why
they are worth stating explicitly: `0x05415002` matches `0x152` only in bytes
0-2 (the three cell temperatures; its tail is `00 00 00 34 6C` here against a
non-zero byte 4 and zero bytes 6/7 on the Ioniq 5), and `0x0BC2FA02` matches
`0x2FC` in shape with byte 7 being the 0.5-scaled state of charge (byte 6 is
`0x8F` in both). Both are decoded in `ioniq6-2023-2025.dbc` as
`Battery_Temperature_Ioniq6` and `Battery_Info_Ioniq6`.

### Media ISO-TP (head-unit bus, not part of the remap)

Track text does **not** use the extended-id scheme — the head-unit bus keeps
plain 11-bit ids. On the Ioniq 6 the verified pair is **`0x6D6` (first /
consecutive frames) with flow control on `0x6B6`**, carrying bare UTF-16LE
after the 2-byte ISO-TP header: `Switching songs.csv` decodes to
`stream of silllver` and `Battery conditioning test.csv` to `Who's That`, both
with `0x4CE` byte 0 = `0xDC` (Apple CarPlay). The same id pair is what
`wicant-i-precondition`'s `track_popup.c` already uses for CarPlay. Its Apps /
Sounds-of-Nature pair (`0x6E0` / `0x6BE`) is *not* confirmed by any capture:
`0x6E0` is never transmitted, and `0x6BE` appears exactly once as a lone flow
control frame (`30 00 03`) while `0x4CE` byte 0 = `0x14` (media off), i.e. the
fallback path that pins the media type to `0x04`. See `BO_ 1750` /
`BO_ 1718` and the media `CM_` notes in `ioniq6-2023-2025.dbc`.

### Consequences

- The 11-bit ids themselves are preserved, so `0x152` (`BMS_10_100ms_2`,
  family base `0x150`, index 2) becomes **`0x05415002`** — confirmed by the
  Oct 2026 `Battery conditioning test.csv` capture, which transmits the whole
  `0x151..0x154` family at a steady 1.66 Hz. The earlier "no frame with family
  base `0x150` is transmitted" result reflected only the awake-not-READY
  capture used at the time, in which the Ioniq 5 also stops sending `0x152`
  (`panda/I-CAN_nothing_on.csv`); a conditioning/READY capture is what settles
  it.
- Likewise `0x2FC` (`Battery_Info`) becomes **`0x0BC2FA02`**, byte 7 times 0.5
  = state of charge (99.0 % = `0xC6` in the stationary Ioniq 6 captures).
- Ioniq 6 frames therefore appear under **two** forms: 11-bit for what stayed
  on the old numbering and 29-bit for the remapped set. Seeing a familiar
  11-bit id in an Ioniq 6 log does *not* mean the car kept the old frame plan —
  and it does not mean the remap is missing either. The bus carries both
  11-bit `0x2FB` (a *different*, constant frame: `00 04 61 F0 00 00 00 00`)
  and the real remap `0x0BC2FA01` at the same time.

