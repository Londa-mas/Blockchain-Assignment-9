import urllib.request
import json

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
        print(f"HTTP Error {e.code}: {error_body}")
        return e.code, json.loads(error_body) if error_body else {}
    except Exception as e:
        print(f"Connection error: {e}")
        return None, None

def run_capstone_demo():
    print("=== CAPSTONE DEMO FLOW: AFRICAN REMITTANCE PROTOTYPE ===")

    print("\n[1] Inspecting Initial Wallets...")
    status, res = send_request("/wallets", method="GET")
    print(json.dumps(res, indent=4))

    print("\n[2] On-Ramp: Sender deposits 1,000 local fiat -> 1,000 mZAR...")
    status, res = send_request("/remittance/onramp", method="POST", data={"wallet_id": "Sender", "amount": 1000.0})
    print(json.dumps(res, indent=4))

    print("\n[3] Transfer: Sender sends 750 mZAR to Recipient...")
    tx_data = {
        "sender": "Sender",
        "recipient": "Recipient",
        "amount": 750.0,
        "signature": "valid_sig_abc123"
    }
    status, res = send_request("/transactions/new", method="POST", data=tx_data)
    print(json.dumps(res, indent=4))

    print("\n[4] Mining the Remittance Block...")
    status, res = send_request("/mine", method="POST")
    print(json.dumps(res, indent=4))

    print("\n[5] Off-Ramp: Recipient redeems 750 mZAR to local fiat...")
    status, res = send_request("/remittance/offramp", method="POST", data={"wallet_id": "Recipient", "amount": 750.0})
    print(json.dumps(res, indent=4))

    print("\n[6] Verification: Verifying Chain Integrity & Transaction Lookup...")
    status, res = send_request("/chain/verify", method="GET")
    print(f"Chain Verification Status (Valid = True): {res}")
    
    status, res = send_request("/transactions/lookup", method="POST", data={"sender": "Sender", "amount": 750.0})
    print(json.dumps(res, indent=4))

    print("\n[7] Negative Test: Attempting invalid transfer (insufficient balance / bad signature)...")
    bad_tx = {
        "sender": "Sender",
        "recipient": "Recipient",
        "amount": 5000.0,
        "signature": "INVALID_SIG"
    }
    status, res = send_request("/transactions/new", method="POST", data=bad_tx)
    print(f"Expected Rejection Status: {status}")
    print(json.dumps(res, indent=4))

if __name__ == "__main__":
    run_capstone_demo()