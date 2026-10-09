import sys
sys.path.insert(0, '/tmp/sentinel_backup')

from web3 import Web3
from eth_account import Account
from tools.eip7702_encoder import create_authorization, sign_eip7702_transaction

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Authority = account #0 (владелец EOA, которую делегируем)
authority_pk = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
authority = Account.from_key(authority_pk).address

# Sender = account #1 (кто платит газ и отправляет tx)
sender_pk = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
sender = Account.from_key(sender_pk).address

print(f"Authority (delегируемая EOA): {authority}")
print(f"Sender (платит газ): {sender}")

print(f"Code before: {w3.eth.get_code(authority).hex()}")

# Auth со стороны authority, nonce = текущий nonce authority
auth_nonce = w3.eth.get_transaction_count(authority)
auth = create_authorization(31337, "0xC000000000000000000000000000000000000000", auth_nonce, authority_pk)
print(f"Auth: chain={auth[0]}, nonce={auth[2]}, y={auth[3]}")

# TX со стороны sender
sender_nonce = w3.eth.get_transaction_count(sender)
print(f"Sender nonce: {sender_nonce}")

tx_dict = {
    'chainId': 31337,
    'nonce': sender_nonce,
    'maxPriorityFeePerGas': 2 * 10**9,
    'maxFeePerGas': 20 * 10**9,
    'gas': 500000,
    'to': sender,  # any address
    'value': 0,
    'data': b'',
    'authorizationList': [auth],
}

raw = sign_eip7702_transaction(tx_dict, sender_pk)
print(f"Raw hex first 60: 0x{raw.hex()[:60]}")

tx_hash = w3.eth.send_raw_transaction(raw)
print(f"TX hash: {tx_hash.hex()}")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=10)
print(f"Status: {receipt.status}")

code = w3.eth.get_code(authority)
print(f"Code after on authority: {code.hex()}")
if code.hex().startswith('0xef0100'):
    print("SUCCESS - delegation applied")
else:
    print("FAIL")
