# Findings - EIP-7702 in Browser Extension Wallets

Date: October 2026
Scope: MetaMask Extension 13.47.0, Trust Wallet Extension, Rabby Extension
Chain: Anvil local fork (--hardfork prague, --chain-id 31337)

## Methodology

All tests use a locally-controlled Anvil node and a controlled dApp page (wallet_harness.html) served over HTTP to the browser. The dApp has no access to the user's private key and can only interact via the injected window.ethereum provider.

The controlled victim is Anvil account #0 (0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266) with a publicly known key. This is intentional - it removes "did the attacker have the key?" as a variable. All delegation attempts use this address as authority.

## Test 1 - eth_sendTransaction with authorizationList

What the dApp requests:

const tx = {
  from: victimEOA,
  to: victimEOA,
  value: '0x0',
  gas: '0x7a120',
  type: '0x4',
  authorizationList: [],
};
await window.ethereum.request({
  method: 'eth_sendTransaction',
  params: [tx],
});

Results:

MetaMask Extension 13.47.0:
Error: External EIP-7702 transactions are not supported
Explicit refusal. MetaMask recognizes type-4 and rejects it from dApps. Consistent with their "Added Protection" feature shipped in September 2026.

Trust Wallet Extension:
- No error surfaced to the dApp.
- On-chain receipt: type: 0, gasUsed: 21000, code: 0x.
- The wallet silently downgraded type-4 to type-0 and stripped authorizationList.
- No delegation applied, no funds lost. But no user-visible indication that the transaction was modified.

This is safe degradation, not a vulnerability. The user gets the same simple transfer they would have gotten without 7702 fields.

Rabby Extension:
Not tested for eth_sendTransaction type-4 directly (skipped in favor of eth_sign and wallet_signAuthorization).

## Test 2 - eth_sign on a valid authorization hash

What the dApp requests:

The dApp computes the EIP-7702 authorization hash locally:
auth_hash = keccak256(0x05 || rlp([chain_id, address, nonce]))

Then requests a signature on it:
await window.ethereum.request({
  method: 'eth_sign',
  params: [victimEOA, authHash],
});

If the wallet signs this without warning, the dApp can package the signature into a type-4 transaction and apply delegation.

Results:

Rabby Extension:
1. First shows a dialog: "Signing with 'eth_sign' can lead to loss of assets. For your safety, Rabby does not support this method."
2. If the user dismisses that and proceeds, the confirmation screen shows: "Unknown signature type" with the raw hex.

This is correct behavior. Rabby flags both the method (eth_sign) and the payload (unknown type). No bounty is warranted here - the wallet did its job.

MetaMask Extension 13.47.0:
Known to show a warning on eth_sign in recent versions. Not exhaustively tested for this specific scenario.

## Test 3 - wallet_signAuthorization (EIP-7702 RPC method)

What the dApp requests:

await window.ethereum.request({
  method: 'wallet_signAuthorization',
  params: [{
    contractAddress: '0xC000000000000000000000000000000000000000',
    chainId: '0x7a69',
    nonce: '0x0'
  }]
});

Results:

Rabby Extension:
{ "code": -32601, "message": "method [wallet_signAuthorization] doesn't has corresponding handler" }

MetaMask Extension 13.47.0:
{ "code": -32601, "message": "method [wallet_signAuthorization] doesn't has corresponding handler" }

Conclusion: Neither extension exposes the RPC method required for a dApp to obtain a valid authorization. This is the critical blocker for the entire attack class on extension wallets.

## Side Finding - ZeroDev SDK (informational, not exploitable today)

While auditing AA SDKs that assume wallet_signAuthorization is available, we noticed that the ZeroDev SDK accepts accountImplementationAddress and factoryAddress as parameters without validating them against a whitelist.

File: packages/core/accounts/kernel/createKernelAccount.ts
Lines: 135-137 (type declarations), 367-371 (runtime resolve)

Code:
// 135-137
factoryAddress?: Address
accountImplementationAddress?: Address

// 367-371
accountImplementationAddress:
    accountImplementationAddress ?? addresses.accountImplementationAddress,
factoryAddress: factoryAddress ?? addresses.factoryAddress,

Why this is not currently exploitable:
- ZeroDev SDK cannot sign authorizations itself - it must call wallet_signAuthorization on the user's wallet.
- No extension wallet currently implements this method.
- Therefore a malicious dApp cannot deliver a valid authorization to the SDK.

Why it matters for the future:
- When a wallet adds wallet_signAuthorization support, this code path becomes reachable.
- If the wallet UI shows the delegate address to the user (as it should), the SDK's parameter is still safe.
- If the wallet UI does not show the delegate address, the SDK parameter becomes a vulnerability.

Recommendation to ZeroDev: add an allowlist of known implementation addresses, or require the dApp to explicitly pass the address in a way that forces the wallet UI to display it.

## Responsible Disclosure Timeline

- 2026-10-08 - Testing performed locally. No live systems targeted.
- 2026-10-09 - Findings documented. No vendor contacted yet (all findings are negative or informational, no active vulnerabilities).

## License

MIT
