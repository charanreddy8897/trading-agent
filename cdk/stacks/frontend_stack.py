"""
FrontendStack - S3 + CloudFront + ACM SSL + optional Route53
=============================================================
Cost (permanent always-free tier, not just 12 months):
  CloudFront : 1 TB data transfer + 10M requests/month → $0
  S3         : 5 GB free (12 months), then ~$0.10/month  → ~$0
  ACM cert   : free when used with CloudFront             → $0
  Route53 HZ : $0.50/month (only if you add a domain)

Deploy frontend after CDK:
  cd frontend && npm run build
  aws s3 sync dist/ s3://<BucketName> --delete
  aws cloudfront create-invalidation --distribution-id <DistId> --paths "/*"

Or use the GitHub Actions workflow: .github/workflows/deploy-frontend.yml
"""
from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    aws_certificatemanager as acm,
    aws_cloudfront         as cf,
    aws_cloudfront_origins as origins,
    aws_route53            as r53,
    aws_route53_targets    as r53_targets,
    aws_s3                 as s3,
    aws_s3_deployment      as s3deploy,
)
from constructs import Construct


class FrontendStack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        domain_name: str | None = None,   # e.g. "trading.yourdomain.com"  (optional)
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # -- S3 Bucket (private - CloudFront is the only entry point) ---------
        self.bucket = s3.Bucket(
            self, "FrontendBucket",
            bucket_name=f"trading-agent-frontend-{self.account}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=False,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        # -- Origin Access Control (OAC) - modern S3+CloudFront auth ----------
        oac = cf.CfnOriginAccessControl(
            self, "OAC",
            origin_access_control_config=cf.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name="trading-agent-oac",
                origin_access_control_origin_type="s3",
                signing_behavior="always",
                signing_protocol="sigv4",
            ),
        )

        # -- ACM Certificate (free - only valid when used with CloudFront) -----
        # Only created when you provide a domain_name.
        # Certificate must be in us-east-1 for CloudFront (CDK handles this).
        certificate = None
        if domain_name:
            # Requires Route53 hosted zone for DNS validation (auto-handled by CDK)
            hosted_zone = r53.HostedZone.from_lookup(
                self, "HostedZone",
                domain_name=".".join(domain_name.split(".")[-2:]),  # apex domain
            )
            certificate = acm.DnsValidatedCertificate(
                self, "Certificate",
                domain_name=domain_name,
                hosted_zone=hosted_zone,
                region="us-east-1",   # CloudFront requires us-east-1
                cleanup_route53_records=True,
            )

        # -- CloudFront Distribution -------------------------------------------
        dist_kwargs: dict = dict(
            default_behavior=cf.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(
                    self.bucket, origin_access_control_id=oac.ref,
                ),
                viewer_protocol_policy=cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cf.CachePolicy.CACHING_OPTIMIZED,
                allowed_methods=cf.AllowedMethods.ALLOW_GET_HEAD,
                compress=True,
            ),
            # SPA routing - return index.html for all 403/404 (React Router)
            error_responses=[
                cf.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=cdk.Duration.seconds(0),
                ),
                cf.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=cdk.Duration.seconds(0),
                ),
            ],
            default_root_object="index.html",
            price_class=cf.PriceClass.PRICE_CLASS_100,  # US + EU only - cheapest
            http_version=cf.HttpVersion.HTTP2_AND_3,
            minimum_protocol_version=cf.SecurityPolicyProtocol.TLS_V1_2_2021,
            comment="Trading Agent Frontend",
        )

        if domain_name and certificate:
            dist_kwargs["domain_names"] = [domain_name]
            dist_kwargs["certificate"]  = certificate

        self.distribution = cf.Distribution(self, "CDN", **dist_kwargs)

        # Fix: attach OAC to the S3 origin (L1 workaround - CDK L2 limitation)
        cfn_dist = self.distribution.node.default_child
        cfn_dist.add_property_override(
            "DistributionConfig.Origins.0.OriginAccessControlId", oac.ref
        )
        cfn_dist.add_property_override(
            "DistributionConfig.Origins.0.S3OriginConfig.OriginAccessIdentity", ""
        )

        # Grant CloudFront read access to the bucket
        self.bucket.add_to_resource_policy(
            cdk.aws_iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[self.bucket.arn_for_objects("*")],
                principals=[cdk.aws_iam.ServicePrincipal("cloudfront.amazonaws.com")],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{self.distribution.distribution_id}"
                    }
                },
            )
        )

        # -- Route53 DNS record (only if domain + hosted zone provided) ---------
        if domain_name and certificate:
            r53.ARecord(
                self, "AliasRecord",
                zone=hosted_zone,
                record_name=domain_name,
                target=r53.RecordTarget.from_alias(
                    r53_targets.CloudFrontTarget(self.distribution)
                ),
            )

        # -- Outputs -----------------------------------------------------------
        cdk.CfnOutput(self, "BucketName",
                      value=self.bucket.bucket_name,
                      description="S3 bucket - upload your React build here")
        cdk.CfnOutput(self, "CloudFrontURL",
                      value=f"https://{self.distribution.distribution_domain_name}",
                      description="Your frontend URL")
        cdk.CfnOutput(self, "DistributionId",
                      value=self.distribution.distribution_id,
                      description="Used for cache invalidation after deploy")
        cdk.CfnOutput(self, "DeployCommand",
                      value=(
                          f"cd frontend && npm run build && "
                          f"aws s3 sync dist/ s3://{self.bucket.bucket_name} --delete && "
                          f"aws cloudfront create-invalidation "
                          f"--distribution-id {self.distribution.distribution_id} --paths '/*'"
                      ),
                      description="One-liner to build and deploy the frontend")
        if domain_name:
            cdk.CfnOutput(self, "CustomDomain", value=f"https://{domain_name}")
