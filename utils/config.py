from dataclasses import dataclass
from typing import List, Optional
import json
import sys


@dataclass
class DatabaseConfig:
    db_cluster_identifier: Optional[str] = None
    delete_protection_enabled: Optional[bool] = None
    instance_class: Optional[str] = None
    connection_string_ssm_arn: Optional[str] = None
    connection_string_ssm_kms_arn: Optional[str] = None


@dataclass
class TagConfig:
    key: Optional[str] = None
    value: Optional[str] = None


@dataclass
class LoadBalancerConfig:
    certificate_arn: Optional[str] = None
    scheme: Optional[str] = None
    ssl_policy: Optional[str] = None
    subnet_placement: Optional[str] = None
    tag: Optional[TagConfig] = None


@dataclass
class ProxyConfig:
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    no_proxy: Optional[str] = None


@dataclass
class SlackConfig:
    enabled: Optional[bool] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    signing_secret: Optional[str] = None


@dataclass
class OidcArgs:
    client_id: Optional[str] = None
    client_credentials: Optional[str] = None
    identity_provider_host: Optional[str] = None


@dataclass
class SamlArgs:
    metadata: Optional[str] = None
    dynamic: Optional[bool] = None
    name_id_format: Optional[str] = None
    update_on_install: Optional[bool] = None


@dataclass
class SSOConfig:
    admin_login: Optional[str] = None
    sso_type: Optional[str] = None
    oidc_args: Optional[OidcArgs] = None
    saml_args: Optional[SamlArgs] = None
    update_on_install: Optional[bool] = None


@dataclass
class TLSConfig:
    server_certificate_secrets_manager_arn: Optional[str] = None
    ca_certificates: Optional[List[str]] = None


@dataclass
class VpcConfig:
    use_custom_vpc: Optional[bool] = None
    vpc_cidr_block: str = None
    vpc_id: str = None
    subnet_mask_size: str = None
    private_subnet_ids: str = None
    public_subnet_ids: str = None
    drain_security_group_id: str = None
    load_balancer_security_group_id: str = None
    server_security_group_id: str = None
    scheduler_security_group_id: str = None
    installation_task_security_group_id: str = None
    database_security_group_id: str = None
    availability_zones: str = None


@dataclass
class S3BucketReplicationConfig:
    enabled: Optional[bool] = None
    replica_kms_key_arn: Optional[str] = None
    states_bucket_arn: Optional[str] = None
    run_logs_bucket_arn: Optional[str] = None
    modules_bucket_arn: Optional[str] = None
    policy_inputs_bucket_arn: Optional[str] = None
    workspaces_bucket_arn: Optional[str] = None


@dataclass
class DisasterRecoveryConfig:
    is_dr_instance: bool = None
    replica_region: str = None
    encryption_primary_key_arn: str = None
    s3_bucket_replication: S3BucketReplicationConfig = None


@dataclass
class AlertingConfig:
    sns_topic_arn: Optional[str] = None


@dataclass
class S3Config:
    run_logs_expiration_days: Optional[int] = None
    deliveries_bucket_expiration_days: Optional[int] = None
    large_queue_messages_bucket_expiration_days: Optional[int] = None
    metadata_bucket_expiration_days: Optional[int] = None
    policy_inputs_bucket_expiration_days: Optional[int] = None
    uploads_bucket_expiration_days: Optional[int] = None
    user_uploaded_workspaces_bucket_expiration_days: Optional[int] = None
    workspaces_bucket_expiration_days: Optional[int] = None
    access_logs_bucket_expiration_days: Optional[int] = None


@dataclass
class AppConfig:
    account_name: Optional[str] = None
    aws_region: Optional[str] = None
    database: Optional[DatabaseConfig] = None
    disaster_recovery: Optional[DisasterRecoveryConfig] = None
    disable_services: Optional[bool] = None
    load_balancer: Optional[LoadBalancerConfig] = None
    proxy_config: Optional[ProxyConfig] = None
    spacelift_hostname: Optional[str] = None
    slack_config: Optional[SlackConfig] = None
    sso_config: Optional[SSOConfig] = None
    tls_config: Optional[TLSConfig] = None
    tracing_enabled: Optional[bool] = None
    vpc_config: Optional[VpcConfig] = None
    iot_broker_endpoint: Optional[str] = None
    alerting: Optional[AlertingConfig] = None
    global_resource_tags: Optional[List[TagConfig]] = None
    s3_config: Optional[S3Config] = None
    automatically_report_usage_data: Optional[bool] = None

    def is_primary_region(self) -> bool:
        return not (self.disaster_recovery and self.disaster_recovery.is_dr_instance)

    def uses_custom_database_connection_string(self) -> bool:
        return (
            self.database
            and self.database.connection_string_ssm_arn
            and len(self.database.connection_string_ssm_arn) > 0
        )

    def has_custom_proxy_config(self) -> bool:
        return self.proxy_config and (
            self.proxy_config.http_proxy
            or self.proxy_config.https_proxy
            or self.proxy_config.no_proxy
        )


def load_app_config(config_path: str) -> AppConfig:
    try:
        with open(config_path, "r") as f:
            config_data = json.load(f)

        if "database" in config_data:
            config_data["database"] = DatabaseConfig(**config_data["database"])
        if "load_balancer" in config_data:
            if "tag" in config_data["load_balancer"]:
                config_data["load_balancer"]["tag"] = TagConfig(
                    **config_data["load_balancer"]["tag"]
                )
            config_data["load_balancer"] = LoadBalancerConfig(**config_data["load_balancer"])
        if "proxy_config" in config_data:
            config_data["proxy_config"] = ProxyConfig(**config_data["proxy_config"])
        if "slack_config" in config_data:
            config_data["slack_config"] = SlackConfig(**config_data["slack_config"])
        if "sso_config" in config_data:
            sso_data = config_data["sso_config"]
            if "oidc_args" in sso_data:
                sso_data["oidc_args"] = OidcArgs(**sso_data["oidc_args"])
            if "saml_args" in sso_data:
                sso_data["saml_args"] = SamlArgs(**sso_data["saml_args"])
            config_data["sso_config"] = SSOConfig(**sso_data)
        if "tls_config" in config_data:
            config_data["tls_config"] = TLSConfig(**config_data["tls_config"])
        if "vpc_config" in config_data:
            config_data["vpc_config"] = VpcConfig(**config_data["vpc_config"])
        if "disaster_recovery" in config_data:
            dr_data = config_data["disaster_recovery"]
            if "s3_bucket_replication" in dr_data:
                dr_data["s3_bucket_replication"] = S3BucketReplicationConfig(
                    **dr_data["s3_bucket_replication"]
                )
            config_data["disaster_recovery"] = DisasterRecoveryConfig(**dr_data)

        if "alerting" in config_data:
            config_data["alerting"] = AlertingConfig(**config_data["alerting"])
        if "s3_config" in config_data:
            config_data["s3_config"] = S3Config(**config_data["s3_config"])

        return AppConfig(**config_data)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading configuration file: {e}")
        sys.exit(1)
    except TypeError as e:
        print(f"Error parsing configuration: {e}")
        sys.exit(1)
