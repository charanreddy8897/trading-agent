# CDK Deployment Guide

Step-by-step guide to deploy the Trading Agent to AWS using CDK.

---

## Prerequisites

### 1. AWS Account
- Create an AWS account at https://aws.amazon.com
- Note your 12-digit account ID (find in AWS Console top-right)

### 2. AWS CLI
```bash
# Install AWS CLI
brew install awscli  # macOS
# or pip install awscli

# Configure credentials
aws configure
# AWS Access Key ID: [your key]
# AWS Secret Access Key: [your secret]
# Default region: us-east-1
# Default output format: json
```

### 3. Node.js & AWS CDK CLI
```bash
# Install Node.js (if not installed)
brew install node  # macOS

# Install CDK CLI globally
npm install -g aws-cdk

# Verify
cdk --version
```

### 4. Python 3.11+
```bash
python3 --version  # Should be 3.11 or higher
```

### 5. EC2 Key Pair
```bash
# Create key pair in AWS Console
# Go to: EC2 → Key Pairs → Create Key Pair
# Name: trading-agent-key
# Type: RSA
# Format: .pem
# Download and save to ~/.ssh/trading-agent-key.pem

chmod 400 ~/.ssh/trading-agent-key.pem
```

### 6. Get Your Public IP
```bash
curl ifconfig.me
# Example output: 203.0.113.45
```

### 7. API Keys
Get these API keys before deploying:
- **Anthropic API Key**: https://console.anthropic.com/settings/keys
- **Finnhub API Key**: https://finnhub.io/dashboard
- **Alpaca API Key + Secret**: https://app.alpaca.markets/paper/dashboard
- (Optional) Slack Bot Token: https://api.slack.com/apps

---

## Deployment Steps

### Step 1: Configure CDK

```bash
cd cdk

# Edit cdk.json with your values
cat > cdk.json << 'EOF'
{
  "app": "python3 app.py",
  "watch": {
    "include": ["**"],
    "exclude": ["README.md", "cdk*.json", "**/__pycache__", "**/.venv"]
  },
  "context": {
    "@aws-cdk/aws-lambda:recognizeLayerVersion": true,
    "@aws-cdk/core:checkSecretUsage": true,

    "region":       "us-east-1",
    "account":      "YOUR_12_DIGIT_AWS_ACCOUNT_ID",

    "my_ip":        "YOUR_PUBLIC_IP/32",
    "key_pair_name": "trading-agent-key",

    "domain_name":  ""
  }
}
EOF
```

**Replace**:
- `YOUR_12_DIGIT_AWS_ACCOUNT_ID` → Your AWS account ID
- `YOUR_PUBLIC_IP` → Your public IP from `curl ifconfig.me`

### Step 2: Install CDK Dependencies

```bash
cd cdk

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Bootstrap CDK (One-Time)

```bash
# Initialize CDK in your AWS account/region (one-time operation)
cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1
```

**This creates**:
- S3 bucket for CDK assets
- IAM roles for CloudFormation
- ECR repository for Docker images

### Step 4: Synthesize (Dry Run)

```bash
# Generate CloudFormation templates
cdk synth
```

**This creates** `cdk.out/` with CloudFormation JSON files. Review them if you want to see exactly what will be created.

### Step 5: Deploy All Stacks

```bash
# Deploy all 4 stacks
cdk deploy --all

# Or deploy one by one:
cdk deploy TradingAgentNetwork
cdk deploy TradingAgentDatabase
cdk deploy TradingAgentApp
cdk deploy TradingAgentFrontend
```

**This takes ~15 minutes**:
- Network stack: ~2 min (VPC, subnets, security groups)
- Database stack: ~8 min (RDS PostgreSQL creation)
- App stack: ~5 min (EC2 instance + user-data script)
- Frontend stack: ~2 min (S3 + CloudFront)

**Output**:
```
TradingAgentApp.PublicIP = 54.123.45.67
TradingAgentApp.APIUrl = http://54.123.45.67:8000
TradingAgentApp.SwaggerDocs = http://54.123.45.67:8000/docs
TradingAgentApp.SSHCommand = ssh -i ~/.ssh/trading-agent-key.pem ec2-user@54.123.45.67
TradingAgentDatabase.DBEndpoint = trading-agent-db.xxxxx.us-east-1.rds.amazonaws.com
```

**Save these outputs!**

---

## Post-Deployment Configuration

### Step 1: Update API Keys in SSM Parameter Store

#### Option A: AWS Console (Easier)

1. Go to: **AWS Systems Manager** → **Parameter Store**
2. You'll see parameters named `/trading-agent/*`
3. Click each one and update the value:

| Parameter Name | Value |
|----------------|-------|
| `/trading-agent/ANTHROPIC_API_KEY` | `sk-ant-...` |
| `/trading-agent/FINNHUB_API_KEY` | Your Finnhub key |
| `/trading-agent/ALPACA_API_KEY` | Your Alpaca key |
| `/trading-agent/ALPACA_SECRET_KEY` | Your Alpaca secret |
| `/trading-agent/JWT_SECRET_KEY` | Generate: `openssl rand -hex 32` |

Leave optional parameters as-is (Slack, Robinhood).

#### Option B: AWS CLI (Faster)

```bash
# Set required API keys
aws ssm put-parameter \
  --name /trading-agent/ANTHROPIC_API_KEY \
  --value "sk-ant-YOUR_KEY_HERE" \
  --type String \
  --overwrite

aws ssm put-parameter \
  --name /trading-agent/FINNHUB_API_KEY \
  --value "YOUR_FINNHUB_KEY" \
  --type String \
  --overwrite

aws ssm put-parameter \
  --name /trading-agent/ALPACA_API_KEY \
  --value "YOUR_ALPACA_KEY" \
  --type String \
  --overwrite

aws ssm put-parameter \
  --name /trading-agent/ALPACA_SECRET_KEY \
  --value "YOUR_ALPACA_SECRET" \
  --type String \
  --overwrite

aws ssm put-parameter \
  --name /trading-agent/JWT_SECRET_KEY \
  --value "$(openssl rand -hex 32)" \
  --type String \
  --overwrite
```

### Step 2: SSH to EC2 and Restart Backend

```bash
# SSH to your EC2 instance (use PublicIP from CDK output)
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@54.123.45.67

# Check if Docker container is running
docker ps

# Restart to load new API keys
docker restart trading-agent

# Watch logs
docker logs -f trading-agent
```

**You should see**:
```json
{"timestamp": "2026-06-05T10:30:00", "level": "INFO", "logger": "app.main", "message": "Starting Trading Agent API"}
{"timestamp": "2026-06-05T10:30:01", "level": "INFO", "logger": "app.scheduler.jobs", "message": "TradingScheduler started — 3 jobs registered"}
{"timestamp": "2026-06-05T10:30:01", "level": "INFO", "logger": "app.core.metrics", "message": "CloudWatch metrics publisher started"}
```

Press `Ctrl+C` to stop watching logs.

### Step 3: Run Database Migrations

```bash
# Still SSH'd to EC2
docker exec -it trading-agent python -m scripts.migrate_db
```

**Output**:
```
✓ Migration complete: backup_codes column added
```

### Step 4: Create First User

```bash
# Create admin user
docker exec -it trading-agent python -m scripts.seed_user \
  --username admin \
  --password "YourStrongPassword123!"
```

**Output**:
```
✓ User 'admin' created successfully
✓ Next step: Login and set up TOTP (Two-Factor Authentication)
```

### Step 5: Test Backend Health

```bash
# From your local machine (use your PublicIP)
curl http://54.123.45.67:8000/health

# Expected response:
{"status":"ok"}
```

### Step 6: Test Connection

```bash
# From your local machine
# Download the connection test script
scp -i ~/.ssh/trading-agent-key.pem \
  ec2-user@54.123.45.67:/app/backend/scripts/test_connections.py \
  /tmp/

# Or run it on EC2
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@54.123.45.67 \
  'docker exec trading-agent python -m scripts.test_connections'
```

**Expected output**:
```
✓ PostgreSQL                PASS   Connected: PostgreSQL
✓ Anthropic Claude Key      PASS   Configured
✓ Finnhub API               PASS   AAPL quote: $311.23
✓ Alpaca API                PASS   Buying power: $400,000.00
✓ Data - Price History      SKIP   Empty (run pipeline to populate)
```

---

## First Login & TOTP Setup

### Step 1: Login

```bash
# Use your EC2 Public IP
export API_URL="http://54.123.45.67:8000"

curl -X POST $API_URL/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "YourStrongPassword123!"
  }'
```

**Response**:
```json
{
  "status": "setup_required",
  "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Step 2: Get TOTP Secret

```bash
export TEMP_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl "$API_URL/api/v1/auth/totp-setup?temp_token=$TEMP_TOKEN"
```

**Response**:
```json
{
  "secret": "GNZRPROVCZLMCCTEHNPOCWMXJRXSHYF6",
  "backup_codes": ["0C5AD181", "C10CB734", ...]
}
```

### Step 3: Add to Authenticator App

1. Open **Google Authenticator** or **Authy** on your phone
2. Tap **"Add Account"** → **"Enter a setup key"**
3. Account name: `TradingAgent`
4. Key: `GNZRPROVCZLMCCTEHNPOCWMXJRXSHYF6`
5. Type: Time-based
6. **Save your backup codes somewhere safe!**

### Step 4: Verify TOTP

```bash
# Get 6-digit code from your authenticator app
export TOTP_CODE="123456"

curl -X POST $API_URL/api/v1/auth/totp-setup \
  -H "Content-Type: application/json" \
  -d '{
    "temp_token": "'$TEMP_TOKEN'",
    "code": "'$TOTP_CODE'"
  }'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**✅ Setup complete!** Save your access_token.

---

## Using the API

### Access Swagger UI

Open in your browser:
```
http://54.123.45.67:8000/docs
```

1. Click **"Authorize"** button
2. Paste your `access_token`
3. Click **"Authorize"** → **"Close"**
4. Try any endpoint!

### Example API Calls

```bash
export ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Get your user info
curl $API_URL/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Get ranked stocks
curl $API_URL/api/v1/screener/ranked \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Get portfolio summary
curl $API_URL/api/v1/portfolio/summary \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Run data pipeline (fetch latest prices)
curl -X POST $API_URL/api/v1/system/run-pipeline \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

---

## Optional: Set Up HTTPS with Domain

### Prerequisites
- Own a domain (e.g., `yourdomain.com`)
- Access to DNS settings

### Step 1: Update cdk.json

```json
{
  "context": {
    "domain_name": "api.yourdomain.com"
  }
}
```

### Step 2: Redeploy App Stack

```bash
cdk deploy TradingAgentApp
```

This will:
- Configure nginx for your domain
- Get Let's Encrypt SSL certificate (automatic)
- Redirect HTTP → HTTPS

### Step 3: Point DNS to EC2

In your DNS provider (Namecheap, GoDaddy, Route 53):

**Add A Record**:
- Name: `api`
- Type: `A`
- Value: `54.123.45.67` (your EC2 Elastic IP)
- TTL: `300`

### Step 4: Wait for DNS Propagation (~5-60 minutes)

```bash
# Check DNS
nslookup api.yourdomain.com

# Should return your EC2 IP
```

### Step 5: Test HTTPS

```bash
curl https://api.yourdomain.com/health

# Should work with HTTPS!
```

**Now your API is at**: `https://api.yourdomain.com` 🎉

---

## Monitoring & Logs

### CloudWatch Logs

```bash
# View logs in AWS Console
# Go to: CloudWatch → Log Groups → /trading-agent/backend

# Or via CLI
aws logs tail /trading-agent/backend --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /trading-agent/backend \
  --filter-pattern "ERROR"
```

### CloudWatch Metrics

Go to: **CloudWatch** → **Metrics** → **TradingAgent/API**

**Available metrics**:
- RequestCount (2xx, 4xx, 5xx)
- RequestLatency (p50, p95, p99)

### SSH to EC2

```bash
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@54.123.45.67

# Check Docker status
docker ps
docker logs trading-agent

# Check disk space
df -h

# Check memory
free -h

# Restart backend
docker restart trading-agent
```

---

## Cost Estimate

### Year 1 (Free Tier)
- EC2 t2.micro: **$0** (750 hrs/month free)
- RDS db.t3.micro: **$0** (750 hrs/month free)
- 20 GB EBS: **$0** (30 GB free)
- S3: **$0** (5 GB free)
- CloudFront: **$0** (always free - 1 TB)
- Elastic IP: **$0** (free when attached)
- Route 53: **$0.50/month** (if you add domain)

**Total Year 1**: **~$0-0.50/month** 🎉

### After Year 1
- EC2 t2.micro: **$8.35/month**
- RDS db.t3.micro: **$14.40/month**
- EBS 20 GB: **$2/month**
- S3 + CloudFront: **$0.12/month**
- Route 53: **$0.50/month**

**Total After Year 1**: **~$25/month**

---

## Updating the Backend

### Option 1: Via GitHub (Recommended)

```bash
# 1. Push changes to GitHub
git add .
git commit -m "Update feature X"
git push origin main

# 2. SSH to EC2
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@54.123.45.67

# 3. Pull latest code
cd /app
git pull origin main

# 4. Rebuild and restart
cd backend
docker build -t trading-agent .
docker stop trading-agent
docker rm trading-agent
docker run -d --restart always --env-file .env -p 127.0.0.1:8000:8000 --name trading-agent trading-agent

# 5. Check logs
docker logs -f trading-agent
```

### Option 2: Direct SCP

```bash
# Copy backend folder to EC2
scp -i ~/.ssh/trading-agent-key.pem -r ../backend/ ec2-user@54.123.45.67:/app/

# SSH and rebuild
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@54.123.45.67
cd /app/backend
docker build -t trading-agent .
docker restart trading-agent
```

---

## Troubleshooting

### Backend not starting

```bash
# Check Docker logs
docker logs trading-agent

# Common issues:
# 1. Missing API keys → Update SSM Parameter Store
# 2. Database connection failed → Check security group
# 3. Port already in use → docker stop old container
```

### Can't connect to database

```bash
# Check RDS endpoint
aws rds describe-db-instances \
  --db-instance-identifier trading-agent-db \
  --query 'DBInstances[0].Endpoint.Address'

# Check security group allows EC2 → RDS
aws ec2 describe-security-groups --filters Name=group-name,Values=trading-agent-rds
```

### TOTP codes not working

```bash
# Check EC2 time is synced
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@54.123.45.67
date -u

# Should match actual UTC time
# If off by > 30 seconds, TOTP will fail
```

### 503 Service Unavailable

```bash
# Check nginx status
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@54.123.45.67
sudo systemctl status nginx

# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Restart nginx
sudo systemctl restart nginx
```

---

## Teardown (Delete Everything)

```bash
# Delete all stacks
cdk destroy --all

# Or one by one (in reverse order)
cdk destroy TradingAgentFrontend
cdk destroy TradingAgentApp
cdk destroy TradingAgentDatabase
cdk destroy TradingAgentNetwork
```

**This will**:
- Delete EC2 instance
- Delete RDS database (snapshot created first)
- Delete VPC and subnets
- Delete S3 bucket and CloudFront
- Delete all CloudWatch logs

**⚠️ Database snapshots remain** (can restore later or delete manually)

---

## Next Steps

1. ✅ Deploy CDK stacks
2. ✅ Update API keys
3. ✅ Create first user
4. ✅ Test login flow
5. 📊 Run data pipeline to populate database
6. 📈 Start trading!

**Questions?** Check:
- Backend README: `../backend/README.md`
- AWS Deployment Guide: `../backend/AWS_DEPLOYMENT.md`
- CDK Comparison: `CDK_VS_DEPLOYMENT_GUIDE.md`

🚀 Happy trading!
