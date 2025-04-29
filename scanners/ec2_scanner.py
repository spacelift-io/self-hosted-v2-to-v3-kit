from typing import Dict, List
import boto3
from converters.ec2_to_terraform import EC2Terraformer
from scanners.cloudformation_helper import get_resources_from_cf_stack


def scan_ec2_resources(session: boto3.Session, terraformer: EC2Terraformer) -> None:
    print(" > Scanning EC2 resources...")

    ec2 = session.client("ec2")
    cloudformation = session.client("cloudformation")

    if not terraformer.uses_custom_vpc():
        _scan_vpcs(ec2, cloudformation, terraformer)
        _scan_subnets(ec2, cloudformation, terraformer)
        _scan_internet_gateways(cloudformation, terraformer)
        _scan_route_tables(ec2, cloudformation, terraformer)
        _scan_elastic_ips(ec2, cloudformation, terraformer)
        _scan_nat_gateways(ec2, cloudformation, terraformer)
        _scan_security_groups(ec2, cloudformation, terraformer)


def _scan_vpcs(ec2, cloudformation, terraformer: EC2Terraformer) -> None:
    [vpc_id] = get_resources_from_cf_stack(cloudformation, "spacelift-infra-vpc", ["VPC"])
    list_resp = ec2.describe_vpcs(VpcIds=[vpc_id])
    vpc = list_resp["Vpcs"][0]
    terraformer.vpc_to_terraform(vpc["VpcId"], vpc["CidrBlock"], vpc.get("Tags", []))


def _scan_subnets(ec2, cloudformation, terraformer: EC2Terraformer) -> None:
    priv_subnets = get_resources_from_cf_stack(
        cloudformation,
        "spacelift-infra-vpc",
        ["PrivateSubnet1", "PrivateSubnet2", "PrivateSubnet3"],
    )
    pub_subnets = get_resources_from_cf_stack(
        cloudformation,
        "spacelift-infra-vpc-config",
        ["PublicSubnet1", "PublicSubnet2", "PublicSubnet3"],
    )

    list_resp = ec2.describe_subnets(SubnetIds=priv_subnets + pub_subnets)

    for subnet in list_resp["Subnets"]:
        terraformer.subnet_to_terraform(
            subnet["SubnetId"], subnet["CidrBlock"], subnet.get("Tags", [])
        )


def _scan_internet_gateways(cloudformation, terraformer: EC2Terraformer) -> None:
    [igw_id] = get_resources_from_cf_stack(
        cloudformation, "spacelift-infra-vpc-config", ["InternetGateway"]
    )
    terraformer.internet_gateway_to_terraform(igw_id)


def _scan_route_tables(ec2, cloudformation, terraformer: EC2Terraformer) -> None:
    route_table_ids = get_resources_from_cf_stack(
        cloudformation,
        "spacelift-infra-vpc-config",
        [
            "InternetGatewayRouteTable1",
            "InternetGatewayRouteTable2",
            "InternetGatewayRouteTable3",
            "NATGatewayRouteTable1",
            "NATGatewayRouteTable2",
            "NATGatewayRouteTable3",
        ],
    )
    table_resp = ec2.describe_route_tables(RouteTableIds=route_table_ids)

    igw_route_table_1 = _get_route_table_by_name(
        table_resp["RouteTables"], "InternetGatewayRouteTable1"
    )
    igw_route_table_2 = _get_route_table_by_name(
        table_resp["RouteTables"], "InternetGatewayRouteTable2"
    )
    igw_route_table_3 = _get_route_table_by_name(
        table_resp["RouteTables"], "InternetGatewayRouteTable3"
    )
    terraformer.route_table_to_terraform(igw_route_table_1, "Spacelift InternetGatewayRouteTable1")
    terraformer.route_table_to_terraform(igw_route_table_2, "Spacelift InternetGatewayRouteTable2")
    terraformer.route_table_to_terraform(igw_route_table_3, "Spacelift InternetGatewayRouteTable3")

    nat_gateway_route_table_1 = _get_route_table_by_name(
        table_resp["RouteTables"], "NATGatewayRouteTable1"
    )
    nat_gateway_route_table_2 = _get_route_table_by_name(
        table_resp["RouteTables"], "NATGatewayRouteTable2"
    )
    nat_gateway_route_table_3 = _get_route_table_by_name(
        table_resp["RouteTables"], "NATGatewayRouteTable3"
    )
    terraformer.route_table_to_terraform(
        nat_gateway_route_table_1, "Spacelift NATGatewayRouteTable1"
    )
    terraformer.route_table_to_terraform(
        nat_gateway_route_table_2, "Spacelift NATGatewayRouteTable2"
    )
    terraformer.route_table_to_terraform(
        nat_gateway_route_table_3, "Spacelift NATGatewayRouteTable3"
    )


def _get_route_table_by_name(route_tables: List[Dict], name: str) -> Dict:
    for route_table in route_tables:
        tags = route_table.get("Tags", [])

        if any(
            tag["Key"] == "aws:cloudformation:logical-id" and tag["Value"] == name for tag in tags
        ):
            return route_table

    raise ValueError(f"Route table with name {name} not found.")


def _scan_elastic_ips(ec2, cloudformation, terraformer: EC2Terraformer) -> None:
    ips = get_resources_from_cf_stack(
        cloudformation,
        "spacelift-infra-vpc-config",
        ["NATGatewayEIP1", "NATGatewayEIP2", "NATGatewayEIP3"],
    )
    elastic_ip_resp = ec2.describe_addresses(PublicIps=ips)

    for elastic_ip in elastic_ip_resp["Addresses"]:
        terraformer.elastic_ip_to_terraform(elastic_ip["AllocationId"], elastic_ip.get("Tags", []))


def _scan_nat_gateways(ec2, cloudformation, terraformer: EC2Terraformer) -> None:
    [gw1, gw2, gw3] = get_resources_from_cf_stack(
        cloudformation, "spacelift-infra-vpc-config", ["NATGateway1", "NATGateway2", "NATGateway3"]
    )
    terraformer.nat_gateway_to_terraform("NATGateway1", gw1)
    terraformer.nat_gateway_to_terraform("NATGateway2", gw2)
    terraformer.nat_gateway_to_terraform("NATGateway3", gw3)


def _scan_security_groups(ec2, cloudformation, terraformer: EC2Terraformer) -> None:
    ids = get_resources_from_cf_stack(
        cloudformation,
        "spacelift-infra-vpc",
        [
            "ServerSecurityGroup",
            "DrainSecurityGroup",
            "DatabaseSecurityGroup",
            "SchedulerSecurityGroup",
        ],
    )
    security_group_resp = ec2.describe_security_groups(GroupIds=ids)

    for security_group in security_group_resp["SecurityGroups"]:
        rules = ec2.describe_security_group_rules(
            Filters=[{"Name": "group-id", "Values": [security_group["GroupId"]]}]
        )
        terraformer.security_group_to_terraform(
            security_group["GroupId"],
            rules["SecurityGroupRules"],
            security_group.get("Tags", []),
        )
