# EKS Helm Deployment

CDK project using Projen to deploy an EKS cluster with environment-based Helm chart configuration.

**Why Projen?** Projen manages project configuration, dependencies, and build tasks through code instead of manual file editing. It ensures consistent project structure and simplifies common operations like testing, deployment, and dependency management across the team.

## What it does

- EKS cluster
- SSM Parameter for storing environment config
- Lambda function that generates Helm values based on environment
- ingress-nginx Helm chart with different replica counts per environment

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

## Environment Configuration

The environment parameter determines the replica count for the ingress-nginx controller:
- `development`: 1 replica
- `staging`: 2 replicas
- `production`: 2 replicas

The environment value is stored in SSM Parameter Store at `/platform/account/env` and read by the Lambda function to generate appropriate Helm values.

## Key Code Snippets

### Custom Resource with Environment Property

```python
# packages/eks_helm_deployment/eks_helm_stack.py
self.helm_values_resource = CustomResource(
    self, "HelmValuesResource",
    service_token=self.helm_values_provider.service_token,
    properties={"Environment": environment}  # Triggers update on environment change
)
```

### Lambda Function - Helm Value Generator

```python
# packages/lambda_functions/helm_value_generator/index.py
def on_event(event, context):
    request_type = event['RequestType']
    
    if request_type in ['Create', 'Update']:
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(Name='/platform/account/env')
        environment = response['Parameter']['Value']
        
        replica_count = 1 if environment == 'development' else 2
        
        return {
            'PhysicalResourceId': 'helm-values-generator',
            'Data': {
                'replicaCount': str(replica_count)
            }
        }
```

### Helm Chart Deployment

```python
# packages/eks_helm_deployment/eks_helm_stack.py
helm_chart = eks_cluster.add_helm_chart(
    f"nginx-{environment}",
    chart="ingress-nginx",
    repository="https://kubernetes.github.io/ingress-nginx",
    namespace="ingress-nginx",
    create_namespace=True,
    values={
        "controller": {
            "replicaCount": Token.as_number(
                self.helm_values_resource.get_att_string("replicaCount")
            )
        }
    }
)
```
