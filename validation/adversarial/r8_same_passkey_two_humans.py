"""R8: check_root rejects a repeated key by keyid = sha256(encoded public bytes). A P-256 passkey has two encodings
(compressed / uncompressed), so the same physical key enrols as two distinct humans, and one WebAuthn assertion is then
counted twice towards a human quorum."""
import sys, base64, copy
import pathlib; _r = pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0, str(_r / "tests")); sys.path.insert(0, str(_r))
from fixture import World
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from tcb.crypto import keyid, verify, b64u_enc
from tcb.kernel import check_root, Refused
import hashlib, json

k = ec.generate_private_key(ec.SECP256R1())
pubs = [base64.b64encode(k.public_key().public_bytes(Encoding.X962, f)).decode()
        for f in (PublicFormat.UncompressedPoint, PublicFormat.CompressedPoint)]
w = World(genesis=False)
root = copy.deepcopy(w.root)
for name, p in zip(("mallory1", "mallory2"), pubs):
    root["identities"][name] = {"kind": "human", "keys": [{"alg": "webauthn-es256", "public": p, "keyid": keyid(p),
                                "rp_id": "ex.org", "origins": ["https://ex.org"]}]}
try:
    check_root(root); print("check_root: ACCEPTED two humans with the same passkey")
except Refused as r:
    print("check_root refused:", r)
msg = b"DSSEv1 test"
client = json.dumps({"type": "webauthn.get", "origin": "https://ex.org",
                     "challenge": b64u_enc(hashlib.sha256(msg).digest())}).encode()
auth = hashlib.sha256(b"ex.org").digest() + bytes([0x05]) + b"\0\0\0\1"
from cryptography.hazmat.primitives import hashes
sig = k.sign(auth + hashlib.sha256(client).digest(), ec.ECDSA(hashes.SHA256()))
wa = {"authenticatorData": b64u_enc(auth), "clientDataJSON": b64u_enc(client)}
for name in ("mallory1", "mallory2"):
    key = root["identities"][name]["keys"][0]
    print(name, "verifies one assertion:", verify(key, msg, {"keyid": key["keyid"], "sig": b64u_enc(sig), "webauthn": wa}))
