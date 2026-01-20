from aws_cdk import (
    Stack,
    aws_ssm as ssm,
    aws_lambda as lambda_,
    aws_eks as eks,
    aws_ec2 as ec2,
    aws_iam,
    custom_resources as cr,
    CustomResource,
)
from aws_cdk.lambda_layer_kubectl_v28 import KubectlV28Layer
from constructs import Construct


class EksHelmStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # validate environment input
        valid_environments = ["development", "staging", "production"]
        if environment not in valid_environments:
            raise ValueError(f"Invalid environment: {environment}. Must be one of {valid_environments}")

        # SSM parameter to store environment
        self.env_parameter = ssm.StringParameter(
            self, "EnvironmentParameter",
            parameter_name="/platform/account/env",
            string_value=environment,
            description="Deployment environment"
        )

        # Lambda function to generate helm values
        self.lambda_function = lambda_.Function(
            self, "HelmValueGenerator",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_asset("packages/lambda_functions/helm_value_generator"),
            environment={
                "SSM_PARAMETER_NAME": self.env_parameter.parameter_name
            }
        )

        # give lambda permission to read SSM
        self.env_parameter.grant_read(self.lambda_function)

        # custom resource provider
        self.helm_values_provider = cr.Provider(
            self, "HelmValuesProvider",
            on_event_handler=self.lambda_function
        )

        # custom resource to get helm values
        self.helm_values_resource = CustomResource(
            self, "HelmValuesResource",
            service_token=self.helm_values_provider.service_token
        )

        # EKS cluster
        self.cluster = eks.Cluster(
            self, "EKSCluster",
            version=eks.KubernetesVersion.V1_28,
            default_capacity=0,
            cluster_name="eks-cluster",
            kubectl_layer=KubectlV28Layer(self, "KubectlLayer")
        )

        self.cluster.add_nodegroup_capacity(
            "DefaultCapacity",
            instance_types=[ec2.InstanceType("t3.micro")],
            desired_size=2,
            min_size=1,
            max_size=3
        )

        # Grant admin access to test user
        self.cluster.aws_auth.add_user_mapping(
            user=aws_iam.User.from_user_name(self, "TestUser", "test"),
            groups=["system:masters"]
        )

        # install ingress-nginx helm chart
        self.ingress_chart = self.cluster.add_helm_chart(
            "IngressNginx",
            chart="ingress-nginx",
            release="nginx",
            repository="https://kubernetes.github.io/ingress-nginx",
            namespace="ingress-nginx",
            create_namespace=True,
            values={
                "controller": {
                    "replicaCount": self.helm_values_resource.get_att("HelmValues.controller.replicaCount")
                }
            }
        )

        # set dependencies
        self.ingress_chart.node.add_dependency(self.helm_values_resource)
        self.helm_values_resource.node.add_dependency(self.env_parameter)
