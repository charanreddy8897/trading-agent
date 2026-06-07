"""
DatabaseStack — RDS PostgreSQL (free tier) with optional Aurora upgrade path
=============================================================================
Using RDS PostgreSQL db.t3.micro (FREE TIER):
  - 750 hours/month free for 12 months
  - 20 GB SSD storage free
  - Automated backups, minor version upgrades

Aurora Serverless v2 (NOT free tier, uncomment to upgrade):
  - Minimum: 0.5 ACU × $0.12/ACU-hr = ~$43/month
  - Scales to zero is NOT available on v2 (minimum is 0.5 ACU)
  - Only worth it at scale for auto-scaling read replicas
"""
from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    aws_ec2   as ec2,
    aws_rds   as rds,
    aws_secretsmanager as sm,
)
from constructs import Construct

from stacks.network_stack import NetworkStack


class DatabaseStack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        network: NetworkStack,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── DB Credentials (Secrets Manager) ─────────────────────────────────
        self.db_secret = sm.Secret(
            self, "DBSecret",
            secret_name="trading-agent/db-credentials",
            description="RDS master credentials for Trading Agent",
            generate_secret_string=sm.SecretStringGenerator(
                secret_string_template='{"username": "trading_user"}',
                generate_string_key="password",
                exclude_punctuation=True,
                password_length=32,
            ),
        )

        # ── Subnet Group (uses the isolated private subnets) ──────────────────
        subnet_group = rds.SubnetGroup(
            self, "DBSubnetGroup",
            vpc=network.vpc,
            description="Trading Agent RDS subnet group",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
        )

        # ── RDS PostgreSQL — FREE TIER ────────────────────────────────────────
        self.db_instance = rds.DatabaseInstance(
            self, "PostgreSQL",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16,
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.MICRO,  # Free tier
            ),
            vpc=network.vpc,
            subnet_group=subnet_group,
            security_groups=[network.rds_sg],
            credentials=rds.Credentials.from_secret(self.db_secret),
            database_name="trading_agent",

            # Free tier storage
            allocated_storage=20,         # 20 GB free
            storage_type=rds.StorageType.GP2,
            storage_encrypted=True,

            # Free tier settings
            multi_az=False,               # Single AZ — multi-AZ doubles the cost
            publicly_accessible=False,    # Private — only EC2 can reach it
            auto_minor_version_upgrade=True,
            deletion_protection=False,    # Easy cleanup for dev/student
            backup_retention=cdk.Duration.days(7),
            removal_policy=cdk.RemovalPolicy.SNAPSHOT,  # Snapshot on delete
        )

        # ── AURORA UPGRADE PATH (uncomment when you outgrow RDS) ─────────────
        # Cost: ~$43+/month — NOT free tier
        #
        # self.aurora_cluster = rds.DatabaseCluster(
        #     self, "Aurora",
        #     engine=rds.DatabaseClusterEngine.aurora_postgres(
        #         version=rds.AuroraPostgresEngineVersion.VER_16_1,
        #     ),
        #     writer=rds.ClusterInstance.serverless_v2("Writer"),
        #     serverless_v2_min_capacity=0.5,
        #     serverless_v2_max_capacity=4,
        #     vpc=network.vpc,
        #     vpc_subnets=ec2.SubnetSelection(
        #         subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
        #     ),
        #     security_groups=[network.rds_sg],
        #     credentials=rds.Credentials.from_secret(self.db_secret),
        #     default_database_name="trading_agent",
        #     deletion_protection=False,
        #     removal_policy=cdk.RemovalPolicy.SNAPSHOT,
        # )

        # ── Outputs ───────────────────────────────────────────────────────────
        cdk.CfnOutput(self, "DBEndpoint",
                      value=self.db_instance.db_instance_endpoint_address,
                      description="RDS endpoint — used in DATABASE_URL")
        cdk.CfnOutput(self, "DBSecretArn",
                      value=self.db_secret.secret_arn,
                      description="Secrets Manager ARN for DB credentials")
        cdk.CfnOutput(self, "DBName", value="trading_agent")
