import boto3
import json
import re
from typing import Dict, Optional


def create_session(region: str, profile: Optional[str] = None) -> boto3.Session:
    boto_args: Dict[str, str] = {"region_name": region}
    if profile:
        boto_args["profile_name"] = profile
    return boto3.Session(**boto_args)


def get_ssm_parameter(session: boto3.Session, param_name: str) -> Optional[str]:
    try:
        ssm_client = session.client("ssm")
        response = ssm_client.get_parameter(Name=param_name)
        return response["Parameter"]["Value"]
    except ssm_client.exceptions.ParameterNotFound:
        return None
    except Exception as e:
        print(f"Error fetching SSM parameter {param_name}: {e}")
        return None


def get_load_balancer_certificate_arn(
    session: boto3.Session, load_balancer_name: str
) -> Optional[str]:
    try:
        elb_client = session.client("elbv2")

        response = elb_client.describe_load_balancers(Names=[load_balancer_name])
        if not response.get("LoadBalancers"):
            print(f"Load balancer '{load_balancer_name}' not found")
            return None

        lb_arn = response["LoadBalancers"][0]["LoadBalancerArn"]

        listeners = elb_client.describe_listeners(LoadBalancerArn=lb_arn)

        for listener in listeners.get("Listeners", []):
            if listener.get("Port") == 443:
                for cert in listener.get("Certificates", []):
                    if "CertificateArn" in cert:
                        return cert["CertificateArn"]

        print(f"No HTTPS listener (port 443) found for load balancer '{load_balancer_name}'")
        return None
    except Exception as e:
        print(f"Error fetching certificate ARN from load balancer {load_balancer_name}: {e}")
        return None


def get_db_password_sm_name(session: boto3.Session) -> str:
    try:
        secrets_client = session.client("secretsmanager")

        response = secrets_client.list_secrets()
        secrets = response.get("SecretList", [])

        target_secret = None
        for secret in secrets:
            tags = secret.get("Tags", [])
            for tag in tags:
                if (
                    tag.get("Key") == "aws:cloudformation:logical-id"
                    and tag.get("Value") == "DBConnectionStringSecret"
                ):
                    target_secret = secret
                    break
            if target_secret:
                break

        if not target_secret:
            raise ValueError(
                "Could not find secret with tag 'aws:cloudformation:logical-id=DBConnectionStringSecret'"
            )

        return target_secret["Name"]
    except Exception as e:
        raise ValueError(f"Error getting secret name from Secrets Manager: {e}")
