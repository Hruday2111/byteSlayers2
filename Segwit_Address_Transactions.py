from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import Decimal
import os

# Load RPC credentials from cookie file
cookie_path = os.path.expandvars(r"%APPDATA%\Bitcoin\regtest\.cookie")
with open(cookie_path, "r") as f:
    rpc_user, rpc_password = f.read().strip().split(":")

rpc_host = "127.0.0.1"
rpc_port = "18443"

# ---- CONNECT TO BITCOIN DAEMON ----
wallet_name = "Byteshru"
rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")

# ---- CREATE OR LOAD WALLET ----
try:
    rpc_connection.createwallet(wallet_name)
    print(f"✅ Created new wallet: {wallet_name}")
except JSONRPCException as e:
    if "already exists" in str(e):
        print(f"⚠ Wallet '{wallet_name}' already exists. Loading it...")
        rpc_connection.loadwallet(wallet_name)
    else:
        print(f"❌ Error: {e}")
        exit(1)

# Switch to wallet connection
rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}/wallet/{wallet_name}")

# ---- GENERATE ADDRESSES ----
# Legacy (P2PKH)
addr_a = rpc_connection.getnewaddress("Address A", "legacy")
addr_b = rpc_connection.getnewaddress("Address B", "legacy")
addr_c = rpc_connection.getnewaddress("Address C", "legacy")

# SegWit (P2SH-P2WPKH)
addr_a_segwit = rpc_connection.getnewaddress("Address A SegWit", "p2sh-segwit")
addr_b_segwit = rpc_connection.getnewaddress("Address B SegWit", "p2sh-segwit")
addr_c_segwit = rpc_connection.getnewaddress("Address C SegWit", "p2sh-segwit")

print(f"🏦 Legacy Address A: {addr_a}")
print(f"🏦 Legacy Address B: {addr_b}")
print(f"🏦 Legacy Address C: {addr_c}")
print(f"🏦 SegWit Address A': {addr_a_segwit}")
print(f"🏦 SegWit Address B': {addr_b_segwit}")
print(f"🏦 SegWit Address C': {addr_c_segwit}")

# ---- MINE INITIAL BLOCKS ----
blockchain_info = rpc_connection.getblockchaininfo()
if blockchain_info["chain"] == "regtest":
    mining_address = rpc_connection.getnewaddress("Mining Address", "legacy")
    rpc_connection.generatetoaddress(101, mining_address)  # Reduced from 101 to 50
    print(f"⛏ Mined 50 blocks to: {mining_address}")

# ---- FUNDING LEGACY ADDRESS A ----
funding_amount = Decimal("1.0")  # BTC
txid_fund = rpc_connection.sendtoaddress(addr_a, float(funding_amount))
print(f"💰 Funded Address A with {funding_amount} BTC. TXID: {txid_fund}")

# Mine a block to confirm funding
rpc_connection.generatetoaddress(1, mining_address)
print("✅ Mined 1 block to confirm funding transaction.")

# ---- TRANSACTION A → B & A ----
unspent_a = rpc_connection.listunspent(1, 9999999, [addr_a])
utxo_a = unspent_a[0]
transaction_fee = Decimal("0.0001")

# Split funds: 70% to B, 30% back to A
remaining_amount_a = utxo_a["amount"] - transaction_fee
amount_to_send_b = remaining_amount_a * Decimal("0.7")
amount_to_send_a = remaining_amount_a * Decimal("0.3")

# Create raw transaction
raw_tx_a = rpc_connection.createrawtransaction(
    [{"txid": utxo_a["txid"], "vout": utxo_a["vout"]}],
    {addr_b: float(amount_to_send_b), addr_a: float(amount_to_send_a)}
)

# Sign & Broadcast
signed_tx_a = rpc_connection.signrawtransactionwithwallet(raw_tx_a)
txid_a_to_b = rpc_connection.sendrawtransaction(signed_tx_a["hex"])
print(f"📢 Transaction A → B & A broadcasted. TXID: {txid_a_to_b}")

# Mine block to confirm transaction
rpc_connection.generatetoaddress(1, mining_address)
print("✅ Mined 1 block to confirm A → B & A transaction.")

# ---- TRANSACTION B → C & B ----
unspent_b = rpc_connection.listunspent(1, 9999999, [addr_b])
utxo_b = unspent_b[0]

# Split funds: 50% to C, 50% back to B
remaining_amount_b = utxo_b["amount"] - transaction_fee
amount_to_send_c = remaining_amount_b * Decimal("0.5")
amount_to_send_b = remaining_amount_b * Decimal("0.5")

# Create raw transaction
raw_tx_b = rpc_connection.createrawtransaction(
    [{"txid": utxo_b["txid"], "vout": utxo_b["vout"]}],
    {addr_c: float(amount_to_send_c), addr_b: float(amount_to_send_b)}
)

# Sign & Broadcast
signed_tx_b = rpc_connection.signrawtransactionwithwallet(raw_tx_b)
txid_b_to_c = rpc_connection.sendrawtransaction(signed_tx_b["hex"])
print(f"📢 Transaction B → C & B broadcasted. TXID: {txid_b_to_c}")

# Mine block to confirm transaction
rpc_connection.generatetoaddress(1, mining_address)
print("✅ Mined 1 block to confirm B → C & B transaction.")

# ---- FUNDING SEGWIT ADDRESS A' ----
txid_fund_segwit = rpc_connection.sendtoaddress(addr_a_segwit, float(funding_amount))
print(f"💰 Funded SegWit Address A' with {funding_amount} BTC. TXID: {txid_fund_segwit}")

# Mine a block to confirm funding
rpc_connection.generatetoaddress(1, mining_address)
print("✅ Mined 1 block to confirm SegWit funding transaction.")

# ---- TRANSACTION A' → B' & A' ----
unspent_a_segwit = rpc_connection.listunspent(1, 9999999, [addr_a_segwit])
utxo_a_segwit = unspent_a_segwit[0]

# Split funds: 70% to B', 30% back to A'
remaining_amount_a_segwit = utxo_a_segwit["amount"] - transaction_fee
amount_to_send_b_segwit = remaining_amount_a_segwit * Decimal("0.7")
amount_to_send_a_segwit = remaining_amount_a_segwit * Decimal("0.3")

# Create raw transaction
raw_tx_a_segwit = rpc_connection.createrawtransaction(
    [{"txid": utxo_a_segwit["txid"], "vout": utxo_a_segwit["vout"]}],
    {addr_b_segwit: float(amount_to_send_b_segwit), addr_a_segwit: float(amount_to_send_a_segwit)}
)

# Sign & Broadcast
signed_tx_a_segwit = rpc_connection.signrawtransactionwithwallet(raw_tx_a_segwit)
txid_a_to_b_segwit = rpc_connection.sendrawtransaction(signed_tx_a_segwit["hex"])
print(f"📢 SegWit Transaction A' → B' & A' broadcasted. TXID: {txid_a_to_b_segwit}")

# Mine block to confirm transaction
rpc_connection.generatetoaddress(1, mining_address)
print("✅ Mined 1 block to confirm A' → B' & A' transaction.")

# ---- SAVE TRANSACTION DETAILS ----
save_path = os.path.expanduser("~/Documents/Complete_transaction_details.txt")
with open(save_path, "w") as f:
    f.write(f"TXID_A_TO_B={txid_a_to_b}\nTXID_B_TO_C={txid_b_to_c}\n")
    f.write(f"TXID_A'_TO_B'={txid_a_to_b_segwit}\nADDR_A={addr_a}\nADDR_A'={addr_a_segwit}\n")

print(f"\n✅ Transaction details saved to: {save_path}")
print("\n🎉 All Legacy & SegWit Transactions Completed Successfully!")