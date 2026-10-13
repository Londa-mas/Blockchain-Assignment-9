"""
Automated checks for the mZAR remittance prototype.
Run with:  python tests.py

Tests marked @unittest.expectedFailure document KNOWN LIMITATIONS of the current
prototype (see report section f). They are expected to fail and are reported as
"expected failure", not as errors. If one of them ever passes, unittest reports
an "unexpected success", meaning that limitation has been fixed.
"""
import time
import importlib
import unittest
from ecdsa import SigningKey, SECP256k1
import app as app_module
from wallet import Wallet, canonical_tx_payload


class RemittanceTests(unittest.TestCase):
    def setUp(self):
        importlib.reload(app_module)                     # fresh chain and wallets for every test
        self.bc = app_module.blockchain
        self.client = app_module.app.test_client()
        wallets = self.client.get('/wallets').get_json()
        self.pubkey = wallets['Sender']['public_key']
        self.sender = Wallet(SigningKey.from_string(
            bytes.fromhex(wallets['Sender']['private_key']), curve=SECP256k1))
        self.client.post('/remittance/onramp', json={'wallet_id': 'Sender', 'amount': 1000.0})

    def signed_tx(self, amount):
        ts = time.time()
        sig = self.sender.sign(canonical_tx_payload('Sender', 'Recipient', amount, ts))
        return {'sender': 'Sender', 'recipient': 'Recipient', 'amount': amount,
                'timestamp': ts, 'public_key': self.pubkey, 'signature': sig}

    # ---------- Features that work ----------
    def test_onramp_is_fully_backed(self):
        status = self.client.get('/reserve/status').get_json()
        self.assertEqual(status['circulating_mzar'], 1000.0)
        self.assertTrue(status['fully_backed'])

    def test_reserve_fully_backed_after_offramp(self):
        self.client.post('/transactions/new', json=self.signed_tx(750.0))
        self.client.post('/remittance/offramp', json={'wallet_id': 'Recipient', 'amount': 750.0})
        status = self.client.get('/reserve/status').get_json()
        self.assertEqual(status['circulating_mzar'], 250.0)
        self.assertTrue(status['fully_backed'])

    def test_valid_signature_accepted(self):
        self.assertEqual(self.client.post('/transactions/new', json=self.signed_tx(10.0)).status_code, 201)

    def test_bad_signature_rejected(self):
        tx = self.signed_tx(10.0)
        tx['signature'] = 'deadbeef' * 16
        self.assertEqual(self.client.post('/transactions/new', json=tx).status_code, 400)

    def test_amount_changed_after_signing_rejected(self):
        tx = self.signed_tx(10.0)
        tx['amount'] = 900.0
        self.assertEqual(self.client.post('/transactions/new', json=tx).status_code, 400)

    def test_insufficient_balance_rejected(self):
        self.assertEqual(self.client.post('/transactions/new', json=self.signed_tx(99999.0)).status_code, 400)

    def test_mined_transaction_has_id_and_chain_verifies(self):
        self.client.post('/transactions/new', json=self.signed_tx(750.0))
        block = self.client.post('/mine').get_json()
        self.assertEqual(len(block['transactions'][0]['tx_id']), 64)
        self.assertTrue(self.client.get('/chain/verify').get_json()['chain_valid'])

    def test_lookup_finds_mined_transfer(self):
        self.client.post('/transactions/new', json=self.signed_tx(750.0))
        self.client.post('/mine')
        res = self.client.post('/transactions/lookup', json={'sender': 'Sender', 'amount': 750.0})
        self.assertEqual(res.status_code, 200)

    # ---------- Known limitations (report section f) ----------
    @unittest.expectedFailure
    def test_limitation_private_keys_not_exposed(self):
        self.assertNotIn('private_key', str(self.client.get('/wallets').get_json()))

    @unittest.expectedFailure
    def test_limitation_replay_rejected(self):
        tx = self.signed_tx(10.0)
        self.client.post('/transactions/new', json=tx)
        self.assertEqual(self.client.post('/transactions/new', json=tx).status_code, 400)

    @unittest.expectedFailure
    def test_limitation_tampered_block_detected_after_rehash(self):
        self.client.post('/transactions/new', json=self.signed_tx(750.0))
        self.client.post('/mine')
        block = self.bc.chain[-1]
        block['transactions'][0]['amount'] = 1.0
        block['hash'] = self.bc.hash({k: v for k, v in block.items() if k != 'hash'})
        self.assertFalse(self.bc.verify_chain())


if __name__ == '__main__':
    unittest.main(verbosity=2)
