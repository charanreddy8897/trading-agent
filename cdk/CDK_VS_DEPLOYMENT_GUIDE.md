# CDK Stacks vs AWS Deployment Guide

Comparison of what's already configured in CDK vs the production architecture described in AWS_DEPLOYMENT.md

---

## Quick Answer

**Your CDK stacks use a different (simpler) architecture optimized for FREE TIER cost savings:**

| Component | AWS_DEPLOYMENT.md (Production) | Your CDK Stacks (Free Tier) |
|-----------|--------------------------------|----------------------------|
| **Compute** | ECS Fargate (~$30/month) | EC2 t2.micro (FREE) |
| **Load Balancer** | ALB (~$20/month) | nginx on EC2 (FREE) |
| **NAT Gateway** | NAT Gateway (~$35/month) | None - EC2 in public subnet (FREE) |
| **Secrets** | Secrets Manager (~$2/month) | SSM Parameter Store (FREE) |
| **Total Cost** | ~$127/month | **~$0-1.50/month** (year 1) |

---

## Detailed Comparison

### ✅ What's ALREADY Configured in CDK

#### 1. **Network Stack** (`cdk/stacks/network_stack.py`)

**Configured**:
- ✅ VPC with public and isolated subnets
- ✅ Security groups for EC2 and RDS
- ✅ EC2 in public subnet (no NAT Gateway needed)
- ✅ RDS in isolated private subnet (no internet access)

**Differences from AWS_DEPLOYMENT.md**:
- ❌ No ALB (using nginx on EC2 instead)
- ❌ No private subnet with NAT Gateway (cost savings)

#### 2. **Database Stack** (`cdk/stacks/database_stack.py`)

**Configured**:
- ✅ RDS PostgreSQL 16 (db.t3.micro - FREE TIER)
- ✅ 20 GB storage (free tier)
- ✅ Automated backups (7 days)
- ✅ Credentials stored in Secrets Manager
- ✅ Single-AZ (Multi-AZ costs 2x)

**Differences from AWS_DEPLOYMENT.md**:
- ❌ No Multi-AZ (for cost savings - not HA)
- ✅ Aurora Serverless v2 upgrade path (commented out - costs $43+/month)

#### 3. **App Stack** (`cdk/stacks/app_stack.py`)

**Configured**:
- ✅ EC2 t2.micro instance (FREE TIER - 750 hrs/month)
- ✅ Docker + Docker Compose installation
- ✅ nginx reverse proxy
- ✅ Let's Encrypt SSL certificate (automated)
- ✅ API keys stored in SSM Parameter Store (FREE)
- ✅ Database credentials from Secrets Manager
- ✅ CloudWatch Logs integration
- ✅ IAM role with permissions for SSM, Secrets Manager, CloudWatch
- ✅ Elastic IP (free when attached)
- ✅ User data script that auto-deploys backend

**Differences from AWS_DEPLOYMENT.md**:
- ❌ No ECS Fargate (using EC2 + Docker instead)
- ❌ No ALB (using nginx on EC2 instead)
- ❌ No auto-scaling (single instance)

#### 4. **Frontend Stack** (`cdk/stacks/frontend_stack.py`)

**Configured**:
- ✅ S3 bucket for static hosting
- ✅ CloudFront distribution (ALWAYS FREE - 1TB + 10M requests/month)
- ✅ ACM certificate for HTTPS (free)
- ✅ Route 53 integration (if domain configured)

**Same as AWS_DEPLOYMENT.md**: ✅ Identical!

---

## Architecture Comparison

### AWS_DEPLOYMENT.md Architecture (Production, ~$127/month)

```
Internet
    │
    ├─→ CloudFront (Frontend) → S3
    │
    └─→ Route 53 → ALB (HTTPS) → ECS Fargate (2+ tasks)
                                      │
                                      ├─→ RDS Multi-AZ
                                      ├─→ Secrets Manager
                                      └─→ CloudWatch
```

**Pros**:
- ✅ Highly available (Multi-AZ RDS, multiple ECS tasks)
- ✅ Auto-scaling (ECS can scale 2-10+ tasks)
- ✅ Zero-downtime deployments
- ✅ Load balanced across multiple instances

**Cons**:
- ❌ Costs ~$127/month
- ❌ More complex to set up

---

### Your CDK Stacks Architecture (Free Tier, ~$0-1.50/month)

```
Internet
    │
    ├─→ CloudFront (Frontend) → S3
    │
    └─→ Route 53 → EC2 (nginx + Docker + FastAPI)
                        │
                        ├─→ RDS Single-AZ
                        ├─→ SSM Parameter Store
                        ├─→ Secrets Manager (DB only)
                        └─→ CloudWatch
```

**Pros**:
- ✅ **FREE TIER** (~$0-1.50/month year 1)
- ✅ Simpler architecture
- ✅ Still production-ready for small/medium scale
- ✅ Easy to SSH and debug

**Cons**:
- ❌ Single point of failure (one EC2 instance)
- ❌ No auto-scaling
- ❌ Downtime during deployments (need to restart Docker container)
- ❌ Less HA (Single-AZ RDS)

---

## Authentication: Works Identically in Both!

**Good News**: Authentication flow is **IDENTICAL** in both architectures!

| Auth Component | AWS_DEPLOYMENT.md | Your CDK Stacks |
|----------------|-------------------|-----------------|
| **JWT Tokens** | ✅ Stateless | ✅ Stateless |
| **TOTP (2FA)** | ✅ Works | ✅ Works |
| **User Data** | RDS PostgreSQL | RDS PostgreSQL |
| **Login Flow** | Same | Same |
| **API Endpoints** | Same | Same |

**Why it works**:
- JWT is stateless (no session storage needed)
- TOTP secrets stored in RDS (shared between instances... or just one instance in your case)
- Same code, same endpoints, just different infrastructure

---

## What's NOT in CDK Stacks (vs AWS_DEPLOYMENT.md)

### ❌ Not Configured

1. **ECS Fargate**
   - CDK uses EC2 + Docker instead
   - Cheaper but manual scaling

2. **Application Load Balancer (ALB)**
   - CDK uses nginx on EC2 instead
   - Saves ~$20/month

3. **NAT Gateway**
   - CDK puts EC2 in public subnet with Elastic IP
   - Saves ~$35/month

4. **Multi-AZ RDS**
   - CDK uses Single-AZ for cost savings
   - Less HA but still reliable

5. **Auto-Scaling**
   - CDK is single instance
   - Can add later when needed

6. **Full Secrets Manager**
   - CDK uses SSM Parameter Store for API keys (free)
   - Only uses Secrets Manager for DB password

---

## How to Use Your CDK Stacks

### Deploy Everything

```bash
cd cdk

# 1. Install dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
npm install -g aws-cdk

# 2. Configure AWS credentials
aws configure

# 3. Set your preferences in cdk.json
cat > cdk.json << 'EOF'
{
  "app": "python3 app.py",
  "context": {
    "account": "YOUR_AWS_ACCOUNT_ID",
    "region": "us-east-1",
    "my_ip": "YOUR_HOME_IP/32",
    "key_pair_name": "trading-agent-key",
    "domain_name": "api.yourdomain.com"
  }
}
EOF

# 4. Bootstrap CDK (one-time per account/region)
cdk bootstrap

# 5. Deploy all stacks
cdk deploy --all
```

### After Deployment

#### 1. **Update SSM Parameter Store API Keys**

```bash
# Via AWS Console:
# Go to: Systems Manager → Parameter Store → /trading-agent/*
# Update each REPLACE_ME value with real API keys

# Or via CLI:
aws ssm put-parameter \
  --name /trading-agent/ANTHROPIC_API_KEY \
  --value "sk-ant-..." \
  --type String \
  --overwrite

aws ssm put-parameter \
  --name /trading-agent/FINNHUB_API_KEY \
  --value "your_key" \
  --type String \
  --overwrite

aws ssm put-parameter \
  --name /trading-agent/ALPACA_API_KEY \
  --value "your_key" \
  --type String \
  --overwrite

aws ssm put-parameter \
  --name /trading-agent/ALPACA_SECRET_KEY \
  --value "your_secret" \
  --type String \
  --overwrite

aws ssm put-parameter \
  --name /trading-agent/JWT_SECRET_KEY \
  --value "$(openssl rand -hex 32)" \
  --type String \
  --overwrite
```

#### 2. **Restart Backend to Load New Keys**

```bash
# SSH to EC2
ssh -i ~/.ssh/trading-agent-key.pem ec2-user@YOUR_ELASTIC_IP

# Restart Docker container
docker restart trading-agent

# Check logs
docker logs -f trading-agent
```

#### 3. **Run Database Migrations**

```bash
# On EC2 instance
cd /app
docker exec -it trading-agent python -m scripts.migrate_db
```

#### 4. **Create First User**

```bash
# On EC2 instance
docker exec -it trading-agent python -m scripts.seed_user \
  --username admin \
  --password "StrongPassword123!"
```

#### 5. **Test Login**

```bash
# Get your EC2 Elastic IP from CDK output
ELASTIC_IP=$(aws cloudformation describe-stacks \
  --stack-name TradingAgentApp \
  --query 'Stacks[0].Outputs[?OutputKey==`PublicIP`].OutputValue' \
  --output text)

# Test login (HTTP for now, HTTPS after Let's Encrypt)
curl -X POST http://$ELASTIC_IP:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "StrongPassword123!"
  }'
```

---

## Upgrading to Production Architecture

If you outgrow the free tier and need high availability:

### Option 1: Keep EC2, Add Multi-AZ RDS

```python
# In cdk/stacks/database_stack.py
self.db_instance = rds.DatabaseInstance(
    ...
    multi_az=True,  # Change from False
    instance_type=ec2.InstanceType.of(
        ec2.InstanceClass.T3, ec2.InstanceSize.SMALL,  # Upgrade from MICRO
    ),
)
```

**Cost**: +$15/month (Multi-AZ doubles RDS cost)

### Option 2: Upgrade to ECS Fargate + ALB

Create new stacks:
1. `ecs_stack.py` - ECS cluster + Fargate service
2. `alb_stack.py` - Application Load Balancer

**Follow AWS_DEPLOYMENT.md guide for full implementation**

**Cost**: ~$127/month (full production stack)

### Option 3: Hybrid Approach

- Keep EC2 backend (simple, cheap)
- Upgrade to Multi-AZ RDS only (for data reliability)
- Add CloudFront in front of EC2 (caching, DDoS protection)

**Cost**: ~$20/month

---

## Key Differences Summary

| Feature | CDK Stacks | AWS_DEPLOYMENT.md |
|---------|------------|-------------------|
| **Cost (Year 1)** | **~$0-1.50/month** ✅ | ~$127/month |
| **Free Tier** | ✅ Yes | ❌ No |
| **High Availability** | ❌ Single-AZ | ✅ Multi-AZ |
| **Auto-Scaling** | ❌ No | ✅ ECS auto-scales |
| **Load Balancer** | nginx | ALB |
| **Compute** | EC2 + Docker | ECS Fargate |
| **Secrets** | SSM (free) | Secrets Manager |
| **Deployment** | Manual restart | Zero-downtime |
| **Complexity** | ⭐⭐ Simple | ⭐⭐⭐⭐ Complex |
| **Auth Flow** | ✅ Same | ✅ Same |
| **Perfect For** | Students, MVPs, side projects | Production, high traffic |

---

## Authentication Still Works the Same!

**No matter which architecture you use**, the authentication flow is identical:

```bash
# Step 1: Login
curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"..."}'

# Step 2: TOTP
curl -X POST https://api.yourdomain.com/api/v1/auth/totp \
  -H "Content-Type: application/json" \
  -d '{"temp_token":"...","code":"123456"}'

# Step 3: Use access_token
curl https://api.yourdomain.com/api/v1/screener/ranked \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Why?**
- JWT is stateless (no load balancer dependency)
- TOTP stored in RDS (works with single or multiple instances)
- Same FastAPI backend code
- Same database schema

---

## Recommendations

### For Learning / MVP / Side Projects
✅ **Use your CDK stacks**
- Nearly free ($0-1.50/month year 1)
- Simple to understand and debug
- Perfect for development and testing
- Easy to SSH and troubleshoot

### For Production with < 1000 users
✅ **Use your CDK stacks + Multi-AZ RDS**
- ~$20/month
- Good balance of cost vs reliability
- Add CloudFront caching for performance

### For Production with > 1000 users or High Availability Required
✅ **Use AWS_DEPLOYMENT.md architecture**
- ~$127/month
- Full auto-scaling, load balancing, Multi-AZ
- Zero-downtime deployments
- Enterprise-grade

---

## Migration Path

**Start**: CDK Stacks (FREE)
↓
**Grow**: Add Multi-AZ RDS (~$20/month)
↓
**Scale**: Migrate to ECS + ALB (~$127/month)

You can migrate gradually without changing any application code! The authentication and API endpoints remain identical.

---

## Quick Deployment Checklist (CDK Stacks)

### Pre-Deployment
- [ ] Create AWS account
- [ ] Get API keys (Anthropic, Finnhub, Alpaca)
- [ ] Create EC2 key pair in AWS Console
- [ ] Update `cdk.json` with your account, IP, key name
- [ ] (Optional) Register domain and update `cdk.json`

### Deploy
- [ ] `cd cdk && cdk bootstrap`
- [ ] `cdk deploy --all`
- [ ] Wait ~10 minutes for EC2 user-data to complete

### Post-Deployment
- [ ] Update SSM Parameter Store with real API keys
- [ ] SSH to EC2 and restart Docker container
- [ ] Run database migrations
- [ ] Create first user
- [ ] Test login flow
- [ ] (Optional) Configure Route 53 DNS to point to Elastic IP

### Production Hardening
- [ ] Restrict SSH security group to your IP only
- [ ] Enable CloudWatch alarms
- [ ] Set up automated backups verification
- [ ] Test RDS restore procedure
- [ ] Document runbooks

---

## Summary

**Your CDK stacks are PERFECT for:**
- ✅ Learning and development
- ✅ Cost-conscious deployments
- ✅ MVPs and prototypes
- ✅ Small to medium scale (< 1000 users)

**AWS_DEPLOYMENT.md is BETTER for:**
- ✅ High availability requirements
- ✅ Auto-scaling needs
- ✅ Zero-downtime deployments
- ✅ Large scale (> 1000 users)

**Both use IDENTICAL authentication!** The login flow, JWT tokens, and 2FA work exactly the same way regardless of which architecture you choose. 🎉

---

**Next Steps:**
1. Deploy CDK stacks: `cd cdk && cdk deploy --all`
2. Update API keys in SSM Parameter Store
3. Follow the "After Deployment" section above
4. Test connection: `python -m scripts.test_connections`
5. Start trading! 🚀
