#!/usr/bin/env python3
import os, sys, time, subprocess

RUNNER = "./shell"
FLAG   = "./flag.txt"
ALPH   = "{}_0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()-+=[]<>/?.,:;"

def run_masked():
    p = subprocess.run([RUNNER, "/bin/cat", FLAG],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if p.returncode != 0:
        raise SystemExit(f"runner exit {p.returncode}")
    return p.stdout

def main():
    os.makedirs(os.path.dirname(FLAG) or ".", exist_ok=True)
    flag = "stctf{"
    with open(FLAG, "wb") as f:
        f.write(flag.encode())

    t0 = time.time()
    total_tries = 0
    found_count = 0
    try:
        from tqdm import tqdm
        use_tqdm = True
    except Exception:
        use_tqdm = False
    while True:
        i = len(flag)
        found = None
        if use_tqdm:
            bar = tqdm(ALPH, leave=False, desc=f"pos {i}", unit="try")
        else:
            print(f"\n[.] pos {i}: перебираю {len(ALPH)} символов...", flush=True)
        for c in ALPH:
            total_tries += 1
            test = (flag + c).encode()
            with open(FLAG, "wb") as f:
                f.write(test)
            out = run_masked()

            if i < len(out) and out[i:i+1] == b"*":
                found = c
                if use_tqdm:
                    bar.close()
                else:
                    print(f"[+] pos {i}: найден '{c}'", flush=True)
                break
            if use_tqdm:
                bar.update(1)
            else:
                if total_tries % 20 == 0:
                    elapsed = time.time() - t0
                    rate = (found_count / elapsed * 60) if elapsed > 0 else 0.0
                    print(f"  ... tries={total_tries}, elapsed={elapsed:,.1f}s, speed={rate:.2f} char/min", end="\r", flush=True)
        if not found:
            elapsed = time.time() - t0
            print(f"\n[!] не нашёл символ на позиции {i}. "
                  f"elapsed={elapsed:,.1f}s, tries={total_tries}")
            sys.exit(2)
        flag += found
        found_count += 1
        elapsed = time.time() - t0
        rate = (found_count / elapsed * 60) if elapsed > 0 else 0.0
        print(f"\r[prog] {flag}  | len={len(flag)}  | elapsed={elapsed:,.1f}s  | speed={rate:.2f} char/min", end="", flush=True)
        if found == "}":
            print(f"\nDONE: {flag}")
            with open(FLAG, "wb") as f:
                f.write(flag.encode())
            break

if __name__ == "__main__":
    main()
