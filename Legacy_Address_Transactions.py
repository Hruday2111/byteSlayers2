from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import Decimal
import os
import time

# Load RPC credentials from cookie file
cookie_path = os.path.expandvars(r"%APPDATA%\Bitcoin\regtest\.cookie")
with open(cookie_path, "r") as f:
    rpc_user, rpc_password = f.read().strip().split(":")

rpc_host = "127.0.0.1"
rpc_port = "18443"

# Connect to Bitcoin daemon
wallet_name = "Byteshru"
rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")

# Create or load wallet
try:
    rpc_connection.createwallet(wallet_name)
    print(f"✅ Created new wallet: {wallet_name}")
except JSONRPCException as e:
    if "already exists" in str(e):
        print(f"⚠ Wallet '{wallet_name}' already exists. Loading it...")
        try:
            rpc_connection.loadwallet(wallet_name)
        except JSONRPCException as e:
            if "already loaded" in str(e):
                print("⚠ Wallet is already loaded, continuing...")
            else:
                print(f"❌ Error: {e}")
                exit(1)

# Reconnect to wallet
rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}/wallet/{wallet_name}")

# Generate three legacy addresses
addr_a = rpc_connection.getnewaddress("Address A", "legacy")
addr_b = rpc_connection.getnewaddress("Address B", "legacy")
addr_c = rpc_connection.getnewaddress("Address C", "legacy")

print(f"🏦 Address A: {addr_a}")
print(f"🏦 Address B: {addr_b}")
print(f"🏦 Address C: {addr_c}")

# Mine blocks if in regtest mode
blockchain_info = rpc_connection.getblockchaininfo()
if blockchain_info["chain"] == "regtest":
    mining_address = rpc_connection.getnewaddress("Mining Address", "legacy")
    rpc_connection.generatetoaddress(101, mining_address)  # Increased blocks to 101
    print(f"⛏ Mined 101 blocks to: {mining_address}")

# Check wallet balance before funding Address A
wallet_balance = rpc_connection.getbalance()
print(f"💰 Wallet balance: {wallet_balance} BTC")

funding_amount = Decimal("1.0")

if wallet_balance < funding_amount:
    print("⚠ Not enough balance! Mining additional blocks...")
    rpc_connection.generatetoaddress(20, mining_address)  # Mine extra blocks if needed
    time.sleep(2)  # Wait for blocks to be processed
    wallet_balance = rpc_connection.getbalance()
    print(f"✅ Updated wallet balance: {wallet_balance} BTC")

# Ensure balance is now sufficient
if wallet_balance < funding_amount:
    print("❌ Still not enough funds! Please mine more blocks manually.")
    exit(1)

# Fund Address A with 1 BTC
txid_fund = rpc_connection.sendtoaddress(addr_a, float(funding_amount))
print(f"💰 Funded Address A with {funding_amount} BTC. TXID: {txid_fund}")

# Mine a block to confirm funding
rpc_connection.generatetoaddress(1, mining_address)
print("✅ Mined 1 block to confirm funding transaction.")

# Get UTXOs for Address A
unspent_a = rpc_connection.listunspent(1, 9999999, [addr_a])
if not unspent_a:
    print("❌ No UTXOs found for Address A! Mining more blocks...")
    rpc_connection.generatetoaddress(2, mining_address)
    unspent_a = rpc_connection.listunspent(1, 9999999, [addr_a])

# Select UTXO from Address A
utxo_a = unspent_a[0]
print(f"🔎 Using UTXO: {utxo_a['txid']} with amount {utxo_a['amount']} BTC")

# Define transaction fee
transaction_fee = Decimal("0.0001")

# Calculate amount distribution
remaining_amount_a = utxo_a["amount"] - transaction_fee
amount_to_send_b = remaining_amount_a * Decimal("0.7")
amount_to_send_a = remaining_amount_a * Decimal("0.3")

# Create raw transaction A → B & A
raw_tx_a = rpc_connection.createrawtransaction(
    [{"txid": utxo_a["txid"], "vout": utxo_a["vout"]}],
    {addr_b: float(amount_to_send_b), addr_a: float(amount_to_send_a)}
)

# Sign and broadcast transaction
signed_tx_a = rpc_connection.signrawtransactionwithwallet(raw_tx_a)
txid_a_to_b = rpc_connection.sendrawtransaction(signed_tx_a["hex"])
print(f"📢 Transaction A → B & A broadcasted. TXID: {txid_a_to_b}")

# Decode transaction A → B
decoded_tx_a_to_b = rpc_connection.decoderawtransaction(signed_tx_a["hex"])
print(f"📜 Decoded Transaction A → B: {decoded_tx_a_to_b}")

# Mine block to confirm transaction
rpc_connection.generatetoaddress(1, mining_address)
print("✅ Mined 1 block to confirm A → B & A transaction.")

# Get UTXOs for Address B
unspent_b = rpc_connection.listunspent(1, 9999999, [addr_b])
if not unspent_b:
    print("❌ No UTXOs found for Address B! Mining another block...")
    rpc_connection.generatetoaddress(1, mining_address)
    unspent_b = rpc_connection.listunspent(1, 9999999, [addr_b])

# Select UTXO from Address B
utxo_b = unspent_b[0]
print(f"🔎 Using UTXO: {utxo_b['txid']} with amount {utxo_b['amount']} BTC")

# Calculate amount distribution for B → C & B
remaining_amount_b = utxo_b["amount"] - transaction_fee
amount_to_send_c = remaining_amount_b * Decimal("0.5")
amount_to_send_b = remaining_amount_b * Decimal("0.5")

# Create raw transaction B → C & B
raw_tx_b = rpc_connection.createrawtransaction(
    [{"txid": utxo_b["txid"], "vout": utxo_b["vout"]}],
    {addr_c: float(amount_to_send_c), addr_b: float(amount_to_send_b)}
)

# Sign and broadcast transaction
signed_tx_b = rpc_connection.signrawtransactionwithwallet(raw_tx_b)
txid_b_to_c = rpc_connection.sendrawtransaction(signed_tx_b["hex"])
print(f"📢 Transaction B → C & B broadcasted. TXID: {txid_b_to_c}")

# Decode transaction B → C
decoded_tx_b_to_c = rpc_connection.decoderawtransaction(signed_tx_b["hex"])
print(f"📜 Decoded Transaction B → C: {decoded_tx_b_to_c}")

# Mine block to confirm transaction
rpc_connection.generatetoaddress(1, mining_address)
print("✅ Mined 1 block to confirm B → C & B transaction.")

# Save transaction details to a writable location
save_path = os.path.expanduser("~/Documents/Complete_transaction_details.txt")
with open(save_path, "w") as f:
    f.write(f"TXID_A_TO_B={txid_a_to_b}\n")
    f.write(f"TXID_B_TO_C={txid_b_to_c}\n")
    f.write(f"ADDR_A={addr_a}\n")
    f.write(f"ADDR_B={addr_b}\n")
    f.write(f"ADDR_C={addr_c}\n")

print(f"\n✅ Transaction details saved to: {save_path}")
print("\n🎉 Transactions A → B & A and B → C & B completed successfully!")