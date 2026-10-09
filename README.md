# EIP-7702 Wallet Research

Negative finding + methodology from testing three popular browser extension wallets against EIP-7702 (Pectra) attack surface.

**Date:** October 2026
**Status:** All tested extension wallets are protected. Full methodology and reproduction harness included.

## Summary

We tested three extension wallets against EIP-7702 (EIP-7702 authorization / type-4 transactions) across three attack vectors:

| Wallet | `eth_sendTransaction` type-4 | `eth_sign` on auth hash | `wallet_signAuthorization` |
|---|---|---|---|
| MetaMask Extension 13.47.0 | Explicit refusal: `External EIP-7702 transactions are not supported` | Warning: raw hash signing | `-32601 method not found` |
| Trust Wallet Extension | Silent downgrade type-4 → type-0 (gasUsed 21000, code `0x`) | n/a | n/a |
| Rabby Extension | n/a | Warning + "Unknown signature type" | `-32601 method not found` |

**Conclusion:** No extension wallet currently exposes a viable path for a malicious dApp to obtain a valid EIP-7702 authorization from a user. All three vendors have implemented protection — through different mechanisms (refusal, degradation, warning).

See [FINDINGS.md](./FINDINGS.md) for full methodology.

## Artifacts

- **`encoder.py`** — Working EIP-7702 type-4 transaction encoder. Correct `y_parity`, correct RLP structure. Tested on Anvil with `--hardfork prague`.
- **`sponsoring_test.py`** — Sponsoring pattern test (sender ≠ authority). Verified that an attacker without the victim's key can apply delegation if a valid signature is provided.
- **`wallet_harness.html`** — HTML harness for testing how a wallet renders `authorizationList` and `eth_sign` on authorization hashes.

## How to Reproduce

Requirements:
- Foundry (`anvil`, `cast`) — v1.8.5+
- Python 3.12+, `web3`, `eth-account`, `rlp`, `eth-keys`
- Chrome with the wallet under test installed

```bash
# 1. Start Anvil
anvil --host 127.0.0.1 --port 8545 --hardfork prague --chain-id 31337

# 2. In another terminal — serve the harness
cd eip7702-wallet-research
python3 -m http.server 9999

# 3. Open http://localhost:9999/wallet_harness.html in Chrome
# 4. Open DevTools → Console
# 5. Run the RPC tests (see FINDINGS.md)
