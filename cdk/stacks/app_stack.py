"""
AppStack - EC2 t2.micro, IAM role, Elastic IP, SSM parameters
==============================================================
Free tier: t2.micro = 750 hrs/month for 12 months ($0).

The EC2 user-data script:
  1. Installs Docker + Docker Compose
  2. Pulls all API keys from SSM Parameter Store (free)
  3. Writes .env and starts the backend container

SSH access:
  Key pair name is read from CDK context "key_pair_name".
  Create one in EC2 console → Key Pairs, then set in cdk.json.
"""
from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    aws_ec2        as ec2,
    aws_iam        as iam,
    aws_logs       as logs,
    aws_ssm        as ssm,
)
from constructs import Construct

from stacks.network_stack  import NetworkStack
from stacks.database_stack import DatabaseStack


class AppStack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        network: NetworkStack,
        database: DatabaseStack,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        key_pair_name: str = self.node.try_get_context("key_pair_name") or "trading-agent-key"

        # -- CloudWatch Log Group ----------------------------------------------
        log_group = logs.LogGroup(
            self, "AppLogs",
            log_group_name="/trading-agent/backend",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # -- IAM Role for EC2 --------------------------------------------------
        role = iam.Role(
            self, "EC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                # SSM Session Manager - SSH without opening port 22 (optional)
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "CloudWatchAgentServerPolicy"
                ),
            ],
        )
        # Read secrets from Secrets Manager (DB credentials)
        database.db_secret.grant_read(role)

        # Read API keys from SSM Parameter Store (free tier)
        role.add_to_policy(iam.PolicyStatement(
            actions=["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"],
            resources=[f"arn:aws:ssm:{self.region}:{self.account}:parameter/trading-agent/*"],
        ))
        role.add_to_policy(iam.PolicyStatement(
            actions=["logs:CreateLogStream", "logs:PutLogEvents"],
            resources=[log_group.log_group_arn],
        ))
        # CloudWatch Metrics for MetricsPublisher
        role.add_to_policy(iam.PolicyStatement(
            actions=["cloudwatch:PutMetricData"],
            resources=["*"],
            conditions={
                "StringEquals": {
                    "cloudwatch:namespace": "TradingAgent/API"
                }
            }
        ))

        # -- SSM Parameters (free - Standard tier) ----------------------------
        # Store all API keys here instead of in .env committed to git.
        # After deploy, fill these in via AWS Console → SSM → Parameter Store.
        ssm_params = {
            "ANTHROPIC_API_KEY":   "REPLACE_ME",
            "FINNHUB_API_KEY":     "REPLACE_ME",
            "ALPACA_API_KEY":      "REPLACE_ME",
            "ALPACA_SECRET_KEY":   "REPLACE_ME",
            "ALPACA_BASE_URL":     "https://paper-api.alpaca.markets",
            "SLACK_BOT_TOKEN":     "REPLACE_ME_optional",
            "SLACK_CHANNEL_BRIEFING": "REPLACE_ME_optional",
            "SLACK_CHANNEL_ALERTS":   "REPLACE_ME_optional",
            "SLACK_CHANNEL_ORDERS":   "REPLACE_ME_optional",
            "SLACK_CHANNEL_EMERGENCY": "REPLACE_ME_optional",
            "JWT_SECRET_KEY":      "REPLACE_ME_generate_with_openssl_rand_hex_32",
            "ROBINHOOD_SYNC_KEY":  "REPLACE_ME_generate_with_openssl_rand_hex_32",
            "TRADING_MODE":        "paper",
            "LOG_LEVEL":           "INFO",
            "RH_USERNAME":         "REPLACE_ME_optional_deprecated",
            "RH_PASSWORD":         "REPLACE_ME_optional_deprecated",
            "RH_TOTP":             "REPLACE_ME_optional_deprecated",
        }
        for name, placeholder in ssm_params.items():
            ssm.StringParameter(
                self, f"Param{name.replace('_', '')}",
                parameter_name=f"/trading-agent/{name}",
                string_value=placeholder,
                description=f"Trading Agent - {name}",
                tier=ssm.ParameterTier.STANDARD,   # Free
            )

        # -- User Data (runs on first boot) ------------------------------------
        db_endpoint = database.db_instance.db_instance_endpoint_address
        region      = self.region
        secret_arn  = database.db_secret.secret_arn

        domain_name: str = self.node.try_get_context("domain_name") or ""

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            # -- System packages -----------------------------------------------
            "yum update -y",
            "yum install -y docker git jq nginx certbot python3-certbot-nginx",
            "systemctl enable --now docker",
            "usermod -aG docker ec2-user",

            # Docker Compose v2
            'curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose',
            "chmod +x /usr/local/bin/docker-compose",

            # -- Pull app code -------------------------------------------------
            "git clone https://github.com/charanreddy8897/trading-agent.git /app",
            "cd /app && git checkout main",

            # -- Fetch DB credentials from Secrets Manager ---------------------
            f'SECRET=$(aws secretsmanager get-secret-value --secret-id "{secret_arn}" --region {region} --query SecretString --output text)',
            'DB_USER=$(echo $SECRET | jq -r .username)',
            'DB_PASS=$(echo $SECRET | jq -r .password)',

            # -- Write .env from SSM + Secrets Manager -------------------------
            f'cat > /app/backend/.env << ENVEOF',
            f'DATABASE_URL=postgresql://${{DB_USER}}:${{DB_PASS}}@{db_endpoint}:5432/trading_agent',
            'ENVEOF',
            f"aws ssm get-parameters-by-path --path '/trading-agent/' --region {region} --output json | "
            r"jq -r '.Parameters[] | (.Name | split(\"/\")[-1]) + \"=\" + .Value' >> /app/backend/.env",

            # -- Build and start FastAPI backend (Docker) ----------------------
            "cd /app/backend && docker build -t trading-agent .",
            "docker run -d --restart always --env-file /app/backend/.env -p 127.0.0.1:8000:8000 --name trading-agent trading-agent",

            # Wait for backend to be ready
            "for i in {1..30}; do curl -f http://localhost:8000/health && break || sleep 2; done",

            # -- nginx reverse proxy -------------------------------------------
            # Routes HTTPS → FastAPI on :8000
            "mkdir -p /etc/nginx/conf.d",
            f"""cat > /etc/nginx/conf.d/trading-agent.conf << 'NGINXEOF'
server {{
    listen 80;
    server_name {domain_name or '_'};

    location / {{
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }}
}}
NGINXEOF""",
            "nginx -t && systemctl enable --now nginx",

            # -- Let's Encrypt SSL (only when domain_name is set) -------------
            # Certbot reads the nginx config and handles the ACME challenge.
            # After cert issuance nginx is reloaded with HTTPS config.
            *(
                [
                    f"certbot --nginx -d {domain_name} "
                    "--non-interactive --agree-tos "
                    f"--email admin@{domain_name.split('.',1)[-1]} "
                    "--redirect",
                    # Auto-renew via cron (certbot installs this automatically)
                ]
                if domain_name else
                ["echo 'No domain set - skipping Let'\\''s Encrypt (HTTP only)'"]
            ),

            # -- CloudWatch agent ----------------------------------------------
            "yum install -y amazon-cloudwatch-agent",
        )

        # -- EC2 Instance (t3.micro - free tier) -------------------------------
        self.instance = ec2.Instance(
            self, "BackendEC2",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.MICRO,  # Free tier
            ),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            vpc=network.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=network.ec2_sg,
            role=role,
            user_data=user_data,
            key_name=key_pair_name,
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(
                        20,                          # 30 GB free tier, 20 GB is plenty
                        volume_type=ec2.EbsDeviceVolumeType.GP2,
                        encrypted=True,
                        delete_on_termination=True,
                    ),
                )
            ],
        )

        # -- Elastic IP (free when attached to running instance) ---------------
        eip = ec2.CfnEIP(self, "ElasticIP", instance_id=self.instance.instance_id)

        # -- Outputs -----------------------------------------------------------
        cdk.CfnOutput(self, "PublicIP",
                      value=eip.ref,
                      description="Elastic IP - put this in your DNS")
        cdk.CfnOutput(self, "APIUrl",
                      value=f"http://{eip.ref}:8000",
                      description="FastAPI base URL")
        cdk.CfnOutput(self, "SSHCommand",
                      value=f"ssh -i ~/.ssh/{key_pair_name}.pem ec2-user@{eip.ref}",
                      description="SSH into the instance")
        cdk.CfnOutput(self, "SwaggerDocs",
                      value=f"http://{eip.ref}:8000/docs",
                      description="Interactive API docs")
