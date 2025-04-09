import boto3
from converters.rds_to_terraform import RDSTerraformer


def scan_rds_resources(session: boto3.Session, terraformer: RDSTerraformer) -> None:
    print(" > Scanning RDS resources...")

    rds = session.client("rds")
    list_resp = rds.describe_db_clusters(DBClusterIdentifier="spacelift")

    for cluster in list_resp["DBClusters"]:
        cluster_members = cluster.get("DBClusterMembers", [])
        if len(cluster_members) != 1:
            raise Exception(
                f"Expected exactly one cluster member, but found {len(cluster_members)}"
            )

        instance_resp = rds.describe_db_instances(
            DBInstanceIdentifier=cluster_members[0]["DBInstanceIdentifier"]
        )
        instances = instance_resp.get("DBInstances", [])
        if len(instances) != 1:
            raise Exception(f"Expected exactly one instance, but found {len(instances)}")

        terraformer.rds_to_terraform(cluster, instances[0])
