from flask import Flask, jsonify, request, render_template_string
import hashlib
import json
import time
from wallet import Wallet, canonical_tx_payload

app = Flask(__name__)

class RemittanceBlockchain:
    def __init__(self):
        self.chain = []
        self.mempool = []
        self.nodes = set()
        
        # Instantiate real cryptographic wallets using Assignment 4 logic
        self.reserve_wallet = Wallet.create()
        self.sender_wallet = Wallet.create()
        self.recipient_wallet = Wallet.create()

        self.wallets = {
            "ReserveAgent": {
                "fiat_balance": 1000000.0, 
                "mzar_balance": 0.0,
                "public_key": self.reserve_wallet.public_key_hex,
                "private_key": self.reserve_wallet.private_key_hex,
                "address": self.reserve_wallet.address
            },
            "Sender": {
                "fiat_balance": 5000.0, 
                "mzar_balance": 0.0,
                "public_key": self.sender_wallet.public_key_hex,
                "private_key": self.sender_wallet.private_key_hex,
                "address": self.sender_wallet.address
            },
            "Recipient": {
                "fiat_balance": 0.0, 
                "mzar_balance": 0.0,
                "public_key": self.recipient_wallet.public_key_hex,
                "private_key": self.recipient_wallet.private_key_hex,
                "address": self.recipient_wallet.address
            }
        }
        self.receipts = []
        # Create genesis block
        self.new_block(previous_hash="0" * 64, nonce=0)

    def total_mzar_supply(self) -> float:
        """Calculates total mZAR currently in circulation across all non-reserve wallets."""
        return sum(w['mzar_balance'] for name, w in self.wallets.items() if name != "ReserveAgent")

    def new_block(self, previous_hash, nonce):
        block = {
            'index': len(self.chain),
            'timestamp': time.time(),
            'transactions': self.mempool,
            'nonce': nonce,
            'previous_hash': previous_hash or (self.chain[-1]['hash'] if self.chain else "0" * 64)
        }
        block['hash'] = self.hash(block)
        self.mempool = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount, signature, timestamp):
        tx_data = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': timestamp
        }
        # Generate unique cryptographic transaction ID hash (Rubric g)
        tx_id = hashlib.sha256(json.dumps(tx_data, sort_keys=True).encode()).hexdigest()
        tx = {
            'tx_id': tx_id,
            **tx_data,
            'signature': signature
        }
        self.mempool.append(tx)
        return len(self.chain)

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_block, difficulty=2):
        last_hash = self.hash(last_block)
        nonce = 0
        target = "0" * difficulty
        while True:
            guess = f"{last_hash}{nonce}".encode()
            guess_hash = hashlib.sha256(guess).hexdigest()
            if guess_hash.startswith(target):
                return nonce
            nonce += 1

    def verify_chain(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block['previous_hash'] != previous_block['hash']:
                return False

            block_copy = current_block.copy()
            current_hash = block_copy.pop('hash')
            if self.hash(block_copy) != current_hash:
                return False
        return True

blockchain = RemittanceBlockchain()

@app.route('/wallets', methods=['GET'])
def get_wallets():
    return jsonify(blockchain.wallets), 200

@app.route('/receipts', methods=['GET'])
def get_receipts():
    return jsonify(blockchain.receipts), 200

@app.route('/reserve/status', methods=['GET'])
def reserve_status():
    circulating = blockchain.total_mzar_supply()
    reserve_fiat = blockchain.wallets["ReserveAgent"]["fiat_balance"]
    backing_collateral = reserve_fiat - 1000000.0  # Baseline initial capital
    is_fully_backed = (circulating == backing_collateral)
    
    return jsonify({
        'circulating_mzar': circulating,
        'reserve_fiat_held': reserve_fiat,
        'backing_collateral': backing_collateral,
        'fully_backed': is_fully_backed
    }), 200

@app.route('/remittance/onramp', methods=['POST'])
def onramp():
    data = request.get_json()
    wallet_id = data.get('wallet_id')
    amount = float(data.get('amount', 0))

    if wallet_id not in blockchain.wallets or wallet_id == "ReserveAgent":
        return jsonify({'error': 'Invalid wallet ID for on-ramp'}), 400

    if blockchain.wallets[wallet_id]['fiat_balance'] < amount:
        return jsonify({'error': 'Insufficient local fiat balance for on-ramp'}), 400

    # 1:1 Reserve Rule Enforced: Debit user fiat, lock into Reserve Agent pool, credit mZAR
    blockchain.wallets[wallet_id]['fiat_balance'] -= amount
    blockchain.wallets["ReserveAgent"]["fiat_balance"] += amount
    blockchain.wallets[wallet_id]['mzar_balance'] += amount

    receipt = {
        'type': 'ON-RAMP',
        'wallet': wallet_id,
        'fiat_debited': amount,
        'mzar_credited': amount,
        'timestamp': time.time()
    }
    receipt['receipt_id'] = hashlib.sha256(json.dumps(receipt, sort_keys=True).encode()).hexdigest()
    blockchain.receipts.append(receipt)
    return jsonify({'message': f'Successfully on-ramped {amount} mZAR under 1:1 reserve rule', 'receipt': receipt}), 200

@app.route('/remittance/offramp', methods=['POST'])
def offramp():
    data = request.get_json()
    wallet_id = data.get('wallet_id')
    amount = float(data.get('amount', 0))

    if wallet_id not in blockchain.wallets or wallet_id == "ReserveAgent":
        return jsonify({'error': 'Invalid wallet ID for off-ramp'}), 400

    if blockchain.wallets[wallet_id]['mzar_balance'] < amount:
        return jsonify({'error': 'Insufficient mZAR balance for off-ramp'}), 400

    # Verify reserve holds enough collateral backing
    reserve_fiat_held = blockchain.wallets["ReserveAgent"]["fiat_balance"]
    if (reserve_fiat_held - 1000000.0) < amount:
        return jsonify({'error': 'Rejected: Reserve agent collateral deficit'}), 400

    # Burn mZAR, release fiat from Reserve Agent back to user
    blockchain.wallets[wallet_id]['mzar_balance'] -= amount
    blockchain.wallets["ReserveAgent"]["fiat_balance"] -= amount
    blockchain.wallets[wallet_id]['fiat_balance'] += amount

    receipt = {
        'type': 'OFF-RAMP',
        'wallet': wallet_id,
        'mzar_debited': amount,
        'fiat_credited': amount,
        'timestamp': time.time()
    }
    receipt['receipt_id'] = hashlib.sha256(json.dumps(receipt, sort_keys=True).encode()).hexdigest()
    blockchain.receipts.append(receipt)
    return jsonify({'message': f'Successfully off-ramped {amount} mZAR to local fiat', 'receipt': receipt}), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    data = request.get_json()
    required = ['sender', 'recipient', 'amount', 'signature', 'timestamp', 'public_key']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing transaction values'}), 400

    sender = data['sender']
    recipient = data['recipient']
    amount = float(data['amount'])
    signature = data['signature']
    timestamp = float(data['timestamp'])
    public_key = data['public_key']

    if sender not in blockchain.wallets or recipient not in blockchain.wallets:
        return jsonify({'error': 'Sender or recipient wallet not found'}), 400

    if public_key != blockchain.wallets[sender]['public_key']:
        return jsonify({'error': 'Rejected: Public key mismatch for sender'}), 400

    payload_bytes = canonical_tx_payload(sender, recipient, amount, timestamp)
    if not Wallet.verify(payload_bytes, signature, public_key):
        return jsonify({'error': 'Rejected: Invalid cryptographic signature'}), 400

    if blockchain.wallets[sender]['mzar_balance'] < amount:
        return jsonify({'error': 'Rejected: Insufficient mZAR balance for transfer'}), 400

    blockchain.wallets[sender]['mzar_balance'] -= amount
    blockchain.wallets[recipient]['mzar_balance'] += amount

    index = blockchain.new_transaction(sender, recipient, amount, signature, timestamp)
    return jsonify({'message': f'Transaction validated and queued for Block {index}'}), 201

@app.route('/transactions/lookup', methods=['POST'])
def lookup_transaction():
    data = request.get_json()
    sender = data.get('sender')
    amount = data.get('amount')

    found_blocks = []
    for block in blockchain.chain:
        for tx in block['transactions']:
            if tx.get('sender') == sender and tx.get('amount') == amount:
                found_blocks.append({
                    'block_index': block['index'],
                    'block_hash': block['hash'],
                    'transaction': tx
                })

    if found_blocks:
        return jsonify({'status': 'Found', 'matches': found_blocks}), 200
    return jsonify({'status': 'Not Found', 'message': 'Transaction not found in mined blocks'}), 404

@app.route('/mine', methods=['POST'])
def mine():
    last_block = blockchain.last_block
    nonce = blockchain.proof_of_work(last_block, difficulty=2)
    block = blockchain.new_block(previous_hash=None, nonce=nonce)
    return jsonify({
        'message': 'New Remittance Block Forged',
        'index': block['index'],
        'hash': block['hash'],
        'transactions': block['transactions']
    }), 200

@app.route('/chain/verify', methods=['GET'])
def verify_chain_route():
    is_valid = blockchain.verify_chain()
    return jsonify({'chain_valid': is_valid}), 200

@app.route('/explorer', methods=['GET'])
def explorer():
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>African Remittance Prototype Explorer</title></head>
    <body style="font-family: Arial; margin: 40px;">
        <h1>mZAR Remittance Explorer</h1>
        <hr>
        <h2>Wallets & Balances</h2>
        <pre>{{ wallets | tojson(indent=2) }}</pre>
        <h2>Off-Ramp / On-Ramp Receipts</h2>
        <pre>{{ receipts | tojson(indent=2) }}</pre>
        <h2>Blockchain Ledger</h2>
        <pre>{{ chain | tojson(indent=2) }}</pre>
    </body>
    </html>
    """
    return render_template_string(html, wallets=blockchain.wallets, receipts=blockchain.receipts, chain=blockchain.chain)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)