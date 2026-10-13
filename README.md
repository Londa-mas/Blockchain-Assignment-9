# mZAR Remittance Prototype 

**Course:** Master of Financial Engineering (MFE), University of Johannesburg  
**Module:** BLCH9X2 Blockchain  
**Group Members:** O.T.H Masuku, P.T. Molete, & M.M. Moketla

---


A simplified remittance payment platform built on our semester blockchain. A sender converts rand into a simulated stablecoin (mZAR) at a 1:1 reserve rule, transfers it in an ECDSA-signed transaction that is mined into a block, and the recipient redeems it for rand. Every step is recorded and verifiable through a small Flask API and an HTML explorer.

This is a teaching prototype, not a production remittance product. All keys are throwaway demo keys generated fresh on each run, and no real funds are involved.

## Requirements

- Python 3.10 or later
- The libraries in `requirements.txt` (Flask and ecdsa)

## Setup (clean virtual environment)

From inside the project folder:

```bash
python -m venv venv
```

Activate it:

- **Windows:** `venv\Scripts\activate`
- **macOS / Linux:** `source venv/bin/activate`

Then install the libraries:

```bash
pip install -r requirements.txt
```

## Running the demo

Use two terminals, both in the project folder with the virtual environment active.

**Terminal 1: start the server** and leave it running:

```bash
python app.py
```

Wait for `Running on http://127.0.0.1:5000`.

**Terminal 2: run the remittance path:**

```bash
python capstone_demo.py
```

**Then open in a browser:**

- `http://127.0.0.1:5000/explorer` (wallets, receipts and the full chain)

All state is held in memory. Restart the server (Ctrl+C, then `python app.py`) before each run to start from a clean chain.

## What the demo shows

| Step | Action | Expected result |
| --- | --- | --- |
| [1] | Inspect wallets | Sender R5,000; Recipient R0; ReserveAgent R1,000,000, each with an ECDSA key pair and address |
| [2] | On-ramp 1,000 | Sender receives 1,000 mZAR; ReserveAgent rises to R1,001,000; receipt issued with a receipt ID |
| [3] | Reserve audit | 1,000 mZAR circulating, 1,000 backing, `fully_backed: true` |
| [4] | Signed transfer of 750 | Signature verified; HTTP 201, queued for block 1 |
| [5] | Mine | Block 1 created at proof-of-work difficulty 2, containing the transfer and its transaction ID |
| [6] | Off-ramp 750 | Recipient's 750 mZAR burned; ReserveAgent pays R750; receipt issued with a receipt ID |
| [6b] | Reserve audit after redemption | 250 mZAR circulating, 250 backing; ReserveAgent down to R1,000,250 |
| [7] | Verify and look up | `chain_valid: true`; the transfer found in block 1 |
| [8a] | Transfer of 99,999 (valid signature) | Rejected, HTTP 400: insufficient balance |
| [8b] | Transfer with forged signature | Rejected, HTTP 400: invalid signature |

Keys, signatures, hashes, IDs and timestamps differ on every run; balances and messages do not.

## Running the tests

With the virtual environment active (the server does not need to be running):

```bash
python tests.py
```

Expected result: `OK (expected failures=3)`. Eight tests confirm working features (reserve backing, signature checks, balance checks, transaction IDs, chain verification, lookup). Three tests are marked as expected failures: they document the known limitations listed below and in section (f) of the report.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/wallets` | Wallets, balances, keys and addresses |
| POST | `/remittance/onramp` | Convert rand to mZAR at 1:1; body `{"wallet_id", "amount"}` |
| GET | `/reserve/status` | Circulating mZAR, reserve held, and whether fully backed |
| POST | `/transactions/new` | Submit a signed transfer; body `{"sender", "recipient", "amount", "timestamp", "public_key", "signature"}` |
| POST | `/mine` | Mine pending transactions into a block |
| POST | `/remittance/offramp` | Redeem mZAR for rand; body `{"wallet_id", "amount"}` |
| GET | `/chain/verify` | Check hash links and block hashes |
| POST | `/transactions/lookup` | Find a mined transfer; body `{"sender", "amount"}` |
| GET | `/receipts` | On-ramp and off-ramp receipts |
| GET | `/explorer` | HTML view of wallets, receipts and the chain |

## Files

| File | Purpose |
| --- | --- |
| `app.py` | Blockchain class and Flask API |
| `wallet.py` | ECDSA (SECP256k1) key pairs, addresses, signing and verification (from Assignment 4) |
| `capstone_demo.py` | Runs the full remittance path against the API |
| `tests.py` | Automated tests of features and known limitations |
| `requirements.txt` | Library dependencies |

## Known limitations

See section (f) of the report: server-held demo keys, no replay protection, proof-of-work that does not cover a block's own transactions, balances updated before mining, a single in-memory node, and no confirmation depth beyond one block.
