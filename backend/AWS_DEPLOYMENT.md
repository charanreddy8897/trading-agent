# AWS Deployment Guide

Complete guide for deploying the Trading Agent backend to AWS with proper authentication.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Authentication in AWS](#authentication-in-aws)
3. [Deployment Steps](#deployment-steps)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup (RDS)](#database-setup-rds)
6. [First-Time User Setup in Production](#first-time-user-setup-in-production)
7. [User Login Flow (Production)](#user-login-flow-production)
8. [Monitoring & Logs](#monitoring--logs)
9. [Scaling Considerations](#scaling-considerations)
10. [Security Best Practices](#security-best-practices)

---

## Architecture Overview

### Production Architecture

```
                           ┌─────────────────┐
                           │   Route 53      │
                           │  (DNS)          │
                           └────────┬────────┘
                                    │
                           ┌────────▼────────┐
                           │  CloudFront     │
                           │  (CDN)          │
                           └────────┬────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        │ HTTPS                     │                           │
        ▼                           ▼                           │
┌───────────────┐          ┌────────────────┐                  │
│ S3 + CloudFront│         │ Application     │                 │
│  (Frontend)    │         │ Load Balancer   │                 │
│  React SPA     │         │  (ALB)          │                 │
└───────────────┘          └────────┬───────┘                  │
                                    │                           │
                    ┌───────────────┼───────────────┐           │
                    │               │               │           │
              ┌─────▼──────┐  ┌────▼──────┐  ┌────▼──────┐   │
              │ ECS Task 1 │  │ECS Task 2 │  │ECS Task 3 │   │
              │ (Backend)  │  │(Backend)  │  │(Backend)  │   │
              └─────┬──────┘  └────┬──────┘  └────┬──────┘   │
                    │              │              │           │
                    └──────────────┼──────────────┘           │
                                   │                          │
                    ┌──────────────┼──────────────┐           │
                    │              │              │           │
                    ▼              ▼              ▼           │
            ┌───────────────────────────────────────┐         │
            │         RDS PostgreSQL                │         │
            │  (Multi-AZ for HA)                    │         │
            └───────────────────────────────────────┘         │
                                                               │
            ┌──────────────────────────────────────────────────┘
            │
            ▼
    ┌────────────────────┐     ┌──────────────────┐
    │  Secrets Manager   │     │  CloudWatch      │
    │  (API Keys, JWT)   │     │  (Logs, Metrics) │
    └────────────────────┘     └──────────────────┘
```

### Key Components

1. **ECS Fargate**: Runs backend containers (stateless, auto-scaling)
2. **RDS PostgreSQL**: Database (Multi-AZ for high availability)
3. **ALB**: Distributes traffic across backend tasks
4. **Secrets Manager**: Stores sensitive credentials
5. **CloudWatch**: Logs and metrics
6. **S3 + CloudFront**: Hosts frontend React app

---

## Authentication in AWS

### How JWT Authentication Works in Production

**Good News**: JWT authentication is **stateless** and works perfectly in distributed AWS environments!

#### Key Points

1. **No Session Storage Required**
   - Tokens contain all auth information (user ID, expiration)
   - No need for sticky sessions or shared session storage
   - Each backend instance can validate tokens independently

2. **Load Balancer Compatible**
   - ALB can route requests to any backend instance
   - Each instance validates JWT using the same `JWT_SECRET_KEY`
   - User can hit different instances on each request - it just works!

3. **TOTP (2FA) Still Works**
   - TOTP secret stored in database (RDS)
   - Any backend instance can validate TOTP codes
   - No local storage needed

### What Changes from Local to AWS?

| Component | Local Development | AWS Production |
|-----------|------------------|----------------|
| **Database** | Local PostgreSQL | RDS PostgreSQL |
| **Environment Variables** | `.env` file | Secrets Manager |
| **Logs** | `/tmp/trading-agent.log` | CloudWatch Logs |
| **Metrics** | CloudWatch (if configured) | CloudWatch Metrics |
| **HTTPS** | HTTP (localhost) | HTTPS (ALB + ACM Certificate) |
| **Domain** | `localhost:8000` | `api.yourdomain.com` |
| **CORS** | `http://localhost:5173` | `https://app.yourdomain.com` |

**Authentication Flow**: IDENTICAL! Same endpoints, same token format, same 2FA process.

---

## Deployment Steps

### Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI configured
3. Docker installed
4. Domain name (for SSL certificates)

### Step 1: Create RDS PostgreSQL Database

```bash
# Via AWS Console or CloudFormation
aws rds create-db-instance \
  --db-instance-identifier trading-agent-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 14.7 \
  --master-username trading_user \
  --master-user-password "STRONG_PASSWORD_HERE" \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name my-db-subnet-group \
  --backup-retention-period 7 \
  --multi-az \
  --publicly-accessible false
```

**Note down the endpoint**: `trading-agent-db.xxxxx.us-east-1.rds.amazonaws.com`

### Step 2: Store Secrets in AWS Secrets Manager

```bash
# Create secret for database URL
aws secretsmanager create-secret \
  --name trading-agent/database-url \
  --secret-string "postgresql://trading_user:PASSWORD@trading-agent-db.xxxxx.us-east-1.rds.amazonaws.com:5432/trading_agent"

# Create secret for JWT key
aws secretsmanager create-secret \
  --name trading-agent/jwt-secret-key \
  --secret-string "$(openssl rand -hex 32)"

# Create secret for API keys
aws secretsmanager create-secret \
  --name trading-agent/api-keys \
  --secret-string '{
    "ANTHROPIC_API_KEY": "sk-ant-...",
    "FINNHUB_API_KEY": "...",
    "ALPACA_API_KEY": "...",
    "ALPACA_SECRET_KEY": "..."
  }'
```

### Step 3: Build and Push Docker Image

```bash
# Build Docker image
cd backend
docker build -t trading-agent-backend:latest .

# Tag for ECR
docker tag trading-agent-backend:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/trading-agent:latest

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

# Push image
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/trading-agent:latest
```

### Step 4: Create ECS Task Definition

```json
{
  "family": "trading-agent-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/tradingAgentTaskRole",
  "containerDefinitions": [
    {
      "name": "trading-agent",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/trading-agent:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ALPACA_BASE_URL",
          "value": "https://paper-api.alpaca.markets"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:trading-agent/database-url"
        },
        {
          "name": "JWT_SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:trading-agent/jwt-secret-key"
        },
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:trading-agent/api-keys:ANTHROPIC_API_KEY::"
        },
        {
          "name": "FINNHUB_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:trading-agent/api-keys:FINNHUB_API_KEY::"
        },
        {
          "name": "ALPACA_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:trading-agent/api-keys:ALPACA_API_KEY::"
        },
        {
          "name": "ALPACA_SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:trading-agent/api-keys:ALPACA_SECRET_KEY::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/trading-agent",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "backend"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Step 5: Create ECS Service with ALB

```bash
# Create ECS service
aws ecs create-service \
  --cluster trading-agent-cluster \
  --service-name trading-agent-service \
  --task-definition trading-agent-backend \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-zzz],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/trading-agent-tg/xxxxx,containerName=trading-agent,containerPort=8000"
```

### Step 6: Configure ALB with HTTPS

1. **Request SSL Certificate** (AWS Certificate Manager):
   ```bash
   aws acm request-certificate \
     --domain-name api.yourdomain.com \
     --validation-method DNS
   ```

2. **Add HTTPS Listener to ALB**:
   ```bash
   aws elbv2 create-listener \
     --load-balancer-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/trading-agent-alb/xxxxx \
     --protocol HTTPS \
     --port 443 \
     --certificates CertificateArn=arn:aws:acm:us-east-1:123456789012:certificate/xxxxx \
     --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/trading-agent-tg/xxxxx
   ```

3. **Update Route 53**:
   ```bash
   # Point api.yourdomain.com to ALB
   aws route53 change-resource-record-sets \
     --hosted-zone-id Z1234567890ABC \
     --change-batch file://dns-change.json
   ```

---

## Environment Configuration

### Update CORS Settings

In `app/main.py`, update CORS origins for production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.yourdomain.com",  # Production frontend
        "http://localhost:5173",        # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Update Logging Configuration

CloudWatch automatically captures stdout/stderr. The existing structured logging works perfectly:

```python
# Logs automatically go to CloudWatch Logs
# View at: /ecs/trading-agent log group
logger.info("Request processed", extra={
    "request_id": request_id,
    "latency_ms": 45.2
})
```

---

## Database Setup (RDS)

### Initial Schema Setup

**Option 1: From Local Machine (One-Time)**

```bash
# SSH tunnel to RDS (if in private subnet)
ssh -i key.pem -L 5433:trading-agent-db.xxxxx.rds.amazonaws.com:5432 ec2-user@bastion-host

# Run migrations
DATABASE_URL="postgresql://trading_user:PASSWORD@localhost:5433/trading_agent" \
  python -m scripts.migrate_db
```

**Option 2: From ECS Task (Recommended)**

```bash
# Run one-off migration task
aws ecs run-task \
  --cluster trading-agent-cluster \
  --task-definition trading-agent-backend \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-zzz]}" \
  --overrides '{
    "containerOverrides": [{
      "name": "trading-agent",
      "command": ["python", "-m", "scripts.migrate_db"]
    }]
  }'
```

---

## First-Time User Setup in Production

### Create Initial Admin User

**You have 3 options:**

### Option 1: Via Bastion Host (Secure)

```bash
# SSH to bastion host
ssh -i key.pem ec2-user@bastion-host

# Install dependencies
pip install -r requirements.txt

# Run seed script
DATABASE_URL="postgresql://trading_user:PASSWORD@trading-agent-db.xxxxx.rds.amazonaws.com:5432/trading_agent" \
  python -m scripts.seed_user \
  --username admin \
  --password "StrongPassword123!"
```

### Option 2: Via ECS Exec (AWS Console)

```bash
# Enable ECS Exec on the service
aws ecs update-service \
  --cluster trading-agent-cluster \
  --service trading-agent-service \
  --enable-execute-command

# Connect to running container
aws ecs execute-command \
  --cluster trading-agent-cluster \
  --task TASK_ID \
  --container trading-agent \
  --interactive \
  --command "/bin/bash"

# Inside container:
python -m scripts.seed_user --username admin --password "StrongPassword123!"
```

### Option 3: Via Temporary API Endpoint (DEV ONLY)

Create a one-time admin endpoint (delete after first user):

```python
# app/main.py (TEMPORARY - DELETE AFTER USE)
@app.post("/admin/create-user", include_in_schema=False)
async def admin_create_user(username: str, password: str, admin_token: str, db: Session = Depends(get_db)):
    # Verify admin token from environment
    if admin_token != os.getenv("ADMIN_SETUP_TOKEN"):
        raise HTTPException(status_code=403)
    
    # Create user
    user = auth_service.create_user(db, username, password)
    return {"message": "User created", "username": user.username}
```

Then:
```bash
curl -X POST "https://api.yourdomain.com/admin/create-user?username=admin&password=StrongPassword123!&admin_token=SECRET_TOKEN"
```

**⚠️ DELETE THIS ENDPOINT IMMEDIATELY AFTER FIRST USER IS CREATED!**

---

## User Login Flow (Production)

### The Flow is IDENTICAL to Local Development!

```
User's Browser/App
       │
       │ POST /api/v1/auth/login
       │ {"username":"admin","password":"..."}
       ▼
   CloudFront
       │
       ▼
Application Load Balancer (HTTPS)
       │
       │ Round-robin to any backend instance
       ▼
┌──────┴──────┬──────────────┬──────────────┐
│ ECS Task 1  │  ECS Task 2  │  ECS Task 3  │
│             │              │              │
│ Validates   │  Validates   │  Validates   │
│ password    │  password    │  password    │
│ with RDS    │  with RDS    │  with RDS    │
└──────┬──────┴──────────────┴──────────────┘
       │
       │ Returns temp_token (JWT)
       ▼
    User's App
       │
       │ POST /api/v1/auth/totp
       │ {"temp_token":"...","code":"123456"}
       ▼
   ALB → Any ECS Task
       │
       │ Validates TOTP against RDS
       │ Returns access_token + refresh_token
       ▼
    User's App
       │
       │ All subsequent requests:
       │ Authorization: Bearer {access_token}
       ▼
   ALB → Any ECS Task
       │
       │ Validates JWT (no DB lookup needed!)
       ▼
   Protected Endpoint
```

### Example: Production Login

```bash
# Step 1: Login with password
curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "StrongPassword123!"
  }'

# Response:
# {
#   "status": "totp_required",
#   "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
# }

# Step 2: Verify TOTP
curl -X POST https://api.yourdomain.com/api/v1/auth/totp \
  -H "Content-Type: application/json" \
  -d '{
    "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "code": "123456"
  }'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer"
# }

# Step 3: Use access token
curl https://api.yourdomain.com/api/v1/screener/ranked \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**EXACTLY the same as local development**, just with `https://api.yourdomain.com` instead of `http://localhost:8000`!

---

## Monitoring & Logs

### CloudWatch Logs

View logs in AWS Console:
```
CloudWatch → Log Groups → /ecs/trading-agent
```

Or via CLI:
```bash
# Tail logs in real-time
aws logs tail /ecs/trading-agent --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /ecs/trading-agent \
  --filter-pattern "ERROR"

# Get specific request by ID
aws logs filter-log-events \
  --log-group-name /ecs/trading-agent \
  --filter-pattern "request_id=1a6ffa0a-2fb5-485b-832a-46ff44a6179d"
```

### CloudWatch Metrics

The MetricsPublisher automatically publishes to CloudWatch:

```python
# In app/core/metrics.py - already configured!
cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")
cloudwatch.put_metric_data(
    Namespace="TradingAgent/API",
    MetricData=[
        {
            "MetricName": "RequestCount",
            "Dimensions": [{"Name": "StatusClass", "Value": "2xx"}],
            "Value": count,
            "Unit": "Count"
        }
    ]
)
```

**View Metrics**:
- Go to CloudWatch → Metrics → TradingAgent/API
- Create dashboards for:
  - Request count (2xx, 4xx, 5xx)
  - Request latency (p50, p95, p99)
  - Error rate
  - Active users

### CloudWatch Alarms

```bash
# Alert on high error rate
aws cloudwatch put-metric-alarm \
  --alarm-name trading-agent-high-errors \
  --alarm-description "Alert when 5xx errors exceed 10/min" \
  --metric-name RequestCount \
  --namespace TradingAgent/API \
  --statistic Sum \
  --period 60 \
  --evaluation-periods 1 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=StatusClass,Value=5xx
```

---

## Scaling Considerations

### Auto-Scaling ECS Tasks

```json
{
  "ServiceName": "trading-agent-service",
  "ScalableTargetAction": {
    "MinCapacity": 2,
    "MaxCapacity": 10
  },
  "ScalingPolicies": [
    {
      "PolicyName": "cpu-scaling",
      "TargetTrackingScalingPolicyConfiguration": {
        "TargetValue": 70.0,
        "PredefinedMetricSpecification": {
          "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
        }
      }
    }
  ]
}
```

### Database Scaling (RDS)

- **Vertical**: Upgrade instance class (e.g., db.t3.micro → db.t3.small)
- **Horizontal**: Add read replicas for read-heavy workloads
- **Connection Pooling**: Already handled by SQLAlchemy

```python
# In app/core/database.py
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=5,           # Max connections per container
    max_overflow=10,       # Burst capacity
    pool_pre_ping=True,    # Validate connections before use
)
```

### JWT Token Validation (Zero Database Load)

Because JWT is stateless:
- ✅ Token validation = 0 database queries
- ✅ Can handle millions of requests
- ✅ Scales horizontally without limits

Only database hits:
- Login (password check)
- TOTP verification
- Data queries (screener, portfolio, etc.)

---

## Security Best Practices

### 1. Network Security

```
┌─────────────────────────────────────────────────────┐
│ VPC: 10.0.0.0/16                                    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │ Public Subnets (ALB Only)                  │    │
│  │ 10.0.1.0/24, 10.0.2.0/24                   │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │ Private Subnets (ECS Tasks)                │    │
│  │ 10.0.10.0/24, 10.0.11.0/24                 │    │
│  │ • No public IPs                             │    │
│  │ • Outbound via NAT Gateway                  │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │ Private Subnets (RDS)                      │    │
│  │ 10.0.20.0/24, 10.0.21.0/24                 │    │
│  │ • Accessible only from ECS tasks            │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Security Groups**:
- ALB SG: Allow 443 from `0.0.0.0/0`
- ECS SG: Allow 8000 from ALB SG only
- RDS SG: Allow 5432 from ECS SG only

### 2. Secrets Management

✅ **DO**: Use AWS Secrets Manager
```python
# ECS fetches secrets at container start
# No secrets in code or environment variables
```

❌ **DON'T**: Hardcode secrets in Dockerfile or task definition

### 3. IAM Roles

**ECS Task Execution Role** (for AWS service access):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "*"
    }
  ]
}
```

**ECS Task Role** (for app-level access):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```

### 4. SSL/TLS

- ✅ ALB handles SSL termination
- ✅ Use ACM for free certificates
- ✅ Enforce HTTPS (redirect HTTP → HTTPS)
- ✅ Use TLS 1.2+ only

### 5. Rate Limiting

Already implemented via `slowapi`:
```python
@limiter.limit("5/minute")
async def login(...):
    # Rate limited per IP
```

ALB also supports rate limiting:
```bash
aws elbv2 create-rule \
  --rule-arn ... \
  --conditions Field=http-request-method,Values=POST \
  --actions Type=fixed-response,FixedResponseConfig={StatusCode=429} \
  --rule-throttle RateLimit=100
```

### 6. Database Security

- ✅ Enable SSL for RDS connections
- ✅ Rotate passwords via Secrets Manager
- ✅ Enable automated backups (7-35 days)
- ✅ Enable Multi-AZ for production
- ✅ Use least-privilege database user

```python
# Update DATABASE_URL in Secrets Manager
DATABASE_URL=postgresql://trading_user:PASSWORD@host:5432/trading_agent?sslmode=require
```

---

## Cost Optimization

### Estimated Monthly Costs (US East-1)

| Service | Configuration | Cost |
|---------|--------------|------|
| **ECS Fargate** | 2 tasks (0.5 vCPU, 1GB RAM) 24/7 | ~$30 |
| **RDS PostgreSQL** | db.t3.micro Multi-AZ | ~$30 |
| **ALB** | 1 ALB + data transfer | ~$20 |
| **NAT Gateway** | 1 NAT Gateway + data | ~$35 |
| **CloudWatch Logs** | 10 GB ingestion + 1 month retention | ~$5 |
| **Secrets Manager** | 5 secrets | ~$2 |
| **S3 + CloudFront** | Frontend hosting | ~$5 |
| **Route 53** | 1 hosted zone | ~$0.50 |
| **ACM Certificate** | SSL certificate | FREE |
| **Total** | | **~$127/month** |

### Cost Savings Tips

1. **Use Fargate Spot** (70% discount):
   ```json
   "capacityProviderStrategy": [
     {
       "capacityProvider": "FARGATE_SPOT",
       "weight": 100
     }
   ]
   ```

2. **Schedule ECS tasks** (off during nights/weekends):
   ```bash
   # Scale to 0 at night
   aws application-autoscaling put-scheduled-action \
     --service-namespace ecs \
     --scheduled-action-name scale-down-night \
     --schedule "cron(0 22 * * ? *)" \
     --scalable-target-action MinCapacity=0,MaxCapacity=0
   ```

3. **Use RDS Reserved Instances** (save up to 60%)

4. **Optimize CloudWatch Logs** (shorter retention):
   ```bash
   aws logs put-retention-policy \
     --log-group-name /ecs/trading-agent \
     --retention-in-days 7
   ```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All API keys obtained and added to Secrets Manager
- [ ] RDS database created and accessible
- [ ] Docker image built and pushed to ECR
- [ ] ECS cluster created
- [ ] ALB created with target group
- [ ] SSL certificate requested and validated (ACM)
- [ ] Route 53 DNS configured
- [ ] Security groups configured (ALB, ECS, RDS)
- [ ] IAM roles created (task execution + task role)
- [ ] CloudWatch log group created

### Initial Deployment

- [ ] ECS task definition registered
- [ ] ECS service created with desired count = 2
- [ ] Database migrations run (via ECS task or bastion)
- [ ] First admin user created
- [ ] Health checks passing (ALB target group)
- [ ] Test login flow from production URL
- [ ] Test 2FA setup flow
- [ ] Verify CloudWatch logs appearing
- [ ] Verify CloudWatch metrics publishing

### Post-Deployment

- [ ] Set up CloudWatch alarms (errors, latency)
- [ ] Configure auto-scaling policies
- [ ] Test disaster recovery (RDS restore)
- [ ] Document runbooks for common issues
- [ ] Set up monitoring dashboard
- [ ] Schedule regular security audits
- [ ] Plan for regular database backups

---

## Troubleshooting Production Issues

### Issue: "Can't connect to database"

**Check**:
```bash
# 1. ECS task has correct security group
aws ecs describe-services --cluster trading-agent-cluster --services trading-agent-service

# 2. RDS security group allows ECS tasks
aws ec2 describe-security-groups --group-ids sg-xxxxx

# 3. Secret is correctly configured
aws secretsmanager get-secret-value --secret-id trading-agent/database-url

# 4. Test connection from ECS task
aws ecs execute-command --cluster trading-agent-cluster --task TASK_ID --container trading-agent --interactive --command "/bin/bash"
# Inside: pg_isready -h HOST -p 5432
```

### Issue: "Invalid token" in production

**Causes**:
1. JWT_SECRET_KEY mismatch between deployments
2. Token signed with old secret after rotation

**Fix**:
```bash
# Verify all tasks use same secret
aws ecs describe-tasks --cluster trading-agent-cluster --tasks TASK_ID_1 TASK_ID_2

# Force redeployment to pick up new secret
aws ecs update-service --cluster trading-agent-cluster --service trading-agent-service --force-new-deployment
```

### Issue: "TOTP codes not working"

**Cause**: Container time drift (rare with Fargate)

**Check**:
```bash
# Connect to container
aws ecs execute-command --cluster trading-agent-cluster --task TASK_ID --container trading-agent --interactive --command "/bin/bash"

# Inside container:
date -u  # Should match actual UTC time

# If drift > 30 seconds, TOTP will fail
```

**Fix**: Fargate handles time sync automatically; force restart:
```bash
aws ecs update-service --cluster trading-agent-cluster --service trading-agent-service --force-new-deployment
```

### Issue: "503 Service Unavailable from ALB"

**Causes**:
1. All ECS tasks unhealthy (failing health checks)
2. No tasks running (scaled to 0)

**Check**:
```bash
# Check target health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:...

# Check task status
aws ecs list-tasks --cluster trading-agent-cluster --service-name trading-agent-service
aws ecs describe-tasks --cluster trading-agent-cluster --tasks TASK_ID
```

**Fix**:
```bash
# View logs for crash reason
aws logs tail /ecs/trading-agent --follow

# Force new deployment
aws ecs update-service --cluster trading-agent-cluster --service trading-agent-service --force-new-deployment
```

---

## Summary: Authentication in AWS

### Key Takeaways

1. **JWT authentication is stateless** → Works perfectly with load balancers and auto-scaling
2. **TOTP secrets stored in RDS** → Any backend instance can validate codes
3. **Login flow is identical** → Just use HTTPS and production domain
4. **Secrets in AWS Secrets Manager** → No `.env` files in production
5. **Logs in CloudWatch** → Searchable by request_id
6. **Metrics auto-published** → 2xx/4xx/5xx counts + latency

### The Bottom Line

**You don't need to change ANY authentication code for AWS deployment!**

The system is designed to be cloud-native from day one:
- ✅ Stateless JWT tokens
- ✅ Database-backed user data
- ✅ No session storage
- ✅ Horizontal scaling ready
- ✅ Load balancer compatible

Just deploy the Docker image, configure secrets, and it works! 🚀

---

**Questions?** Check:
- Backend README: `backend/README.md`
- Connection test: `python -m scripts.test_connections`
- CloudWatch logs: `/ecs/trading-agent`
- Health endpoint: `https://api.yourdomain.com/health`
