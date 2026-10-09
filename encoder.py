import rlp
from eth_utils import to_bytes, keccak, to_checksum_address
from eth_account import Account

class EIP7702Encoder:
    def __init__(self, chain_id, nonce, max_priority_fee, max_fee, gas_limit, to, value, data, auth_list):
        self.fields = [
            chain_id, nonce, max_priority_fee, max_fee, gas_limit,
            to_bytes(hexstr=to) if to else b'', 
            value, data, [], auth_list
        ]

    def get_message_to_sign(self):
        # Хеш для подписи самой транзакции: keccak(0x04 || rlp([fields]))
        return keccak(b'\x04' + rlp.encode(self.fields))

def create_authorization(chain_id, contract_address, nonce, private_key):
    # EIP-7702 Auth List item RLP
    auth_fields = [chain_id, to_bytes(hexstr=contract_address), nonce]
    auth_hash = keccak(b'\x05' + rlp.encode(auth_fields))
    
    account = Account.from_key(private_key)
    sig = account._key_obj.sign_msg_hash(auth_hash)
    
    # Формат для authorization_list: [chain_id, address, nonce, y_parity, r, s]
    return [chain_id, to_bytes(hexstr=contract_address), nonce, sig.v, sig.r, sig.s]

def sign_eip7702_transaction(tx_dict, private_key):
    encoder = EIP7702Encoder(
        tx_dict['chainId'], tx_dict['nonce'], 
        tx_dict['maxPriorityFeePerGas'], tx_dict['maxFeePerGas'],
        tx_dict['gas'], tx_dict['to'], tx_dict['value'], 
        tx_dict.get('data', b''), tx_dict['authorizationList']
    )
    
    tx_hash = encoder.get_message_to_sign()
    account = Account.from_key(private_key)
    sig = account._key_obj.sign_msg_hash(tx_hash)
    
    # Собираем финальный список полей с подписью
    # В Type 4 'v' — это y_parity (0 или 1)
    final_fields = encoder.fields + [sig.v, sig.r, sig.s]
    
    # Возвращаем 0x04 + RLP
    return b'\x04' + rlp.encode(final_fields)
