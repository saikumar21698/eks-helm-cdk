# EKS Helm Deployment

CDK project using Projen to deploy an EKS cluster with environment-based Helm chart configuration.

## What it does

- EKS cluster
- SSM Parameter for storing environment config
- Lambda function that generates Helm values based on environment
- ingress-nginx Helm chart with different replica counts per environment

## Prerequisites

- Python 3.11+
- Node.js
- AWS CLI configured
- AWS account

## Setup

1. Install dependencies:
```bash
npx projen install
```

2. Bootstrap CDK (first time only):
```bash
npx projen deploy --require-approval never
```

## Deployment

Deploy with environment parameter:

```bash
# Development (1 replica)
npx projen deploy -c environment=development

# Staging (2 replicas)
npx projen deploy -c environment=staging

# Production (2 replicas)
npx projen deploy -c environment=production
```
## Projen Commands

```bash
npx projen                    # Synthesize project configuration
npx projen install            # Install dependencies
npx projen test               # Run tests
npx projen synth              # Synthesize CDK stack
npx projen deploy             # Deploy stack
npx projen destroy            # Destroy stack
```

## Project Structure

```
eks-helm-deployment/
├── app.py                      # CDK app entry point
├── .projenrc.js                # Projen configuration
├── requirements.txt            # Python dependencies
├── cdk.json                    # CDK configuration
├── README.md                   # Project documentation
├── packages/
│   ├── eks_helm_deployment/
│   │   ├── __init__.py
│   │   └── eks_helm_stack.py  # Main stack definition
│   └── lambda_functions/
│       ├── __init__.py
│       └── helm_value_generator/
│           ├── __init__.py
│           ├── index.py       # Lambda handler
│           └── requirements.txt
└── tests/
    ├── __init__.py
    ├── test_helm_value_generator.py
    └── conftest.py
```

## Cleanup

To destroy the stack and all resources:

```bash
npx projen destroy
```

## Environment Configuration

The environment parameter determines the replica count for the ingress-nginx controller:
- `development`: 1 replica
- `staging`: 2 replicas
- `production`: 2 replicas

The environment value is stored in SSM Parameter Store at `/platform/account/env` and read by the Lambda function to generate appropriate Helm values.
