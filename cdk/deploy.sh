#!/bin/bash
#
# Trading Agent CDK Deployment Helper
# ====================================
# This script helps deploy the Trading Agent to AWS with interactive prompts.
#
# Usage:
#   ./deploy.sh               # Interactive mode
#   ./deploy.sh --auto        # Non-interactive (uses cdk.json values)
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if running in auto mode
AUTO_MODE=false
if [[ "$1" == "--auto" ]]; then
    AUTO_MODE=true
fi

print_header "Trading Agent - CDK Deployment"

# Step 1: Check prerequisites
print_info "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Install it: pip install awscli"
    exit 1
fi
print_success "AWS CLI installed"

if ! command -v cdk &> /dev/null; then
    print_error "CDK CLI not found. Install it: npm install -g aws-cdk"
    exit 1
fi
print_success "CDK CLI installed"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found"
    exit 1
fi
print_success "Python 3 installed"

if ! command -v jq &> /dev/null; then
    print_warning "jq not found (optional). Install it: brew install jq"
fi

# Step 2: Check AWS credentials
print_info "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Run: aws configure"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")
print_success "AWS Account: $AWS_ACCOUNT"
print_success "AWS Region: $AWS_REGION"

# Step 3: Check/update cdk.json
print_header "Configuration"

if [[ ! -f cdk.json ]]; then
    print_error "cdk.json not found. Are you in the cdk/ directory?"
    exit 1
fi

# Get current values from cdk.json
CURRENT_ACCOUNT=$(jq -r '.context.account // "YOUR_12_DIGIT_AWS_ACCOUNT_ID"' cdk.json)
CURRENT_REGION=$(jq -r '.context.region // "us-east-1"' cdk.json)
CURRENT_MY_IP=$(jq -r '.context.my_ip // "0.0.0.0/0"' cdk.json)
CURRENT_KEY=$(jq -r '.context.key_pair_name // "trading-agent-key"' cdk.json)
CURRENT_DOMAIN=$(jq -r '.context.domain_name // ""' cdk.json)

if [[ "$AUTO_MODE" == true ]]; then
    print_info "Running in auto mode with values from cdk.json"
    ACCOUNT=$CURRENT_ACCOUNT
    REGION=$CURRENT_REGION
    MY_IP=$CURRENT_MY_IP
    KEY_NAME=$CURRENT_KEY
    DOMAIN=$CURRENT_DOMAIN
else
    # Interactive prompts
    echo ""
    echo "Current configuration:"
    echo "  Account ID: $CURRENT_ACCOUNT"
    echo "  Region: $CURRENT_REGION"
    echo "  Your IP: $CURRENT_MY_IP"
    echo "  Key Pair: $CURRENT_KEY"
    echo "  Domain: ${CURRENT_DOMAIN:-"(none)"}"
    echo ""

    read -p "Update configuration? (y/N): " UPDATE_CONFIG
    if [[ "$UPDATE_CONFIG" =~ ^[Yy]$ ]]; then
        read -p "AWS Account ID [$AWS_ACCOUNT]: " ACCOUNT
        ACCOUNT=${ACCOUNT:-$AWS_ACCOUNT}

        read -p "AWS Region [$AWS_REGION]: " REGION
        REGION=${REGION:-$AWS_REGION}

        # Get public IP
        PUBLIC_IP=$(curl -s ifconfig.me || echo "")
        if [[ -n "$PUBLIC_IP" ]]; then
            DEFAULT_MY_IP="$PUBLIC_IP/32"
        else
            DEFAULT_MY_IP="0.0.0.0/0"
        fi
        read -p "Your public IP for SSH [$DEFAULT_MY_IP]: " MY_IP
        MY_IP=${MY_IP:-$DEFAULT_MY_IP}

        read -p "EC2 Key Pair Name [$CURRENT_KEY]: " KEY_NAME
        KEY_NAME=${KEY_NAME:-$CURRENT_KEY}

        read -p "Domain name (optional, leave empty for HTTP): " DOMAIN
        DOMAIN=${DOMAIN:-""}

        # Update cdk.json
        jq ".context.account = \"$ACCOUNT\" | .context.region = \"$REGION\" | .context.my_ip = \"$MY_IP\" | .context.key_pair_name = \"$KEY_NAME\" | .context.domain_name = \"$DOMAIN\"" cdk.json > cdk.json.tmp
        mv cdk.json.tmp cdk.json
        print_success "Configuration updated"
    else
        ACCOUNT=$CURRENT_ACCOUNT
        REGION=$CURRENT_REGION
        MY_IP=$CURRENT_MY_IP
        KEY_NAME=$CURRENT_KEY
        DOMAIN=$CURRENT_DOMAIN
    fi
fi

# Validate configuration
if [[ "$ACCOUNT" == "YOUR_12_DIGIT_AWS_ACCOUNT_ID" ]] || [[ -z "$ACCOUNT" ]]; then
    print_error "AWS Account ID not configured. Update cdk.json or run with prompts."
    exit 1
fi

# Step 4: Check EC2 key pair exists
print_info "Checking EC2 key pair: $KEY_NAME"
if ! aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" &> /dev/null; then
    print_warning "Key pair '$KEY_NAME' not found in AWS"
    print_info "Create it in AWS Console: EC2 → Key Pairs → Create Key Pair"
    print_info "Or run: aws ec2 create-key-pair --key-name $KEY_NAME --query 'KeyMaterial' --output text > ~/.ssh/$KEY_NAME.pem"

    if [[ "$AUTO_MODE" == false ]]; then
        read -p "Continue anyway? (y/N): " CONTINUE
        if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Step 5: Install Python dependencies
print_header "Installing Dependencies"

if [[ ! -d .venv ]]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv .venv
    print_success "Virtual environment created"
fi

print_info "Activating virtual environment..."
source .venv/bin/activate

if [[ ! -f .venv/.deps_installed ]]; then
    print_info "Installing Python dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    touch .venv/.deps_installed
    print_success "Dependencies installed"
else
    print_success "Dependencies already installed"
fi

# Step 6: CDK Bootstrap (if needed)
print_header "CDK Bootstrap"

BOOTSTRAP_STACK="CDKToolkit"
if aws cloudformation describe-stacks --stack-name "$BOOTSTRAP_STACK" --region "$REGION" &> /dev/null; then
    print_success "CDK already bootstrapped in $REGION"
else
    print_info "Bootstrapping CDK (one-time operation)..."
    cdk bootstrap aws://$ACCOUNT/$REGION
    print_success "CDK bootstrapped"
fi

# Step 7: Synthesize
print_header "Synthesizing CloudFormation Templates"

print_info "Running cdk synth..."
cdk synth > /dev/null
print_success "CloudFormation templates generated in cdk.out/"

# Step 8: Show what will be deployed
print_header "Deployment Plan"

echo "The following stacks will be deployed:"
echo ""
echo "  1. TradingAgentNetwork  - VPC, subnets, security groups"
echo "  2. TradingAgentDatabase - RDS PostgreSQL (db.t3.micro)"
echo "  3. TradingAgentApp      - EC2 t2.micro + Docker + nginx"
echo "  4. TradingAgentFrontend - S3 + CloudFront"
echo ""
echo "Estimated time: ~15 minutes"
echo "Estimated cost (Year 1): ~\$0-0.50/month (free tier)"
echo ""

if [[ "$AUTO_MODE" == false ]]; then
    read -p "Proceed with deployment? (y/N): " PROCEED
    if [[ ! "$PROCEED" =~ ^[Yy]$ ]]; then
        print_warning "Deployment cancelled"
        exit 0
    fi
fi

# Step 9: Deploy
print_header "Deploying to AWS"

print_info "Starting deployment... (this takes ~15 minutes)"
echo ""

if cdk deploy --all --require-approval never; then
    print_success "Deployment completed!"
else
    print_error "Deployment failed"
    exit 1
fi

# Step 10: Get outputs
print_header "Deployment Summary"

print_info "Fetching stack outputs..."
echo ""

# Get EC2 public IP
PUBLIC_IP=$(aws cloudformation describe-stacks \
    --stack-name TradingAgentApp \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`PublicIP`].OutputValue' \
    --output text 2>/dev/null || echo "")

# Get RDS endpoint
DB_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name TradingAgentDatabase \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`DBEndpoint`].OutputValue' \
    --output text 2>/dev/null || echo "")

# Get CloudFront URL
CF_URL=$(aws cloudformation describe-stacks \
    --stack-name TradingAgentFrontend \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [[ -n "$PUBLIC_IP" ]]; then
    echo "Backend API:"
    echo "  URL:     http://$PUBLIC_IP:8000"
    echo "  Docs:    http://$PUBLIC_IP:8000/docs"
    echo "  Health:  http://$PUBLIC_IP:8000/health"
    echo ""
    echo "SSH Access:"
    echo "  ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP"
    echo ""
fi

if [[ -n "$DB_ENDPOINT" ]]; then
    echo "Database:"
    echo "  Endpoint: $DB_ENDPOINT"
    echo ""
fi

if [[ -n "$CF_URL" ]]; then
    echo "Frontend:"
    echo "  URL: $CF_URL"
    echo ""
fi

# Step 11: Next steps
print_header "Next Steps"

echo "1. Update API keys in SSM Parameter Store:"
echo "   https://console.aws.amazon.com/systems-manager/parameters"
echo ""
echo "2. SSH to EC2 and restart backend:"
echo "   ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP"
echo "   docker restart trading-agent"
echo ""
echo "3. Run database migrations:"
echo "   docker exec -it trading-agent python -m scripts.migrate_db"
echo ""
echo "4. Create first user:"
echo "   docker exec -it trading-agent python -m scripts.seed_user --username admin --password 'YourPassword123!'"
echo ""
echo "5. Test login:"
echo "   curl -X POST http://$PUBLIC_IP:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"YourPassword123!\"}'"
echo ""
echo "For detailed instructions, see: DEPLOYMENT_GUIDE.md"
echo ""

print_success "Deployment complete! 🚀"
