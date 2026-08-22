#!/usr/bin/env python3
"""Validate hand-curated DBC files.

Checks per file:
  - statement lines (CM_/BA_/VAL_/VAL_TABLE_) have balanced quotes and end with ';'
  - unique BO_ ids
  - every SG_ fits inside its frame's DLC
  - cantools strict load (with a workaround for the known cantools crash when
    "VFrameFormat" attributes only cover some messages: retries on a copy with
    those lines stripped and downgrades the failure to a warning)

Only top-level *.dbc files are validated. Each file is checked in a subprocess
with a timeout so one pathological file cannot hang CI.

Exit code 0 = no errors (warnings allowed), 1 = at least one error.
"""

import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile

TIMEOUT_S = 60
VFVF_CRASH = "cannot access local variable 'frame_format'"
STATEMENT_RE = re.compile(r"^(CM_|BA_|VAL_|VAL_TABLE_)")


def strip_vframe_format(text):
    return "\n".join(
        ln for ln in text.splitlines()
        if 'VFrameFormat' not in ln or ln.startswith(("NS_", "NS_DESC_"))
    ) + "\n"


def check_statements(text):
    """Quote-balance / ';' termination across (possibly multi-line) statements."""
    errors = []
    in_str = False
    start_line = None
    quotes = 0
    terminated = False
    prev = ""

    for i, ln in enumerate(text.splitlines(), 1):
        if not in_str:
            if not STATEMENT_RE.match(ln):
                prev = ln[-1:] if ln else prev
                continue
            start_line, quotes, terminated = i, 0, False
        for ch in ln:
            if ch == '"' and prev != "\\":
                in_str = not in_str
                quotes += 1
            elif ch == ";" and not in_str:
                terminated = True
                if quotes % 2:
                    errors.append(f"line {start_line}: unbalanced quotes")
            prev = ch
        if terminated:
            in_str, start_line = False, None

    if start_line is not None or in_str:
        errors.append(f"line {start_line}: missing ';' terminator")
    return errors


def check_file(path):
    """Return (errors, warnings) for one DBC file."""
    errors, warnings = [], []

    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError as e:
        return [f"unreadable: {e}"], warnings

    errors.extend(check_statements(text))

    ids = re.findall(r"^BO_ (\d+) ", text, re.M)
    dupes = sorted({i for i in ids if ids.count(i) > 1}, key=int)
    if dupes:
        errors.append(f"duplicate BO_ ids: {', '.join(dupes)}")

    for m in re.finditer(r"^BO_ (\d+) [^:]+: (\d+)", text, re.M):
        msg_id, dlc = m.group(1), int(m.group(2))
        block = re.search(
            rf"^BO_ {msg_id} \n?(.*?)(?=^BO_ |\Z)", text, re.M | re.S)
        body = block.group(0) if block else ""
        for s in re.finditer(r"SG_ \S+ : (\d+)\|(\d+)@", body):
            if int(s.group(1)) + int(s.group(2)) > 8 * dlc:
                errors.append(
                    f"BO_ {msg_id}: signal bits {s.group(1)}+{s.group(2)}"
                    f" exceed {8 * dlc}-bit frame")

    import cantools
    try:
        db = cantools.database.load_file(path, strict=True)
    except Exception as e:
        if VFVF_CRASH in str(e):
            with tempfile.NamedTemporaryFile(
                    "w", suffix=".dbc", delete=False,
                    encoding="utf-8") as tmp:
                tmp.write(strip_vframe_format(text))
                sanitized = tmp.name
            try:
                cantools.database.load_file(sanitized, strict=True)
                warnings.append(
                    "loads only after stripping \"VFrameFormat\" attributes "
                    "(cantools bug with partial attribute coverage); add "
                    "explicit BA_ \"VFrameFormat\" for every message or drop "
                    "the attribute entirely")
            except Exception as e2:
                errors.append(f"cantools strict load failed: {e2}")
            finally:
                os.unlink(sanitized)
        else:
            errors.append(f"cantools strict load failed: {e}")
    return errors, warnings


def worker(path):
    errors, warnings = check_file(path)
    for w in warnings:
        print(f"WARN {w}")
    for e in errors:
        print(f"ERROR {e}")
    sys.exit(1 if errors else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check-one", metavar="FILE",
                    help=argparse.SUPPRESS)  # internal worker mode
    args = ap.parse_args()

    if args.check_one:
        worker(args.check_one)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = sorted(glob.glob(os.path.join(root, "*.dbc")))
    if not files:
        print("no top-level .dbc files found")
        sys.exit(1)

    had_error = False
    for f in files:
        rel = os.path.relpath(f, root)
        try:
            p = subprocess.run(
                [sys.executable, os.path.abspath(__file__), "--check-one", f],
                capture_output=True, text=True, timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired:
            had_error = True
            print(f"FAIL {rel}: timed out after {TIMEOUT_S}s")
            print(f"::error file={rel}::timed out after {TIMEOUT_S}s")
            continue

        warns = [l[5:].strip() for l in p.stdout.splitlines()
                 if l.startswith("WARN ")]
        errs = [l[6:].strip() for l in p.stdout.splitlines()
                if l.startswith("ERROR ")]

        if errs:
            had_error = True
            print(f"FAIL {rel}")
            for e in errs + p.stderr.strip().splitlines():
                print(f"  ERROR {e}")
                print(f"::error file={rel}::{e}")
        elif p.returncode != 0:
            had_error = True
            stderr = p.stderr.strip() or f"worker exited {p.returncode}"
            print(f"FAIL {rel}\n  ERROR {stderr}")
            print(f"::error file={rel}::{stderr}")
        else:
            n = count_messages(f)
            print(f"OK   {rel} ({n} messages)")
            for w in warns:
                print(f"  WARN {w}")
                print(f"::warning file={rel}::{w}")

    sys.exit(1 if had_error else 0)


def count_messages(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return len(re.findall(r"^BO_ \d+ ", fh.read(), re.M))


if __name__ == "__main__":
    main()
