import json
import os
import boto3


def generate_helm_values(environment):
    """Generate Helm values based on environment."""
    replica_map = {
        "development": 1,
        "staging": 2,
        "production": 2
    }
    return {
        "controller": {
            "replicaCount": replica_map.get(environment, 2)
        }
    }


def handler(event, context):
    """CloudFormation custom resource handler for Helm values generation."""
    print(f"Received event: {json.dumps(event)}")

    request_type = event.get("RequestType")
    physical_id = event.get("PhysicalResourceId", "HelmValuesGenerator")

    # Handle delete requests
    if request_type == "Delete":
        return {
            "Status": "SUCCESS",
            "PhysicalResourceId": physical_id,
            "StackId": event["StackId"],
            "RequestId": event["RequestId"],
            "LogicalResourceId": event["LogicalResourceId"],
            "Data": {}
        }

    try:
        # Get environment from SSM Parameter Store
        ssm_parameter_name = os.environ.get("SSM_PARAMETER_NAME", "/platform/account/env")
        ssm_client = boto3.client("ssm")
        response = ssm_client.get_parameter(Name=ssm_parameter_name)
        environment = response["Parameter"]["Value"]

        print(f"Environment from SSM: {environment}")

        # Generate Helm values
        helm_values = generate_helm_values(environment)
        print(f"Helm values: {json.dumps(helm_values)}")

        return {
            "Status": "SUCCESS",
            "PhysicalResourceId": physical_id,
            "StackId": event["StackId"],
            "RequestId": event["RequestId"],
            "LogicalResourceId": event["LogicalResourceId"],
            "Data": {
                "HelmValues.controller.replicaCount": helm_values["controller"]["replicaCount"]
            }
        }

    except ssm_client.exceptions.ParameterNotFound:
        error_message = f"SSM parameter {ssm_parameter_name} not found"
        print(f"Error: {error_message}")
        return {
            "Status": "FAILED",
            "Reason": error_message,
            "PhysicalResourceId": physical_id,
            "StackId": event["StackId"],
            "RequestId": event["RequestId"],
            "LogicalResourceId": event["LogicalResourceId"]
        }

    except Exception as e:
        error_message = f"Error: {str(e)}"
        print(error_message)
        return {
            "Status": "FAILED",
            "Reason": error_message,
            "PhysicalResourceId": physical_id,
            "StackId": event["StackId"],
            "RequestId": event["RequestId"],
            "LogicalResourceId": event["LogicalResourceId"]
        }
