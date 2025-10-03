#!/usr/bin/env python3
import sys
import struct
import itertools
from typing import List, Tuple, Optional
from Crypto.Cipher import AES

MAGIC = b"SCTFBv01"
HEX_ALPHABET = "0123456789abcdef"
BRUTE_POSITIONS = (12, 13, 14, 15)

def pkcs7_unpad(b: bytes, block: int = 16) -> bytes:
    if not b or len(b) % block != 0:
        raise ValueError("bad length for PKCS#7")
    pad = b[-1]
    if pad == 0 or pad > block or b[-pad:] != bytes([pad]) * pad:
        raise ValueError("bad PKCS#7 padding")
    return b[:-pad]

def decrypt_try(ct: bytes, key16: bytes) -> Optional[bytes]:
    try:
        ptp = AES.new(key16, AES.MODE_ECB).decrypt(ct)
        return pkcs7_unpad(ptp, 16)
    except Exception:
        return None

def is_asciiish(b: bytes) -> bool:
    return all((32 <= x <= 126) or x in (9, 10, 13) for x in b)

def parse_container(path: str) -> List[Tuple[bytes, bytearray]]:
    with open(path, "rb") as f:
        blob = f.read()
    if len(blob) < 12:
        raise ValueError("too short")
    if blob[:8] != MAGIC:
        raise ValueError("bad magic")
    (count,) = struct.unpack(">I", blob[8:12])
    off = 12
    blocks: List[Tuple[bytes, bytearray]] = []
    for i in range(count):
        if off + 4 > len(blob):
            raise ValueError(f"truncated header at block {i}")
        ct_len, key_len = struct.unpack(">HH", blob[off:off + 4])
        off += 4
        if key_len != 16:
            raise ValueError(f"block {i}: key_len != 16")
        if off + ct_len + key_len > len(blob):
            raise ValueError(f"truncated payload at block {i}")
        ct = blob[off:off + ct_len]
        off += ct_len
        key = bytearray(blob[off:off + key_len])
        off += key_len
        blocks.append((ct, key))
    return blocks

def brute_last4_hex(ct: bytes, key: bytearray) -> Optional[bytes]:
    k = bytearray(key)
    for combo in itertools.product(HEX_ALPHABET, repeat=len(BRUTE_POSITIONS)):
        for idx, pos in enumerate(BRUTE_POSITIONS):
            k[pos] = ord(combo[idx])
        pt = decrypt_try(ct, bytes(k))
        if pt is not None and is_asciiish(pt):
            return pt
    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: solution.py <container.sc>")
        sys.exit(1)

    blocks = parse_container(sys.argv[1])

    plaintexts: List[bytes] = []
    for ct, key in blocks:
        pt = decrypt_try(ct, bytes(key))
        if pt is None:
            pt = brute_last4_hex(ct, key)
        plaintexts.append(pt if pt is not None else b"<failed>")

    try:
        flag = b"".join(plaintexts).decode("utf-8", "replace")
    except Exception:
        flag = "".join(p.decode("latin1", "replace") for p in plaintexts)

    print(flag)

if __name__ == "__main__":
    main()
