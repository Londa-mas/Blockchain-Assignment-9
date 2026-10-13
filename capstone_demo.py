import urllib.request
import json
import time
from ecdsa import SigningKey, SECP256k1
from wallet import Wallet, canonical_tx_payload

BASE_URL = "http://127.0.0.1:5000"

def send_request(endpoint, method="GET", data=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    req_data = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode('utf-8')
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return e.code, json.loads(error_body) if error_body else {}
    except Exception as e:
        print(f"Connection error: {e}")
        return None, None

def run_capstone_demo():
    print("=== CAPSTONE DEMO FLOW: AFRICAN REMITTANCE PROTOTYPE ===")

    print("\n[1] Inspecting Initial Wallets...")
    status, res = send_request("/wallets", method="GET")
    print(json.dumps(res, indent=4))

    sender_priv_hex = res["Sender"]["private_key"]
    sender_pubkey = res["Sender"]["public_key"]
    sender_wallet = Wallet(SigningKey.from_string(bytes.fromhex(sender_priv_hex), curve=SECP256k1))

    print("\n[2] On-Ramp: Sender deposits 1,000 local fiat -> 1,000 mZAR (Locked in Reserve)...")
    status, res = send_request("/remittance/onramp", method="POST", data={"wallet_id": "Sender", "amount": 1000.0})
    print(json.dumps(res, indent=4))

    print("\n[3] Auditing 1:1 Reserve Invariant Status...")
    status, res = send_request("/reserve/status", method="GET")
    print(json.dumps(res, indent=4))

    print("\n[4] Transfer: Sender cryptographically signs and sends 750 mZAR to Recipient...")
    timestamp = time.time()
    payload = canonical_tx_payload("Sender", "Recipient", 750.0, timestamp)
    signature = sender_wallet.sign(payload)

    tx_data = {
        "sender": "Sender",
        "recipient": "Recipient",
        "amount": 750.0,
        "timestamp": timestamp,
        "public_key": sender_pubkey,
        "signature": signature
    }
    status, res = send_request("/transactions/new", method="POST", data=tx_data)
    print(json.dumps(res, indent=4))

    print("\n[5] Mining the Remittance Block...")
    status, res = send_request("/mine", method="POST")
    print(json.dumps(res, indent=4))

    print("\n[6] Off-Ramp: Recipient redeems 750 mZAR to local fiat (Released from Reserve)...")
    status, res = send_request("/remittance/offramp", method="POST", data={"wallet_id": "Recipient", "amount": 750.0})
    print(json.dumps(res, indent=4))

    print("\n[6b] Auditing 1:1 Reserve after Redemption (vault decreases)...")
    status, res = send_request("/reserve/status", method="GET")
    print(json.dumps(res, indent=4))

    print("\n[7] Verification: Verifying Chain Integrity & Transaction Lookup...")
    status, res = send_request("/chain/verify", method="GET")
    print(f"Chain Verification Status (Valid = True): {res}")
    
    status, res = send_request("/transactions/lookup", method="POST", data={"sender": "Sender", "amount": 750.0})
    print(json.dumps(res, indent=4))

    print("\n[8a] Negative Test 1: Attempting transfer with insufficient balance...")
    bad_bal_ts = time.time()
    bad_bal_payload = canonical_tx_payload("Sender", "Recipient", 99999.0, bad_bal_ts)
    bad_bal_sig = sender_wallet.sign(bad_bal_payload)
    bad_balance_tx = {
        "sender": "Sender",
        "recipient": "Recipient",
        "amount": 99999.0,
        "timestamp": bad_bal_ts,
        "public_key": sender_pubkey,
        "signature": bad_bal_sig
    }
    status, res = send_request("/transactions/new", method="POST", data=bad_balance_tx)
    print(f"Expected Rejection Status (400): {status}")
    print(json.dumps(res, indent=4))

    print("\n[8b] Negative Test 2: Attempting transfer with invalid cryptographic signature...")
    bad_sig_ts = time.time()
    bad_sig_tx = {
        "sender": "Sender",
        "recipient": "Recipient",
        "amount": 10.0,
        "timestamp": bad_sig_ts,
        "public_key": sender_pubkey,
        "signature": "deadbeef" * 16
    }
    status, res = send_request("/transactions/new", method="POST", data=bad_sig_tx)
    print(f"Expected Rejection Status (400): {status}")
    print(json.dumps(res, indent=4))

if __name__ == "__main__":
    run_capstone_demo()