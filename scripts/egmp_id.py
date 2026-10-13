#!/usr/bin/env python3
"""11-bit <-> 29-bit CCU CAN hub id mapping for E-GMP cars.

DeepSeek V4.1 Flash determined this mapping and this is totally vibe-coded, but
many of the mapped IDs have been tested and work.

The CCU CAN hub (Ioniq 6, GV60, ...) re-addresses classic 11-bit car-bus frames
onto 29-bit extended ids that encode the original id:

    prefix = 4 * (base >> 4)
    ext    = (prefix << 20) | (base << 8) | index        # id11 = base + index

where ``base = min(id11 of the family) - 1`` and ``index = 1..N`` inside the
family.  Decoding is the authoritative direction: an extended id carries its own
base, so ``from_extended()`` never has to guess.  See README.md, "11-bit to
29-bit ID translation for CCU cars", for the field-verified family table.

The DBCs in this repo use ``BO_ = 0x80000000 | ext`` for these frames plus
``BA_ "VFrameFormat" BO_ <id> 1`` (ExtendedCAN); :func:`dbc_frame_id` and
:func:`ext_from_dbc_frame_id` convert to and from that convention.

Gotcha: :func:`family_base_from_ids` derives a base from a set of 11-bit ids and
therefore *assumes the set is the complete family*.  A capture that only
transmitted ``0x152`` of the ``0x151..0x154`` family would derive base ``0x151``
and encode it wrongly as ``0x05415101``.  Use the extended ids from the capture
(or a complete family) whenever you can.

No third-party dependencies.  Run ``python3 scripts/egmp_id.py selftest`` to
check the mapping against ids recorded in this repo's DBCs.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, NamedTuple

ID11_MAX = 0x7FF
BASE_MAX = 0xFFF
INDEX_MAX = 0xFF
PREFIX_MAX = 0xFFF
EXT_MAX = 0x1FFFFFFF
DBC_EXTENDED_FLAG = 0x80000000


class Remap(NamedTuple):
    """One decoded extended id: ``id11 == base + index``."""

    base: int
    index: int
    id11: int


def prefix_for_base(base: int) -> int:
    """The id-space prefix this family's extended ids are filed under."""
    if not 0 <= base <= BASE_MAX:
        raise ValueError(f"base 0x{base:X} outside 0x000..0xFFF")
    return 4 * (base >> 4)


def to_extended(id11: int, base: int) -> int:
    """Encode an 11-bit car-bus id into its 29-bit CCU-hub id.

    ``base`` is the family base (``min(id11 of the family) - 1``); ``id11`` must
    be inside that family, i.e. ``base + 1 <= id11 <= base + 0xFF``.
    """
    if not 0 <= id11 <= ID11_MAX:
        raise ValueError(f"id11 0x{id11:X} outside 0x000..0x7FF")
    index = id11 - base
    if not 1 <= index <= INDEX_MAX:
        raise ValueError(
            f"id11 0x{id11:X} is not in the family with base 0x{base:X} "
            f"(index would be {index}, want 1..{INDEX_MAX})")
    return (prefix_for_base(base) << 20) | ((base & BASE_MAX) << 8) | index


def is_remap(ext: int) -> bool:
    """True if ``ext`` looks like a CCU-hub remap of an 11-bit id."""
    if not 0 <= ext <= EXT_MAX:
        return False
    base, index = (ext >> 8) & BASE_MAX, ext & INDEX_MAX
    return (index != 0
            and base + index <= ID11_MAX
            and (ext >> 20) & PREFIX_MAX == prefix_for_base(base))


def from_extended(ext: int) -> Remap:
    """Decode a 29-bit CCU-hub id into ``(base, index, id11)``.

    Raises ValueError if the prefix does not match ``4 * (base >> 4)``, if the
    index is zero (an id that was never remapped) or if the decoded id11 is not
    an 11-bit id.
    """
    if not 0 <= ext <= EXT_MAX:
        raise ValueError(f"ext 0x{ext:X} outside 0x00000000..0x1FFFFFFF")
    base, index = (ext >> 8) & BASE_MAX, ext & INDEX_MAX
    prefix = (ext >> 20) & PREFIX_MAX
    if index == 0:
        raise ValueError(f"0x{ext:08X}: index 0, not a CCU-hub remap")
    if prefix != prefix_for_base(base):
        raise ValueError(
            f"0x{ext:08X}: prefix 0x{prefix:03X} != 4 * (base 0x{base:03X} >> 4) "
            f"= 0x{prefix_for_base(base):03X}")
    id11 = base + index
    if id11 > ID11_MAX:
        raise ValueError(f"0x{ext:08X}: decodes to 0x{id11:X}, not an 11-bit id")
    return Remap(base=base, index=index, id11=id11)


def family_base_from_ids(ids11: Iterable[int]) -> int:
    """Family base for a *complete* set of 11-bit family ids (``min - 1``).

    Assumes the lowest family member is present; see the module docstring.
    """
    ids = sorted(set(ids11))
    if not ids:
        raise ValueError("no ids given")
    for i in ids:
        if not 0 <= i <= ID11_MAX:
            raise ValueError(f"id11 0x{i:X} outside 0x000..0x7FF")
    return ids[0] - 1


def encode_family(ids11: Iterable[int]) -> dict[int, int]:
    """Map a whole complete family of 11-bit ids to their extended ids."""
    base = family_base_from_ids(ids11)
    return {i: to_extended(i, base) for i in sorted(set(ids11))}


def dbc_frame_id(ext: int) -> int:
    """``BO_`` value for an extended frame: ``0x80000000 | ext``."""
    from_extended(ext)  # validate
    return DBC_EXTENDED_FLAG | ext


def ext_from_dbc_frame_id(frame_id: int) -> int:
    """Recover the on-bus extended id from a ``BO_`` value."""
    if not frame_id & DBC_EXTENDED_FLAG:
        raise ValueError(f"BO_ {frame_id}: bit 31 clear, not an extended frame")
    return frame_id & ~DBC_EXTENDED_FLAG


def _format(ext: int) -> str:
    r = from_extended(ext)
    return (f"0x{ext:08X}  base 0x{r.base:03X}  index {r.index:3d}  "
            f"id11 0x{r.id11:03X}  BO_ {dbc_frame_id(ext)}")


# (id11, base, ext) vectors all recorded in this repo's DBCs, plus the two ids
# recovered from the Oct 2026 Ioniq 6 captures (0x152, 0x2FC).
VECTORS = (
    (0x037, 0x035, 0x00C03502),
    (0x038, 0x035, 0x00C03503),
    (0x0A1, 0x0A0, 0x0280A001),
    (0x0A2, 0x0A0, 0x0280A002),
    (0x10C, 0x10A, 0x04010A02),
    (0x151, 0x150, 0x05415001),
    (0x152, 0x150, 0x05415002),
    (0x153, 0x150, 0x05415003),
    (0x154, 0x150, 0x05415004),
    (0x236, 0x235, 0x08C23501),
    (0x2AB, 0x2AA, 0x0A82AA01),
    (0x2AC, 0x2AA, 0x0A82AA02),
    (0x2AD, 0x2AA, 0x0A82AA03),
    (0x2AE, 0x2AA, 0x0A82AA04),
    (0x2E2, 0x2E0, 0x0B82E002),
    (0x2E3, 0x2E0, 0x0B82E003),
    (0x2E4, 0x2E0, 0x0B82E004),
    (0x2FB, 0x2FA, 0x0BC2FA01),
    (0x2FC, 0x2FA, 0x0BC2FA02),
    (0x337, 0x335, 0x0CC33502),
    (0x397, 0x395, 0x0E439502),
    (0x398, 0x395, 0x0E439503),
)


def selftest() -> int:
    """Check encode/decode against :data:`VECTORS`. Returns an exit code."""
    failures = []
    for id11, base, ext in VECTORS:
        if to_extended(id11, base) != ext:
            failures.append(
                f"encode 0x{id11:03X}/base 0x{base:03X}: "
                f"0x{to_extended(id11, base):08X} != 0x{ext:08X}")
        r = from_extended(ext)
        if r != Remap(base, id11 - base, id11):
            failures.append(f"decode 0x{ext:08X}: {r} != ({base:#05x}, ..., {id11:#05x})")
        if not is_remap(ext):
            failures.append(f"is_remap(0x{ext:08X}) is False")
        if ext_from_dbc_frame_id(dbc_frame_id(ext)) != ext:
            failures.append(f"BO_ round trip failed for 0x{ext:08X}")

    for ids, base, exts in (
        ((0x151, 0x152, 0x153, 0x154), 0x150,
         (0x05415001, 0x05415002, 0x05415003, 0x05415004)),
    ):
        fam = encode_family(ids)
        if family_base_from_ids(ids) != base or list(fam.values()) != list(exts):
            failures.append(f"family {ids}: base 0x{family_base_from_ids(ids):03X} -> {fam}")

    for bad in (0x00000000, 0x00C03500, 0x20000000, 0x0FF03503, 0x1FC7F020):
        try:
            from_extended(bad)
        except ValueError:
            pass
        else:
            failures.append(f"from_extended(0x{bad:08X}) should have raised")
    for id11, base in ((0x152, 0x152), (0x800, 0x7FF), (0x152, 0x1000)):
        try:
            to_extended(id11, base)
        except ValueError:
            pass
        else:
            failures.append(f"to_extended(0x{id11:X}, 0x{base:X}) should have raised")

    # A wrong-but-plausible base is NOT detectable from the id alone: 0x152 with
    # base 0x151 encodes happily as 0x05415101.  This is why a base derived from
    # a capture is only trustworthy if the family's lowest member was present;
    # prefer from_extended() on ids that already carry their own base.
    if to_extended(0x152, 0x151) != 0x05415101:
        failures.append("wrong-base trap behaves unexpectedly")

    for f in failures:
        print(f"FAIL {f}")
    print(f"{len(VECTORS)} vectors, {'FAILED' if failures else 'all checks OK'}")
    return 1 if failures else 0


def _int(text: str) -> int:
    return int(text, 0)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("decode", help="29-bit id -> base/index/id11/BO_")
    p.add_argument("ext", nargs="+", type=_int)

    p = sub.add_parser("encode", help="11-bit id + family base -> 29-bit id/BO_")
    p.add_argument("id11", type=_int)
    p.add_argument("--base", type=_int, required=True,
                   help="family base, i.e. min(id11 of the family) - 1")

    p = sub.add_parser("family", help="complete family of 11-bit ids -> base + ext ids")
    p.add_argument("ids11", nargs="+", type=_int)

    sub.add_parser("selftest", help="check the mapping against the DBC-recorded ids")

    args = ap.parse_args()

    if args.cmd == "selftest":
        return selftest()
    if args.cmd == "decode":
        for ext in args.ext:
            try:
                print(_format(ext))
            except ValueError as e:
                print(f"0x{ext:08X}  not a remap: {e}")
        return 0
    if args.cmd == "encode":
        ext = to_extended(args.id11, args.base)
        print(_format(ext))
        return 0
    if args.cmd == "family":
        base = family_base_from_ids(args.ids11)
        print(f"base 0x{base:03X} (prefix 0x{prefix_for_base(base):03X})")
        for id11, ext in encode_family(args.ids11).items():
            print(f"    id11 0x{id11:03X} -> 0x{ext:08X}  BO_ {dbc_frame_id(ext)}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
