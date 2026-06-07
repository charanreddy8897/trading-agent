#!/usr/bin/env python3
"""
Trading Agent — AWS CDK Application
====================================
Four stacks, deployed in order:
  1. TradingAgentNetwork   — VPC, subnets, security groups
  2. TradingAgentDatabase  — RDS PostgreSQL 16 (free tier)
  3. TradingAgentApp       — EC2 t2.micro, nginx, Let's Encrypt
  4. TradingAgentFrontend  — S3 + CloudFront (permanently free tier)

Free-tier cost estimate (first 12 months):
  EC2 t2.micro          → $0   (750 hrs/month free)
  RDS db.t3.micro       → $0   (750 hrs/month free, 20 GB storage)
  S3                    → $0   (5 GB free)
  CloudFront            → $0   (1 TB + 10M requests/month ALWAYS free)
  ACM SSL certificate   → $0   (free with CloudFront)
  Elastic IP            → $0   (free when attached to running instance)
  SSM Parameter Store   → $0   (standard tier is free)
  CloudWatch basic      → $0
  Route53 hosted zone   → $0.50/month  ← only cost if you add a domain
  Domain registration   → ~$1/month amortised (buy from any registrar)
  ─────────────────────────────────────────────────
  Total year 1          → ~$0–$1.50/month

After 12 months:
  EC2 t2.micro          → ~$8.35/month
  RDS db.t3.micro       → ~$14.40/month
  S3 (< 5 GB)           → ~$0.12/month
  CloudFront            → $0  (always free tier)
  Route53               → $0.50/month
  Domain                → ~$1/month
  ─────────────────────────────────────────────────
  Total after year 1    → ~$24/month

Deploy:
  cd cdk
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  npm install -g aws-cdk          # install CDK CLI
  aws configure                   # set your AWS credentials
  cdk bootstrap                   # one-time per account/region
  cdk deploy --all                # deploy all stacks
"""
import aws_cdk as cdk

from stacks.network_stack  import NetworkStack
from stacks.database_stack import DatabaseStack
from stacks.app_stack      import AppStack
from stacks.frontend_stack import FrontendStack

app = cdk.App()

env = cdk.Environment(
    account=app.node.try_get_context("account"),
    region=app.node.try_get_context("region") or "us-east-1",
)

# Optional: set your domain in cdk.json context as "domain_name": "trading.yourdomain.com"
domain_name: str | None = app.node.try_get_context("domain_name")

network  = NetworkStack(app,  "TradingAgentNetwork",  env=env)
database = DatabaseStack(app, "TradingAgentDatabase", network=network, env=env)
compute  = AppStack(app,      "TradingAgentApp",      network=network, database=database, env=env)
frontend = FrontendStack(app, "TradingAgentFrontend", domain_name=domain_name, env=env)

# Deployment order
compute.add_dependency(database)
database.add_dependency(network)
# frontend is independent of the backend stacks

cdk.Tags.of(app).add("Project", "TradingAgent")
cdk.Tags.of(app).add("Owner",   "charan")
cdk.Tags.of(app).add("Env",     "prod")

app.synth()
