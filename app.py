#!/usr/bin/env python3
import os
import aws_cdk as cdk
from packages.eks_helm_deployment.eks_helm_stack import EksHelmStack

app = cdk.App()

# Get environment from context or use default
environment = app.node.try_get_context("environment") or "development"

# Validate environment value
valid_environments = ["development", "staging", "production"]
if environment not in valid_environments:
    raise ValueError(f"Invalid environment: {environment}. Must be one of {valid_environments}")

EksHelmStack(
    app,
    "EksHelmStack",
    environment=environment,
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    )
)

app.synth()
