# Trading Agent - AWS CDK Infrastructure

Deploy the Trading Agent to AWS using Infrastructure as Code (CDK).

---

## 🚀 Quick Start

```bash
cd cdk
./deploy.sh
```

The script guides you through everything!

---

## 📚 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete step-by-step guide
- **[CDK_VS_DEPLOYMENT_GUIDE.md](CDK_VS_DEPLOYMENT_GUIDE.md)** - Architecture comparison
- **[CHANGES.md](CHANGES.md)** - Recent CDK changes
- **[../backend/AWS_DEPLOYMENT.md](../backend/AWS_DEPLOYMENT.md)** - Production architecture

---

## 🏗️ Architecture

```
Internet
  │
  ├── CloudFront (free 1TB/mo) ──► S3 (React frontend)
  │
  └── EC2 t2.micro (public subnet)
        │ nginx :443 (Let's Encrypt SSL)
        │ → FastAPI :8000
        │
        └── RDS PostgreSQL db.t3.micro (isolated private subnet)
```

**4 Stacks** (~15 minutes total):
1. Network (VPC, subnets, security groups)
2. Database (RDS PostgreSQL)
3. App (EC2 + Docker + nginx)
4. Frontend (S3 + CloudFront)

---

## 💰 Cost

| Resource | Year 1 | After Year 1 |
|---|---|---|
| EC2 t2.micro | $0 (750 hrs/mo free) | ~$8.35/mo |
| RDS db.t3.micro | $0 (750 hrs/mo free) | ~$14.40/mo |
| S3 (< 5 GB) | $0 (5 GB free) | ~$0.12/mo |
| CloudFront | **$0 forever** (1 TB + 10M req) | $0 |
| ACM SSL cert | $0 | $0 |
| SSM Parameter Store | $0 (standard tier) | $0 |
| Elastic IP | $0 (when attached) | $0 |
| Route53 hosted zone | $0.50/mo | $0.50/mo |
| Domain | ~$1/mo (amortised) | ~$1/mo |
| **Total** | **~$0-1.50/mo** | **~$25/mo** |

## One-Time Setup

### 1. Prerequisites

```bash
# Install CDK CLI
npm install -g aws-cdk

# Install Python CDK dependencies
cd cdk
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure AWS CLI
aws configure
# Enter: AWS Access Key ID, Secret, region (us-east-1), output (json)
```

### 2. Edit cdk.json

```json
{
  "account":       "123456789012",        ← your AWS account ID
  "my_ip":         "1.2.3.4/32",          ← your home IP (find at whatismyip.com)
  "key_pair_name": "trading-agent-key",   ← create in EC2 console → Key Pairs
  "domain_name":   "trading.yourdomain.com"  ← leave "" if no domain yet
}
```

### 3. Create EC2 Key Pair

```
AWS Console → EC2 → Key Pairs → Create key pair
Name: trading-agent-key
Type: ED25519
Format: .pem
Download and save to ~/.ssh/trading-agent-key.pem
chmod 400 ~/.ssh/trading-agent-key.pem
```

### 4. Bootstrap & Deploy

```bash
cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1
cdk deploy --all
```

Takes ~15 minutes. Outputs include:
- EC2 Elastic IP
- CloudFront URL
- SSH command
- S3 bucket name
- CloudFront distribution ID

### 5. Fill in API Keys (SSM Parameter Store)

After deploy, go to AWS Console → Systems Manager → Parameter Store.
Find `/trading-agent/*` and fill in the real values for:
- `ANTHROPIC_API_KEY`
- `FINNHUB_API_KEY`
- `ALPACA_API_KEY` / `ALPACA_SECRET_KEY`
- `SLACK_BOT_TOKEN`
- `JWT_SECRET_KEY` (generate: `openssl rand -hex 32`)
- `ROBINHOOD_SYNC_KEY`

Then SSH in and restart the container:
```bash
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@YOUR_ELASTIC_IP
docker restart trading-agent
```

### 6. Create your user (one-time)

```bash
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@YOUR_ELASTIC_IP
cd /app
docker exec trading-agent python -m scripts.seed_user \
  --username charan \
  --password "your-strong-password-min-12-chars"
```

### 7. Deploy the frontend

```bash
# Build React app
cd frontend
npm run build

# Deploy to S3 + invalidate CloudFront cache
aws s3 sync dist/ s3://BUCKET_NAME_FROM_CDK_OUTPUT --delete
aws cloudfront create-invalidation \
  --distribution-id DIST_ID_FROM_CDK_OUTPUT \
  --paths "/*"
```

---

## Adding a Custom Domain (Optional — $0.50/month)

### Via Route53

1. Buy a domain (Route53, Namecheap, Cloudflare — any registrar)
2. Create a Route53 Hosted Zone: `$0.50/month`
3. Point your domain's nameservers to Route53's NS records
4. Set `"domain_name": "trading.yourdomain.com"` in `cdk.json`
5. `cdk deploy TradingAgentFrontend TradingAgentApp`

CDK will automatically:
- Create the ACM SSL certificate (free)
- Validate it via DNS
- Attach it to CloudFront
- Create an A-alias record in Route53
- Configure nginx + Let's Encrypt on EC2 for the API

---

## GitHub Actions CI/CD

Add these secrets to your GitHub repo (Settings → Secrets):

| Secret | Value |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | IAM role ARN that GitHub Actions assumes |
| `S3_BUCKET_NAME` | From CDK output `TradingAgentFrontend.BucketName` |
| `CLOUDFRONT_DISTRIBUTION_ID` | From CDK output `TradingAgentFrontend.DistributionId` |
| `CLOUDFRONT_DOMAIN` | From CDK output `TradingAgentFrontend.CloudFrontURL` |
| `EC2_SSH_PRIVATE_KEY` | Contents of `~/.ssh/trading-agent-key.pem` |
| `VITE_API_BASE_URL` | `https://api.yourdomain.com` or `http://YOUR_EC2_IP:8000` |

After setup: every push to `main` auto-deploys frontend to S3+CloudFront and backend to EC2.

---

## Useful Commands

```bash
# View logs
docker logs -f trading-agent

# Restart backend
docker restart trading-agent

# Update backend code
cd /app && git pull && docker build -t trading-agent ./backend
docker stop trading-agent && docker rm trading-agent
docker run -d --restart always --env-file .env -p 8000:8000 --name trading-agent trading-agent

# Check nginx
sudo nginx -t
sudo systemctl status nginx

# Check SSL cert
sudo certbot certificates

# Renew SSL (auto, but manual trigger)
sudo certbot renew

# Destroy everything
cdk destroy --all
```
