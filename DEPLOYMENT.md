# Trading Agent - AWS Deployment Guide

Complete guide for deploying the Trading Agent system to AWS using CDK infrastructure-as-code.

---

## 🎯 Deployment Overview

**Deployed Infrastructure:**
- **Frontend**: React app on S3 + CloudFront CDN
- **Backend**: FastAPI on EC2 t3.micro + Docker
- **Database**: RDS PostgreSQL 16 (free tier)
- **Network**: VPC with public/private subnets
- **Secrets**: AWS SSM Parameter Store + Secrets Manager

**Total Setup Time**: ~30-40 minutes
**Cost**: ~$0-1.50/month (Year 1 free tier) → ~$25/month after

---

## 📋 Prerequisites

### 1. Install Required Tools

```bash
# AWS CLI
brew install awscli

# AWS CDK CLI
brew install aws-cdk

# GitHub CLI (optional, for repo management)
brew install gh
```

### 2. Configure AWS Credentials

```bash
# Configure AWS CLI with your credentials
aws configure
# Enter: Access Key ID, Secret Access Key, region (us-east-1), output (json)

# Verify configuration
aws sts get-caller-identity
```

### 3. Get API Keys

You'll need API keys from these services:

| Service | Sign Up URL | Free Tier |
|---------|------------|-----------|
| **Anthropic** | https://console.anthropic.com/ | $5 credit |
| **Finnhub** | https://finnhub.io/ | 60 calls/min free |
| **Alpaca** | https://alpaca.markets/ | Paper trading (unlimited) |
| **Slack** (optional) | https://api.slack.com/apps | Free |

---

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Your Project

```bash
# Clone the repository (if not already done)
git clone https://github.com/charanreddy8897/trading-agent.git
cd trading-agent

# Make repository public (EC2 needs to clone it)
gh repo edit --visibility public --accept-visibility-change-consequences
```

### Step 2: Configure CDK

```bash
cd cdk

# Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install CDK dependencies
pip install -r requirements.txt

# Get your AWS account ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Get your public IP
export MY_IP=$(curl -s https://checkip.amazonaws.com)

# Update cdk.json with your details
cat > cdk.json << EOF
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
    "account":      "$AWS_ACCOUNT_ID",

    "my_ip":        "$MY_IP/32",
    "key_pair_name": "trading-agent-key",

    "domain_name":  ""
  }
}
EOF
```

### Step 3: Create EC2 Key Pair

```bash
# Create SSH key for EC2 access
aws ec2 create-key-pair \
  --key-name trading-agent-key \
  --key-type ed25519 \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/trading-agent-key.pem

chmod 400 ~/.ssh/trading-agent-key.pem
```

### Step 4: Bootstrap and Deploy CDK

```bash
# Bootstrap CDK (one-time per AWS account/region)
cdk bootstrap aws://$AWS_ACCOUNT_ID/us-east-1

# Deploy all infrastructure stacks (~15 minutes)
cdk deploy --all --require-approval never
```

**What Gets Created:**
1. **TradingAgentNetwork** - VPC, subnets, security groups (~2 min)
2. **TradingAgentDatabase** - RDS PostgreSQL (~8 min)
3. **TradingAgentApp** - EC2 instance with Docker (~4 min)
4. **TradingAgentFrontend** - S3 + CloudFront (~3 min)

**Save the outputs** - you'll need them later:
- **PublicIP**: EC2 Elastic IP address
- **CloudFrontURL**: Frontend URL
- **BucketName**: S3 bucket for frontend
- **DistributionId**: CloudFront distribution ID

### Step 5: Configure API Keys in AWS SSM

Generate secret keys:

```bash
export JWT_SECRET=$(openssl rand -hex 32)
export RH_SYNC_KEY=$(openssl rand -hex 32)
```

Add all API keys to SSM Parameter Store:

```bash
# Core API Keys (REPLACE WITH YOUR ACTUAL KEYS)
aws ssm put-parameter --name "/trading-agent/ANTHROPIC_API_KEY" --value "sk-ant-YOUR_KEY" --overwrite
aws ssm put-parameter --name "/trading-agent/FINNHUB_API_KEY" --value "YOUR_KEY" --overwrite
aws ssm put-parameter --name "/trading-agent/ALPACA_API_KEY" --value "YOUR_KEY" --overwrite
aws ssm put-parameter --name "/trading-agent/ALPACA_SECRET_KEY" --value "YOUR_SECRET" --overwrite
aws ssm put-parameter --name "/trading-agent/ALPACA_BASE_URL" --value "https://paper-api.alpaca.markets" --overwrite

# Auto-generated secrets
aws ssm put-parameter --name "/trading-agent/JWT_SECRET_KEY" --value "$JWT_SECRET" --overwrite
aws ssm put-parameter --name "/trading-agent/ROBINHOOD_SYNC_KEY" --value "$RH_SYNC_KEY" --overwrite

# Trading mode
aws ssm put-parameter --name "/trading-agent/TRADING_MODE" --value "paper" --overwrite
aws ssm put-parameter --name "/trading-agent/LOG_LEVEL" --value "INFO" --overwrite

# Optional: Slack (if you're using Slack notifications)
# aws ssm put-parameter --name "/trading-agent/SLACK_BOT_TOKEN" --value "xoxb-YOUR-TOKEN" --overwrite
# aws ssm put-parameter --name "/trading-agent/SLACK_CHANNEL_ALERTS" --value "C123456789" --overwrite
# aws ssm put-parameter --name "/trading-agent/SLACK_CHANNEL_BRIEFING" --value "C123456789" --overwrite
# aws ssm put-parameter --name "/trading-agent/SLACK_CHANNEL_ORDERS" --value "C123456789" --overwrite
# aws ssm put-parameter --name "/trading-agent/SLACK_CHANNEL_EMERGENCY" --value "C123456789" --overwrite
```

### Step 6: Deploy Backend to EC2

The EC2 instance should auto-deploy via user-data script. However, if the repository was private during initial deployment, you need to manually clone and start:

```bash
# SSH into EC2
export EC2_IP=$(aws cloudformation describe-stacks \
  --stack-name TradingAgentApp \
  --query 'Stacks[0].Outputs[?OutputKey==`PublicIP`].OutputValue' \
  --output text)

ssh -i ~/.ssh/trading-agent-key.pem ec2-user@$EC2_IP

# Clone repository
git clone https://github.com/charanreddy8897/trading-agent.git /tmp/trading-agent
sudo mv /tmp/trading-agent /app
cd /app

# Get DB credentials from Secrets Manager
SECRET=$(aws secretsmanager get-secret-value \
  --secret-id "arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT_ID:secret:trading-agent/db-credentials-XXXXX" \
  --region us-east-1 \
  --query SecretString --output text)
DB_USER=$(echo $SECRET | jq -r .username)
DB_PASS=$(echo $SECRET | jq -r .password)
DB_ENDPOINT="YOUR_RDS_ENDPOINT"  # from CDK outputs

# Create .env file
cat > /app/backend/.env << ENVEOF
DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@${DB_ENDPOINT}:5432/trading_agent
ENVEOF

# Append SSM parameters
aws ssm get-parameters-by-path --path '/trading-agent/' --region us-east-1 --output json | \
  jq -r '.Parameters[] | (.Name | split("/")[-1]) + "=" + .Value' >> /app/backend/.env

# Build and run Docker container
cd /app/backend
docker build -t trading-agent .
docker run -d \
  --restart always \
  --env-file /app/backend/.env \
  -p 127.0.0.1:8000:8000 \
  --name trading-agent \
  trading-agent

# Verify it's running
docker ps
docker logs -f trading-agent

# Exit SSH
exit
```

### Step 7: Add HTTP Port to Security Group

```bash
# Get security group ID
export SG_ID=$(aws cloudformation describe-stacks \
  --stack-name TradingAgentNetwork \
  --query 'Stacks[0].Outputs[?contains(OutputKey,`BackendSG`)].OutputValue' \
  --output text | cut -d'=' -f2)

# Add port 80 for HTTP access
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0
```

### Step 8: Deploy Frontend

```bash
cd frontend

# Create production environment file
cat > .env.production << EOF
VITE_API_BASE_URL=http://$EC2_IP
EOF

# Install dependencies and build
npm install
npm run build

# Deploy to S3
export BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name TradingAgentFrontend \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text)

export DIST_ID=$(aws cloudformation describe-stacks \
  --stack-name TradingAgentFrontend \
  --query 'Stacks[0].Outputs[?OutputKey==`DistributionId`].OutputValue' \
  --output text)

aws s3 sync dist/ s3://$BUCKET_NAME --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id $DIST_ID \
  --paths "/*"
```

### Step 9: Access Your Application

Get your CloudFront URL:

```bash
aws cloudformation describe-stacks \
  --stack-name TradingAgentFrontend \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text
```

Open the URL in your browser and create your first user account!

---

## 🔧 Post-Deployment

### Verify Everything Works

```bash
# Test backend health
curl http://$EC2_IP/health

# Test API docs
open http://$EC2_IP/docs

# Test frontend
open https://YOUR_CLOUDFRONT_URL
```

### Enable GitHub Actions CI/CD (Optional)

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

```
AWS_DEPLOY_ROLE_ARN=arn:aws:iam::YOUR_ACCOUNT:role/github-actions-deploy
S3_BUCKET_NAME=trading-agent-frontend-YOUR_ACCOUNT_ID
CLOUDFRONT_DISTRIBUTION_ID=YOUR_DIST_ID
CLOUDFRONT_DOMAIN=YOUR_CLOUDFRONT_URL
EC2_SSH_PRIVATE_KEY=<contents of ~/.ssh/trading-agent-key.pem>
VITE_API_BASE_URL=http://YOUR_EC2_IP
```

Then uncomment the workflow triggers in `.github/workflows/deploy-*.yml`.

---

## 📊 Deployed Infrastructure Details

### Network (TradingAgentNetwork)
- **VPC**: 10.0.0.0/16
- **Public Subnets**: 2 AZs for EC2
- **Private Isolated Subnets**: 2 AZs for RDS
- **Security Groups**: 
  - Backend SG: SSH (your IP), HTTP (0.0.0.0/0), HTTPS (0.0.0.0/0)
  - Database SG: PostgreSQL 5432 (from Backend SG only)

### Database (TradingAgentDatabase)
- **Engine**: PostgreSQL 16
- **Instance**: db.t3.micro (free tier)
- **Storage**: 20 GB GP2 SSD (encrypted)
- **Backup**: 1 day retention (free tier max)
- **Multi-AZ**: Disabled (single AZ for free tier)
- **Access**: Private isolated subnet only

### Application (TradingAgentApp)
- **Instance**: EC2 t3.micro (free tier)
- **OS**: Amazon Linux 2023
- **Docker**: Backend runs in container
- **Nginx**: Reverse proxy on port 80
- **Elastic IP**: Static public IP
- **IAM Role**: SSM access, Secrets Manager read, CloudWatch metrics

### Frontend (TradingAgentFrontend)
- **Storage**: S3 private bucket
- **CDN**: CloudFront distribution
- **SSL**: Free ACM certificate (via CloudFront)
- **Cache**: Aggressive caching for static assets

---

## 💰 Cost Breakdown

### Year 1 (Free Tier)
| Resource | Monthly Cost |
|----------|-------------|
| EC2 t3.micro (750 hrs) | $0 |
| RDS db.t3.micro (750 hrs) | $0 |
| S3 (< 5 GB) | $0 |
| CloudFront (1 TB + 10M requests) | $0 |
| SSM Parameter Store (Standard) | $0 |
| Secrets Manager (1 secret) | $0 |
| Elastic IP (attached) | $0 |
| **TOTAL** | **~$0/month** |

### After Year 1
| Resource | Monthly Cost |
|----------|-------------|
| EC2 t3.micro | ~$8.35 |
| RDS db.t3.micro | ~$14.40 |
| S3 (< 5 GB) | ~$0.12 |
| CloudFront (always free) | $0 |
| SSM + Secrets Manager | $0 |
| Elastic IP | $0 |
| **TOTAL** | **~$23/month** |

---

## 🛠️ Maintenance

### Update Backend Code

```bash
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@$EC2_IP

# Pull latest code
cd /app
git pull origin main

# Rebuild and restart
cd backend
docker build -t trading-agent .
docker stop trading-agent
docker rm trading-agent
docker run -d \
  --restart always \
  --env-file /app/backend/.env \
  -p 127.0.0.1:8000:8000 \
  --name trading-agent \
  trading-agent
```

### Update Frontend

```bash
cd frontend
npm run build
aws s3 sync dist/ s3://$BUCKET_NAME --delete
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```

### View Logs

```bash
# Backend logs
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@$EC2_IP
docker logs -f trading-agent

# Nginx logs
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@$EC2_IP
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Update API Keys

```bash
# Update any SSM parameter
aws ssm put-parameter \
  --name "/trading-agent/ANTHROPIC_API_KEY" \
  --value "NEW_KEY" \
  --overwrite

# Restart backend to pick up changes
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@$EC2_IP
docker restart trading-agent
```

---

## 🗑️ Cleanup / Teardown

To completely remove all AWS resources:

```bash
cd cdk
source .venv/bin/activate

# Destroy all stacks
cdk destroy --all

# Remove bootstrap stack (optional)
aws cloudformation delete-stack --stack-name CDKToolkit
```

**Note**: This will delete:
- All EC2 instances
- RDS database (final snapshot created)
- S3 buckets (auto-deleted)
- CloudFront distributions
- All network resources

---

## 🐛 Troubleshooting

### Backend Not Starting

```bash
# Check container logs
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@$EC2_IP
docker logs trading-agent

# Check if .env file exists
cat /app/backend/.env

# Verify SSM parameters
aws ssm get-parameters-by-path --path "/trading-agent/" --region us-east-1
```

### Frontend Not Loading

```bash
# Check if files are in S3
aws s3 ls s3://$BUCKET_NAME/

# Check CloudFront distribution status
aws cloudfront get-distribution --id $DIST_ID
```

### Database Connection Issues

```bash
# Verify RDS is running
aws rds describe-db-instances --region us-east-1

# Check security group rules
aws ec2 describe-security-groups --region us-east-1
```

### API Not Accessible

```bash
# Check security group allows port 80
aws ec2 describe-security-groups --group-ids $SG_ID

# Check nginx is running
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@$EC2_IP
sudo systemctl status nginx
```

---

## 🔒 Security Best Practices

1. **Rotate API Keys Regularly**: Update SSM parameters every 90 days
2. **Use HTTPS**: Add a custom domain with ACM certificate
3. **Restrict SSH**: Update security group to only allow your IP
4. **Enable MFA**: Enable MFA on your AWS account
5. **Monitor Costs**: Set up AWS Budget alerts
6. **Enable CloudTrail**: Track all API calls
7. **Regular Backups**: RDS automated backups are enabled

---

## 📚 Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Backend API Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)
- [CDK Deployment Guide](cdk/DEPLOYMENT_GUIDE.md)
- [High-Level Design](documentation/HLD.md)

---

**Deployed on**: June 7, 2026
**Stack Version**: CDK v2.1126.0
**Region**: us-east-1
**Account**: 657347292520
