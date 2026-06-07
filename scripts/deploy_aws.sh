#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Trading Agent — AWS EC2 Deployment Script
#
# Run this ONCE on a fresh EC2 instance (Amazon Linux 2023 or Ubuntu 22.04).
# After setup, use the daily commands at the bottom to manage the service.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Config (edit before running) ─────────────────────────────────────────────
APP_DIR="/home/ec2-user/trading_agent"   # where the repo lives on EC2
COMPOSE_FILE="docker-compose.yml"

# ── 1. Install Docker + Compose ───────────────────────────────────────────────
echo "=== Installing Docker ==="
sudo yum update -y 2>/dev/null || sudo apt-get update -y
sudo yum install -y docker git 2>/dev/null || sudo apt-get install -y docker.io git

sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
newgrp docker

# Docker Compose v2
sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
     -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo "=== Docker $(docker --version) ==="
echo "=== Compose $(docker-compose --version) ==="

# ── 2. Clone / pull repo ──────────────────────────────────────────────────────
echo "=== Deploying app ==="
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR" && git pull
else
    git clone https://github.com/YOUR_GITHUB_USERNAME/trading_agent.git "$APP_DIR"
    cd "$APP_DIR"
fi

# ── 3. Create .env from AWS Secrets Manager ───────────────────────────────────
# Uncomment this block if you store secrets in AWS Secrets Manager:
#
# echo "=== Pulling secrets ==="
# aws secretsmanager get-secret-value \
#     --secret-id trading-agent-env \
#     --query SecretString \
#     --output text | python3 -c "
# import sys, json
# d = json.load(sys.stdin)
# with open('.env', 'w') as f:
#     for k, v in d.items():
#         f.write(f'{k}={v}\n')
# "

# ── 4. Build and start ────────────────────────────────────────────────────────
echo "=== Building containers ==="
docker-compose -f "$COMPOSE_FILE" build --no-cache backend

echo "=== Starting services ==="
docker-compose -f "$COMPOSE_FILE" up -d

echo "=== Waiting for health check ==="
sleep 10
curl -sf http://localhost:8000/health && echo " ✓ Backend healthy" || echo " ✗ Backend not ready"

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "API:  http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "Docs: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000/docs"
echo "=========================================="
echo ""
echo "Daily commands:"
echo "  Logs:    docker-compose logs -f backend"
echo "  Restart: docker-compose restart backend"
echo "  Update:  git pull && docker-compose up -d --build backend"
echo "  Status:  docker-compose ps"
