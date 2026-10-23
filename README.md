# egmpdbc
DBC files for the E-GMP platform (Hyundai/KIA).

## Naming scheme

We name files by car model and a single year based on the most-tested car. It's unlikely that CAN signals change within a model year group before a refresh. There are also many commonalities between cars, and we haven't done a great job of validating these commonalities, so it's worth trying other cars' DBC files if you're looking for a new signal.

The large majority of signals were recorded on `M-CAN`. Signals from ECUs on other busses that aren't known to be broadcast on `M-CAN` should be distinguished as such in a comment.

**WARNING** Meddling with your canbus can harm your car or void your warranty!

# Branches

We maintain `main` and `testing` branches. `main` is well-validated signals, while testing is bleeding-edge reverse engineering that may contain wild misinterpretations. At the moment, we don't have a validation pipeline, so `testing` is far ahead of `main`.

## 11-bit to 29-bit ID translation for CCU cars

Ioniq 5 and EV6 CAN frame IDs are strictly 11-bit. Cars with a CCU (Ioniq 6, GV60 and later) have 29-bit IDs, and there appears to be a translation scheme between them. See [EXTENDED_IDS.md](EXTENDED_IDS.md) for more information on this translation scheme.

