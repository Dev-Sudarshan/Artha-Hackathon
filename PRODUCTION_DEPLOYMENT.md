# Production-Ready Blockchain Integration Guide

Complete checklist for deploying Aartha blockchain features to production.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Smart Contract Deployment](#smart-contract-deployment)
3. [Security Hardening](#security-hardening)
4. [Backend Configuration](#backend-configuration)
5. [Frontend Configuration](#frontend-configuration)
6. [Database Setup](#database-setup)
7. [Testing Checklist](#testing-checklist)
8. [Monitoring & Logging](#monitoring--logging)
9. [Deployment Steps](#deployment-steps)
10. [Post-Deployment Verification](#post-deployment-verification)

---

## 1. Prerequisites

### Required Tools
```bash
# Verify installations
node --version          # v18+ required
npm --version           # v9+ required
python --version        # v3.8+ required
psql --version         # PostgreSQL client
```

### Required Accounts
- [ ] MultiChain node access (or Ethereum network)
- [ ] Blockchain wallet with private key
- [ ] Sufficient gas/funds for transactions
- [ ] Blockchain explorer access (optional but recommended)

---

## 2. Smart Contract Deployment

### Option A: Deploy to MultiChain (Recommended for Your Setup)

#### Step 1: Prepare MultiChain Environment
```bash
# Connect to your MultiChain node
multichain-cli artha-chain getinfo

# Create a new address for the contract owner
multichain-cli artha-chain getnewaddress

# Get the private key (SAVE THIS SECURELY!)
multichain-cli artha-chain dumpprivkey <new-address>
```

#### Step 2: Deploy Smart Contract

**If MultiChain supports smart contracts:**
```bash
# Use your MultiChain deployment method
# Refer to MultiChain documentation for smart contract deployment
```

**If MultiChain doesn't support EVM contracts:**
You have two options:
1. Use MultiChain streams (simpler, already partially implemented)
2. Deploy to Ethereum/Polygon sidechain for smart contracts

### Option B: Deploy to Ethereum/Polygon (Alternative)

#### Step 1: Install Hardhat
```bash
cd backend/blockchain_scripts
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
npx hardhat init
```

#### Step 2: Configure Hardhat
Create `hardhat.config.js`:
```javascript
require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: "0.8.19",
  networks: {
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL,
      accounts: [process.env.DEPLOYER_PRIVATE_KEY]
    },
    polygon: {
      url: "https://polygon-rpc.com",
      accounts: [process.env.DEPLOYER_PRIVATE_KEY]
    }
  }
};
```

#### Step 3: Create Deployment Script
Create `deploy.js`:
```javascript
async function main() {
  const LoanRegistry = await ethers.getContractFactory("LoanRegistry");
  console.log("Deploying LoanRegistry...");
  
  const loanRegistry = await LoanRegistry.deploy();
  await loanRegistry.waitForDeployment();
  
  const address = await loanRegistry.getAddress();
  console.log("✅ LoanRegistry deployed to:", address);
  console.log("🔑 Contract Owner:", await loanRegistry.owner());
  
  // Save this address to your .env!
  return address;
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
```

#### Step 4: Deploy
```bash
# Deploy to testnet (Sepolia)
npx hardhat run deploy.js --network sepolia

# Deploy to mainnet (after testing!)
npx hardhat run deploy.js --network polygon
```

#### Step 5: Verify Contract (Optional but Recommended)
```bash
# Verify on Etherscan/Polygonscan
npx hardhat verify --network sepolia <CONTRACT_ADDRESS>
```

### Step 6: Update Contract ABI

After deployment, update the ABI in all scripts:

**Get ABI from Hardhat:**
```bash
# ABI is in artifacts/contracts/LoanRegistry.sol/LoanRegistry.json
cat artifacts/contracts/LoanRegistry.sol/LoanRegistry.json | jq '.abi' > abi.json
```

**Update these files:**
1. `backend/blockchain_scripts/storeLoan.js`
2. `backend/blockchain_scripts/markRepaid.js`
3. `backend/blockchain_scripts/getLoan.js`

Replace the `CONTRACT_ABI` constant with your actual ABI.

---

## 3. Security Hardening

### A. Private Key Management

**NEVER store private keys in code!**

#### Production Setup: Use Secret Manager

**AWS Secrets Manager:**
```python
# backend/services/blockchain_service.py
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# In BlockchainService __init__:
secrets = get_secret('aartha/blockchain/prod')
self.private_key = secrets['BLOCKCHAIN_PRIVATE_KEY']
```

**Azure Key Vault:**
```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://aartha-vault.vault.azure.net/", credential=credential)
self.private_key = client.get_secret("blockchain-private-key").value
```

**HashiCorp Vault:**
```python
import hvac

client = hvac.Client(url='http://vault:8200', token=os.getenv('VAULT_TOKEN'))
secret = client.secrets.kv.v2.read_secret_version(path='blockchain/keys')
self.private_key = secret['data']['data']['private_key']
```

#### Development Setup: Environment Variables
```bash
# .env (DO NOT COMMIT!)
BLOCKCHAIN_PRIVATE_KEY=0x...
```

### B. Rate Limiting

Add rate limiting to blockchain endpoints:

```python
# backend/admin/admin_routes.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/admin/loans/{loan_id}/blockchain/store")
@limiter.limit("5/minute")  # Max 5 blockchain calls per minute
def store_loan_on_blockchain(...):
    ...
```

### C. Input Validation

Strengthen validation:

```python
# backend/services/blockchain_service.py
import re

def _validate_loan_id(self, loan_id: str) -> bool:
    """Validate loan ID format"""
    if not loan_id or len(loan_id) > 100:
        return False
    # Only allow alphanumeric and hyphens
    if not re.match(r'^[a-zA-Z0-9-]+$', loan_id):
        return False
    return True

def store_loan_on_chain(self, loan_id: str, ...):
    if not self._validate_loan_id(loan_id):
        raise ValueError("Invalid loan ID format")
    ...
```

### D. Transaction Retry Logic

Add retry mechanism for failed transactions:

```python
# backend/services/blockchain_service.py
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def _call_blockchain_script(self, script_name: str, params: list) -> Dict:
    """Execute with automatic retry on failure"""
    # ... existing code ...
```

### E. Audit Logging

Add comprehensive logging:

```python
# backend/services/blockchain_service.py
import logging
from datetime import datetime

audit_logger = logging.getLogger("aartha.blockchain.audit")

def store_loan_on_chain(self, loan_id: str, ...):
    audit_logger.info(
        f"BLOCKCHAIN_STORE_ATTEMPT",
        extra={
            "loan_id": loan_id,
            "timestamp": datetime.utcnow().isoformat(),
            "admin_email": admin_email,  # Pass from route
            "borrower": borrower_address,
            "lender": lender_address
        }
    )
    
    success, tx_hash, error = # ... blockchain call ...
    
    audit_logger.info(
        f"BLOCKCHAIN_STORE_{'SUCCESS' if success else 'FAILURE'}",
        extra={
            "loan_id": loan_id,
            "tx_hash": tx_hash,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

---

## 4. Backend Configuration

### Production .env File

```env
# =============================================================================
# PRODUCTION BLOCKCHAIN CONFIGURATION
# =============================================================================

# Private key (use secret manager in production!)
BLOCKCHAIN_PRIVATE_KEY=${SECRET_MANAGER_KEY}

# Production RPC endpoint
BLOCKCHAIN_RPC_URL=https://polygon-mainnet.infura.io/v3/YOUR_PROJECT_ID

# Deployed contract address
BLOCKCHAIN_CONTRACT_ADDRESS=0xYOUR_DEPLOYED_CONTRACT_ADDRESS

# Gas settings
BLOCKCHAIN_GAS_LIMIT=500000
BLOCKCHAIN_MAX_GAS_PRICE=100  # in Gwei

# Retry settings
BLOCKCHAIN_MAX_RETRIES=3
BLOCKCHAIN_RETRY_DELAY=5

# Monitoring
BLOCKCHAIN_ALERT_EMAIL=admin@aartha.com
BLOCKCHAIN_WEBHOOK_URL=https://your-monitoring-service.com/webhook

# =============================================================================
# DATABASE
# =============================================================================
DATABASE_URL=postgresql://user:password@prod-db:5432/aartha_prod

# =============================================================================
# API CONFIGURATION
# =============================================================================
API_BASE_URL=https://api.aartha.com
ADMIN_PANEL_URL=https://admin.aartha.com

# =============================================================================
# SECURITY
# =============================================================================
JWT_SECRET_KEY=${SECRET_MANAGER_JWT_KEY}
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# CORS
ALLOWED_ORIGINS=https://aartha.com,https://admin.aartha.com
```

### Update blockchain_service.py for Production

Add configuration management:

```python
# backend/services/blockchain_service.py

class BlockchainConfig:
    """Centralized blockchain configuration"""
    
    def __init__(self):
        self.private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")
        self.rpc_url = os.getenv("BLOCKCHAIN_RPC_URL")
        self.contract_address = os.getenv("BLOCKCHAIN_CONTRACT_ADDRESS")
        self.gas_limit = int(os.getenv("BLOCKCHAIN_GAS_LIMIT", "500000"))
        self.max_gas_price = int(os.getenv("BLOCKCHAIN_MAX_GAS_PRICE", "100"))
        self.max_retries = int(os.getenv("BLOCKCHAIN_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("BLOCKCHAIN_RETRY_DELAY", "5"))
        
        # Validate critical settings
        self._validate()
    
    def _validate(self):
        if not all([self.private_key, self.rpc_url, self.contract_address]):
            raise ValueError("Missing required blockchain configuration")
        
        if not self.contract_address.startswith("0x"):
            raise ValueError("Invalid contract address format")
```

---

## 5. Frontend Configuration

### Production Environment Variables

Create `admin-frontend/.env.production`:

```env
VITE_API_BASE_URL=https://api.aartha.com/api
VITE_BLOCKCHAIN_EXPLORER_URL=https://polygonscan.com
VITE_ENABLE_BLOCKCHAIN=true
```

### Update adminApi.js for Production

```javascript
// admin-frontend/src/services/adminApi.js

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';
const BLOCKCHAIN_EXPLORER = import.meta.env.VITE_BLOCKCHAIN_EXPLORER_URL || 'https://polygonscan.com';

// Export for use in components
export const getExplorerUrl = (txHash) => {
  return `${BLOCKCHAIN_EXPLORER}/tx/${txHash}`;
};
```

### Update Loans.jsx for Production

```javascript
// Use environment-based explorer URL
const explorerUrl = getExplorerUrl(blockchainStatuses[l.loan_id]?.transaction_hash);
```

---

## 6. Database Setup

### Production Database Migration

```bash
# 1. Backup production database
pg_dump -h prod-db -U user -d aartha_prod > backup_$(date +%Y%m%d).sql

# 2. Test migration on staging
psql -h staging-db -U user -d aartha_staging < migrate_blockchain_fields.sql

# 3. Run on production (during maintenance window)
python migrate_blockchain_fields.py
```

### Create Indexes for Performance

```sql
-- Add indexes for blockchain queries
CREATE INDEX idx_loans_blockchain_status ON loans(blockchain_status);
CREATE INDEX idx_loans_blockchain_tx_hash ON loans(blockchain_tx_hash);
CREATE INDEX idx_loans_blockchain_stored_at ON loans(blockchain_stored_at);

-- Analyze table
ANALYZE loans;
```

---

## 7. Testing Checklist

### A. Unit Tests

Create `backend/tests/test_blockchain_service.py`:

```python
import pytest
from services.blockchain_service import BlockchainService

def test_hash_generation():
    service = BlockchainService()
    loan_data = {"loan_id": "123", "amount": 1000}
    hash1 = service._generate_loan_hash(loan_data)
    hash2 = service._generate_loan_hash(loan_data)
    assert hash1 == hash2  # Deterministic

def test_hash_changes_with_data():
    service = BlockchainService()
    loan1 = {"loan_id": "123", "amount": 1000}
    loan2 = {"loan_id": "123", "amount": 2000}
    assert service._generate_loan_hash(loan1) != service._generate_loan_hash(loan2)

@pytest.mark.asyncio
async def test_store_loan_validation():
    service = BlockchainService()
    with pytest.raises(ValueError):
        service.store_loan_on_chain("", {}, "", "")  # Empty loan_id
```

### B. Integration Tests

```python
# backend/tests/test_blockchain_integration.py

def test_full_loan_lifecycle(test_client):
    # 1. Create and approve loan
    response = test_client.post("/api/admin/loans/test-123/approve")
    assert response.status_code == 200
    
    # 2. Store on blockchain
    response = test_client.post("/api/admin/loans/test-123/blockchain/store")
    assert response.status_code == 200
    assert "transaction_hash" in response.json()
    
    # 3. Verify integrity
    response = test_client.get("/api/admin/loans/test-123/blockchain/verify")
    assert response.json()["verified"] == True
    
    # 4. Mark repaid
    response = test_client.post("/api/admin/loans/test-123/blockchain/mark-repaid")
    assert response.status_code == 200
```

### C. Load Testing

```bash
# Install locust
pip install locust

# Create locustfile.py
# Run load test
locust -f tests/locustfile.py --host=https://api.aartha.com
```

### D. Security Testing

```bash
# 1. Run security scan
pip install bandit
bandit -r backend/services/blockchain_service.py

# 2. Check for secrets in code
pip install detect-secrets
detect-secrets scan

# 3. Dependency vulnerability scan
pip install safety
safety check
```

---

## 8. Monitoring & Logging

### A. Set Up Application Monitoring

**Using New Relic:**
```python
# backend/main.py
import newrelic.agent
newrelic.agent.initialize('newrelic.ini')

@app.middleware("http")
async def add_newrelic_tracking(request, call_next):
    transaction = newrelic.agent.current_transaction()
    transaction.add_custom_parameter('endpoint', request.url.path)
    response = await call_next(request)
    return response
```

**Using Sentry:**
```python
# backend/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://your-sentry-dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0,
)
```

### B. Blockchain-Specific Metrics

```python
# backend/services/blockchain_service.py
from prometheus_client import Counter, Histogram

# Define metrics
blockchain_calls = Counter('blockchain_calls_total', 'Total blockchain calls', ['operation', 'status'])
blockchain_latency = Histogram('blockchain_call_duration_seconds', 'Blockchain call duration')

def store_loan_on_chain(self, ...):
    with blockchain_latency.time():
        try:
            # ... blockchain operation ...
            blockchain_calls.labels(operation='store', status='success').inc()
        except Exception as e:
            blockchain_calls.labels(operation='store', status='failure').inc()
            raise
```

### C. Alert Configuration

Create alert rules:

```yaml
# alerts.yml
groups:
  - name: blockchain
    rules:
      - alert: HighBlockchainFailureRate
        expr: rate(blockchain_calls_total{status="failure"}[5m]) > 0.1
        annotations:
          summary: "High blockchain failure rate detected"
      
      - alert: BlockchainHighLatency
        expr: blockchain_call_duration_seconds > 30
        annotations:
          summary: "Blockchain calls taking too long"
```

---

## 9. Deployment Steps

### Pre-Deployment Checklist

- [ ] Smart contract deployed and verified
- [ ] Contract ABI updated in all scripts
- [ ] Environment variables configured
- [ ] Database migration script tested
- [ ] All tests passing
- [ ] Security scan completed
- [ ] Load testing completed
- [ ] Monitoring configured
- [ ] Backup created
- [ ] Rollback plan ready

### Step-by-Step Deployment

#### 1. Deploy to Staging First

```bash
# 1. Deploy backend to staging
git checkout main
git pull origin main
cd backend

# 2. Install dependencies
npm install  # For blockchain scripts
pip install -r requirements.txt

# 3. Run migrations
python migrate_blockchain_fields.py

# 4. Run tests
pytest tests/

# 5. Start service
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

#### 2. Deploy Frontend to Staging

```bash
cd admin-frontend

# 1. Build for production
npm install
npm run build

# 2. Deploy to staging
# (Use your deployment method: S3, Netlify, Vercel, etc.)
```

#### 3. Staging Verification

- [ ] Test loan approval flow
- [ ] Test blockchain storage
- [ ] Test verification
- [ ] Test marking as repaid
- [ ] Verify transaction on blockchain explorer
- [ ] Check monitoring dashboards
- [ ] Review logs for errors

#### 4. Production Deployment

```bash
# During maintenance window:

# 1. Enable maintenance mode
# 2. Backup database
pg_dump aartha_prod > backup_prod_$(date +%Y%m%d_%H%M%S).sql

# 3. Run migration
python migrate_blockchain_fields.py

# 4. Deploy backend
git tag v1.0.0-blockchain
git push --tags
# Trigger CI/CD pipeline

# 5. Deploy frontend
npm run build
# Deploy to production CDN

# 6. Disable maintenance mode
```

---

## 10. Post-Deployment Verification

### Immediate Checks (First 10 minutes)

```bash
# 1. Health check
curl https://api.aartha.com/health

# 2. Test blockchain endpoints
curl -X GET https://api.aartha.com/api/admin/loans/test-loan/blockchain/status \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 3. Check logs
tail -f /var/log/aartha/blockchain.log

# 4. Monitor error rates
# Check your monitoring dashboard
```

### First Hour Monitoring

- [ ] No 5xx errors
- [ ] Blockchain success rate > 95%
- [ ] Average response time < 2s
- [ ] No security alerts
- [ ] Database performance stable

### First 24 Hours

- [ ] Process 10+ blockchain transactions successfully
- [ ] Verify all transactions on explorer
- [ ] No data inconsistencies
- [ ] Monitor gas costs
- [ ] Review audit logs

### Week 1 Review

- [ ] Analyze transaction success rate
- [ ] Review gas usage and costs
- [ ] Check for any security incidents
- [ ] Gather user feedback
- [ ] Optimize based on metrics

---

## 11. Operational Procedures

### Daily Operations

```bash
# Morning checks
- Review overnight blockchain transactions
- Check gas prices and adjust if needed
- Verify no failed transactions
- Review alert logs
```

### Weekly Maintenance

```bash
# Every Monday
- Verify 100 random loans against blockchain
- Review and optimize gas settings
- Check for smart contract updates needed
- Backup blockchain transaction logs
```

### Monthly Audits

- [ ] Full blockchain integrity audit
- [ ] Security review
- [ ] Cost analysis (gas fees)
- [ ] Performance optimization review
- [ ] Update documentation

---

## 12. Troubleshooting Production Issues

### Issue: Blockchain Transactions Failing

**Diagnosis:**
```bash
# Check node status
curl -X POST $BLOCKCHAIN_RPC_URL \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# Check gas prices
# Check account balance
```

**Resolution:**
1. Verify RPC endpoint is accessible
2. Check account has sufficient balance
3. Increase gas limit if needed
4. Switch to backup RPC if primary is down

### Issue: High Gas Costs

**Resolution:**
1. Batch transactions if possible
2. Optimize contract calls
3. Consider Layer 2 solutions (Polygon, Arbitrum)
4. Implement gas price monitoring and alerts

### Issue: Verification Failing

**Diagnosis:**
```python
# Debug specific loan
python -c "
from services.blockchain_service import get_blockchain_service
service = get_blockchain_service()
success, data, error = service.get_loan_from_chain('LOAN-123')
print(f'Success: {success}')
print(f'Data: {data}')
print(f'Error: {error}')
"
```

**Resolution:**
1. Check if loan was actually stored on-chain
2. Verify transaction was confirmed
3. Check if contract state matches expectation
4. Re-store if necessary

---

## 13. Cost Optimization

### Reduce Gas Costs

1. **Batch Operations:** Group multiple loans when possible
2. **Use Events:** Instead of storing large data, store hash and emit event
3. **Optimize Contract:** Remove unnecessary storage variables
4. **Layer 2:** Consider Polygon, Arbitrum, or Optimism

### Example: Optimize Smart Contract

```solidity
// Instead of storing full loan data:
struct Loan {
    string loanId;
    string loanHash;  // ✅ Store hash only
    address borrower;
    address lender;
    bool isRepaid;
    uint256 timestamp;
}

// Emit event for full data
event LoanStored(
    string indexed loanId,
    string loanHash,
    address indexed borrower,
    address indexed lender,
    uint256 timestamp
);
```

---

## 14. Compliance & Audit Trail

### Maintain Audit Logs

```python
# Store comprehensive audit trail
audit_log = {
    "timestamp": datetime.utcnow().isoformat(),
    "action": "LOAN_STORED_ON_BLOCKCHAIN",
    "loan_id": loan_id,
    "admin_email": admin.email,
    "admin_ip": request.client.host,
    "tx_hash": tx_hash,
    "gas_used": gas_used,
    "gas_price": gas_price,
    "total_cost": total_cost,
    "blockchain_network": "polygon-mainnet",
    "contract_address": contract_address
}
```

### Regular Compliance Reports

Generate monthly reports:
- Total transactions processed
- Success/failure rates
- Gas costs incurred
- Data integrity verification results
- Security incidents (if any)

---

## 15. Disaster Recovery

### Backup Strategy

```bash
# Daily automated backups
0 2 * * * pg_dump aartha_prod > /backups/aartha_$(date +\%Y\%m\%d).sql

# Weekly blockchain transaction log backup
0 3 * * 0 python scripts/export_blockchain_logs.py
```

### Recovery Procedures

**If database is corrupted:**
1. Restore from latest backup
2. Verify blockchain data from on-chain records
3. Reconcile any discrepancies

**If blockchain transactions are lost:**
1. Query blockchain directly for all transactions
2. Rebuild database records from on-chain data
3. Verify integrity of all loans

---

## Summary Checklist

### Before Going Live

- [ ] ✅ Smart contract deployed to production network
- [ ] ✅ Contract verified on blockchain explorer
- [ ] ✅ Private keys secured in secret manager
- [ ] ✅ All environment variables configured
- [ ] ✅ Database migration completed
- [ ] ✅ All tests passing (unit, integration, load)
- [ ] ✅ Security scan completed with no critical issues
- [ ] ✅ Monitoring and alerting configured
- [ ] ✅ Backup and disaster recovery plan in place
- [ ] ✅ Staging environment tested successfully
- [ ] ✅ Documentation updated
- [ ] ✅ Team trained on new features
- [ ] ✅ Rollback plan prepared
- [ ] ✅ Support team notified
- [ ] ✅ Compliance requirements met

### First Week Post-Launch

- [ ] Monitor all blockchain transactions
- [ ] Review gas costs daily
- [ ] Check error logs hourly
- [ ] Gather user feedback
- [ ] Optimize based on production metrics

---

**🎉 You're Ready for Production!**

This guide covers everything needed for a secure, scalable, production-ready blockchain integration. Follow each step carefully and test thoroughly before deploying to production.

For questions or issues, refer to [BLOCKCHAIN_INTEGRATION.md](BLOCKCHAIN_INTEGRATION.md) for technical details.
