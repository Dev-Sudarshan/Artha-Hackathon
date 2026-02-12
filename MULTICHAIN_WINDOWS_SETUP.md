# MultiChain Windows Installation Guide

## Step 1: Download MultiChain

1. Go to: https://www.multichain.com/download-install/
2. Download **MultiChain 2.3.3 for Windows** (or latest version)
3. Extract the ZIP file to a folder (e.g., `C:\MultiChain`)

## Step 2: Add to PATH (Optional but Recommended)

1. Right-click "This PC" → Properties → Advanced System Settings → Environment Variables
2. Under "System Variables", find "Path" and click Edit
3. Click "New" and add the MultiChain folder path (e.g., `C:\MultiChain`)
4. Click OK to save

## Step 3: Create Your Blockchain

Open **PowerShell as Administrator** and run:

```powershell
# Navigate to MultiChain folder (if not in PATH)
cd C:\MultiChain

# Create a new blockchain named 'artha-chain'
.\multichain-util.exe create artha-chain

# This will show you the blockchain directory location
# Usually: C:\Users\YourName\AppData\Roaming\MultiChain\artha-chain
```

## Step 4: Configure the Blockchain

Edit the configuration file:

```powershell
# Open the config file
notepad $env:APPDATA\MultiChain\artha-chain\params.dat
```

**Important settings** (verify these are set):
```
chain-protocol = multichain
chain-description = Artha P2P Lending Blockchain
root-stream-open = true
anyone-can-connect = true
anyone-can-send = true
anyone-can-receive = true
```

## Step 5: Start the MultiChain Node

```powershell
# Start the blockchain daemon
.\multichaind.exe artha-chain -daemon

# If you get an error about blockchain not initialized, use:
.\multichaind.exe artha-chain -daemon -initprivkey=[COPY KEY FROM ERROR MESSAGE]
```

**Expected output:**
```
MultiChain 2.3.3 Daemon (latest protocol 20017)

Starting up node...
Looking for genesis block...
Genesis block found
...
Node ready.
```

## Step 6: Get RPC Connection Details

```powershell
# View the RPC credentials
notepad $env:APPDATA\MultiChain\artha-chain\multichain.conf
```

You'll see something like:
```
rpcuser=multichainrpc
rpcpassword=YOUR_GENERATED_PASSWORD_HERE
rpcport=6820
```

## Step 7: Test the Connection

```powershell
.\multichain-cli.exe artha-chain getinfo
```

This should return blockchain information if everything is working.

## Step 8: Create Required Streams

```powershell
# Create the loan storage stream
.\multichain-cli.exe artha-chain create stream loan_storage '{"restrict":"write"}' true

# Create the loan repayments stream
.\multichain-cli.exe artha-chain create stream loan_repayments '{"restrict":"write"}' true

# Verify streams were created
.\multichain-cli.exe artha-chain liststreams
```

## Step 9: Update Your Backend Configuration

Create a `.env` file in your backend folder with:

```env
MULTICHAIN_HOST=127.0.0.1
MULTICHAIN_PORT=6820
MULTICHAIN_USER=multichainrpc
MULTICHAIN_PASSWORD=YOUR_PASSWORD_FROM_STEP_6
MULTICHAIN_CHAIN_NAME=artha-chain
```

## Step 10: Keep MultiChain Running

**Important**: Keep the PowerShell window open or run as a service.

To run MultiChain in the background:
```powershell
Start-Process -FilePath ".\multichaind.exe" -ArgumentList "artha-chain" -WindowStyle Hidden
```

To stop MultiChain:
```powershell
.\multichain-cli.exe artha-chain stop
```

---

## Troubleshooting

### "Port already in use"
- Check if another instance is running: `Get-Process | Where-Object {$_.ProcessName -like "*multichain*"}`
- Change the port in `multichain.conf`

### "Cannot connect to server"
- Verify multichaind is running: `Get-Process multichaind`
- Check firewall isn't blocking port 6820
- Verify credentials in `multichain.conf`

### "Permission denied"
- Run PowerShell as Administrator
- Check folder permissions in `%APPDATA%\MultiChain`

---

## Quick Start After Installation

Once set up, to start your node in the future:

```powershell
cd C:\MultiChain
.\multichaind.exe artha-chain -daemon
```

Then restart your FastAPI backend and it will connect automatically!
