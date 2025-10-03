#!/usr/bin/env python3
import os, sys, json, subprocess

def parse_value(val):
    if isinstance(val, str):
        hexs = val.split()
        return bytes(int(x, 16) for x in hexs)
    if isinstance(val, list):
        if not val:
            return b""
        if isinstance(val[0], int):
            return bytes(val)
        if isinstance(val[0], str):
            try:
                return bytes(int(x, 0) for x in val)
            except Exception as e:
                raise SystemExit(f"unexpected string list in value: {val[:8]} ... ({e})")
    raise SystemExit(f"unexpected bpftool JSON format for 'value': {type(val)}")

def dump(path):
    p = subprocess.run(["bpftool","map","dump","pinned",path,"-j"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit(p.stderr.strip() or p.stdout.strip() or f"bpftool failed ({p.returncode})")
    j = json.loads(p.stdout)
    if not j:
        raise SystemExit(f"{path}: map is empty")
    if "value" not in j[0]:
        raise SystemExit(f"{path}: no 'value' in bpftool output")
    return parse_value(j[0]["value"])

def main():
    a = dump("/sys/fs/bpf/part_a")
    b = dump("/sys/fs/bpf/part_b")
    n = min(len(a), len(b))
    flag = bytes([a[i]^b[i] for i in range(n)]).split(b"\x00",1)[0]
    print(flag.decode(errors="replace"))

if __name__ == "__main__":
    main()
