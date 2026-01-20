import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../packages/lambda_functions/helm_value_generator'))
from index import handler, generate_helm_values


@pytest.fixture
def lambda_context():
    context = Mock()
    context.log_stream_name = "test-log-stream"
    return context


@pytest.fixture
def cfn_event():
    return {
        "RequestType": "Create",
        "RequestId": "test-request-id",
        "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack/guid",
        "LogicalResourceId": "HelmValuesResource",
        "ResourceProperties": {}
    }


def test_development_environment_replica_count(lambda_context, cfn_event):
    with patch('boto3.client') as mock_boto3:
        mock_ssm = Mock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "development"}}
        mock_boto3.return_value = mock_ssm

        response = handler(cfn_event, lambda_context)

        assert response["Status"] == "SUCCESS"
        assert response["Data"]["HelmValues.controller.replicaCount"] == 1


def test_staging_environment_replica_count(lambda_context, cfn_event):
    with patch('boto3.client') as mock_boto3:
        mock_ssm = Mock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "staging"}}
        mock_boto3.return_value = mock_ssm

        response = handler(cfn_event, lambda_context)

        assert response["Status"] == "SUCCESS"
        assert response["Data"]["HelmValues.controller.replicaCount"] == 2


def test_production_environment_replica_count(lambda_context, cfn_event):
    with patch('boto3.client') as mock_boto3:
        mock_ssm = Mock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "production"}}
        mock_boto3.return_value = mock_ssm

        response = handler(cfn_event, lambda_context)

        assert response["Status"] == "SUCCESS"
        assert response["Data"]["HelmValues.controller.replicaCount"] == 2


def test_helm_values_format():
    result = generate_helm_values("development")

    assert isinstance(result, dict)
    assert "controller" in result
    assert "replicaCount" in result["controller"]
    assert isinstance(result["controller"]["replicaCount"], int)


def test_ssm_parameter_not_found(lambda_context, cfn_event):
    with patch('boto3.client') as mock_boto3:
        mock_ssm = Mock()
        mock_ssm.exceptions.ParameterNotFound = Exception
        mock_ssm.get_parameter.side_effect = mock_ssm.exceptions.ParameterNotFound()
        mock_boto3.return_value = mock_ssm

        response = handler(cfn_event, lambda_context)

        assert response["Status"] == "FAILED"
        assert "not found" in response["Reason"]


def test_delete_event_succeeds(lambda_context, cfn_event):
    cfn_event["RequestType"] = "Delete"

    response = handler(cfn_event, lambda_context)

    assert response["Status"] == "SUCCESS"
    assert response["Data"] == {}
