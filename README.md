# BLCH9X2 — Assignment 9: Financial Blockchain Capstone: African Remittances Payment Prototype

**Course:** Master of Financial Engineering (MFE), University of Johannesburg  
**Module:** BLCH9X2 Blockchain  
**Group Members:** O.T.H Masuku, P.T. Molete, & M. Moketla

---

## 1. Project Overview
This repository contains the Minimum Viable Product (MVP) for the **African Remittances Payment Prototype** capstone project. The prototype demonstrates a verifiable cross-border remittance architecture where local currency is converted to a simulated stablecoin ("mZAR") under a 1:1 reserve rule, transferred securely across an immutable cryptographic ledger, redeemed back to local fiat, and audited via an integrated REST API and web explorer.

---

## 2. Core Features & Architecture
* **`app.py`**: The unified Flask backend application combining ledger state management, cryptographic hashing, Proof-of-Work mining, fiat-stablecoin on/off ramp gateway logic, account wallets, and the HTML block explorer.
* **`capstone_demo.py`**: An automated end-to-end test script executing the full reproducible remittance demonstration flow.

---

## 3. API Endpoint Specification

| Method | Path | Purpose / Description | Success Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/wallets` | Inspects account balances across all wallets (Reserve Agent, Sender, Recipient). | `200 OK` |
| `GET` | `/receipts` | Retrieves the audit log of all fiat/stablecoin on-ramp and off-ramp receipts. | `200 OK` |
| `POST` | `/remittance/onramp` | Converts local fiat currency units to stablecoin (mZAR) at a 1:1 ratio. | `200 OK` |
| `POST` | `/remittance/offramp` | Redeems stablecoin (mZAR) balance back to local fiat currency. | `200 OK` |
| `POST` | `/transactions/new` | Validates balances/signatures and enqueues a stablecoin transfer into the mempool. | `201 Created` |
| `POST` | `/transactions/lookup` | Searches the immutable ledger for a specific transaction by sender and amount. | `200 OK` |
| `POST` | `/mine` | Executes Proof-of-Work difficulty search (`difficulty=2`) and forges a new block. | `200 OK` |
| `GET` | `/chain` | Returns the complete immutable blockchain ledger and height. | `200 OK` |
| `GET` | `/chain/verify` | Validates hash-linking and cryptographic integrity across the entire chain. | `200 OK` |
| `GET` | `/explorer` | Human-readable HTML web explorer displaying live wallets, receipts, and blocks. | `200 OK` |

---

## 4. Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Londa-mas/Blockchain-Assignment-9.git](https://github.com/Londa-mas/Blockchain-Assignment-9.git)
   cd Blockchain-Assignment-9
   ```
2. Install dependencies using `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

---

## 5. Running the Application & Reproducible Demo

1. Start the local server:
   ```bash
   python app.py
   ```
2. Run the automated demo script (in a separate terminal):
   ```bash
   python capstone_demo.py
   ```

---

## 6. Reproducible Demo Lifecycle
The automated demo script executes and verifies the following sequence:

1. **Wallet Inspection:** Displays initial fiat and mZAR balances.
2. **On-Ramp:** Sender converts 1,000 local fiat units into 1,000 mZAR.
3. **Transfer:** Sender transfers 750 mZAR to Recipient.
4. **Mining:** Forges a new block containing the transfer transaction via Proof-of-Work.
5. **Off-Ramp:** Recipient redeems 750 mZAR back into local fiat.
6. **Verification & Lookup:** Confirms global chain integrity (chain_valid: True) and successfully queries the transaction hash via /transactions/lookup.
7. **Negative Testing:** Submits an invalid transfer (insufficient balance / bad signature) and verifies proper rejection (HTTP 400). 
