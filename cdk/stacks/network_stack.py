"""
NetworkStack — VPC, public/private subnets, security groups
============================================================
Architecture decision (free-tier):
  - EC2 lives in the PUBLIC subnet with a tight security group.
    A NAT Gateway would cost ~$33/month — not free-tier friendly.
    Security is enforced by the security group (inbound only from
    your home IP for SSH, and the API port).
  - RDS lives in PRIVATE ISOLATED subnets — no internet route,
    only reachable from the EC2 security group.
"""
from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class NetworkStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        my_ip: str = self.node.try_get_context("my_ip") or "0.0.0.0/0"

        # ── VPC ──────────────────────────────────────────────────────────────
        # Two AZs for RDS subnet group requirement (needs ≥2 AZs).
        # nat_gateways=0 saves $33/month — EC2 uses its public IP for egress.
        self.vpc = ec2.Vpc(
            self, "TradingVPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            nat_gateways=0,   # Free tier — no NAT Gateway
            subnet_configuration=[
                # EC2 lives here — public IP gives internet access without NAT
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                # RDS lives here — no internet route, completely isolated
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )

        # ── EC2 Security Group ────────────────────────────────────────────────
        self.ec2_sg = ec2.SecurityGroup(
            self, "BackendSG",
            vpc=self.vpc,
            security_group_name="trading-agent-backend",
            description="Trading Agent EC2 — SSH from home + API from internet",
            allow_all_outbound=True,   # EC2 needs to call Anthropic, Finnhub, etc.
        )
        # SSH only from your home IP (set my_ip in cdk.json context)
        self.ec2_sg.add_ingress_rule(
            ec2.Peer.ipv4(my_ip),
            ec2.Port.tcp(22),
            "SSH from home",
        )
        # API port — lock down to specific IP in production or use CloudFront
        self.ec2_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(8000),
            "FastAPI",
        )
        # HTTPS if you add nginx + Let's Encrypt later
        self.ec2_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            "HTTPS",
        )

        # ── RDS Security Group ────────────────────────────────────────────────
        self.rds_sg = ec2.SecurityGroup(
            self, "DatabaseSG",
            vpc=self.vpc,
            security_group_name="trading-agent-rds",
            description="RDS PostgreSQL — only reachable from EC2",
            allow_all_outbound=False,
        )
        # Only EC2 can talk to PostgreSQL — not the internet
        self.rds_sg.add_ingress_rule(
            self.ec2_sg,
            ec2.Port.tcp(5432),
            "PostgreSQL from EC2 only",
        )

        # ── Outputs ───────────────────────────────────────────────────────────
        cdk.CfnOutput(self, "VpcId",   value=self.vpc.vpc_id)
        cdk.CfnOutput(self, "PublicSubnets",
                      value=",".join(s.subnet_id for s in self.vpc.public_subnets))
        cdk.CfnOutput(self, "IsolatedSubnets",
                      value=",".join(s.subnet_id for s in self.vpc.isolated_subnets))
