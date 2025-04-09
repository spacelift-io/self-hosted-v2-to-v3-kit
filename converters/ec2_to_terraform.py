from typing import List, Dict

from converters.terraformer import Terraformer

from .migration_context import MigrationContext


class EC2Terraformer(Terraformer):
    def __init__(self, file_path: str, migration_context: MigrationContext):
        super().__init__(file_path, migration_context)

        self.vpc_resource_name = (
            "module.spacelift.module.network[0].aws_vpc.spacelift_vpc"
        )
        self.private_subnet_resource_name_one = (
            "module.spacelift.module.network[0].aws_subnet.private_subnets[0]"
        )
        self.private_subnet_resource_name_two = (
            "module.spacelift.module.network[0].aws_subnet.private_subnets[1]"
        )
        self.private_subnet_resource_name_three = (
            "module.spacelift.module.network[0].aws_subnet.private_subnets[2]"
        )
        self.public_subnet_resource_name_one = (
            "module.spacelift.module.network[0].aws_subnet.public_subnets[0]"
        )
        self.public_subnet_resource_name_two = (
            "module.spacelift.module.network[0].aws_subnet.public_subnets[1]"
        )
        self.public_subnet_resource_name_three = (
            "module.spacelift.module.network[0].aws_subnet.public_subnets[2]"
        )

    def vpc_to_terraform(self, vpc_id: str, cidr_block: str, tags: List[Dict]):
        for tag in tags:
            if tag["Key"] == "aws:cloudformation:logical-id" and tag["Value"] == "VPC":
                self.migration_context.vpc_cidr_block = cidr_block
                self.process(self.vpc_resource_name, vpc_id)

    def subnet_to_terraform(self, subnet_id: str, cidr_block: str, tags: List[Dict]):
        for tag in tags:
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "PrivateSubnet1"
            ):
                self.migration_context.private_subnet_cidr_blocks[0] = cidr_block
                self.process(self.private_subnet_resource_name_one, subnet_id)
            elif (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "PrivateSubnet2"
            ):
                self.migration_context.private_subnet_cidr_blocks[1] = cidr_block
                self.process(self.private_subnet_resource_name_two, subnet_id)
            elif (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "PrivateSubnet3"
            ):
                self.migration_context.private_subnet_cidr_blocks[2] = cidr_block
                self.process(self.private_subnet_resource_name_three, subnet_id)
            elif (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "PublicSubnet1"
            ):
                self.migration_context.public_subnet_cidr_blocks[0] = cidr_block
                self.process(self.public_subnet_resource_name_one, subnet_id)
            elif (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "PublicSubnet2"
            ):
                self.migration_context.public_subnet_cidr_blocks[1] = cidr_block
                self.process(self.public_subnet_resource_name_two, subnet_id)
            elif (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "PublicSubnet3"
            ):
                self.migration_context.public_subnet_cidr_blocks[2] = cidr_block
                self.process(self.public_subnet_resource_name_three, subnet_id)

    def internet_gateway_to_terraform(self, igw_id: str, tags: List[Dict]):
        for tag in tags:
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "InternetGateway"
            ):
                self.process(
                    "module.spacelift.module.network[0].aws_internet_gateway.main",
                    igw_id,
                )

    def route_table_to_terraform(self, route_table: Dict, tags: List[Dict]):
        for tag in tags:
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "InternetGatewayRouteTable1"
            ):
                # In v2 we have:
                # - Public Subnet 1 -> InternetGatewayRouteTable1 -> Interner GW
                # - Public Subnet 2 -> InternetGatewayRouteTable2 -> Interner GW
                # - Public Subnet 3 -> InternetGatewayRouteTable3 -> Interner GW
                # In v3 we have:
                # - Public Subnet 1 -> InternetGatewayRouteTable -> InternetGateway
                # - Public Subnet 2 -> InternetGatewayRouteTable -> InternetGateway
                # - Public Subnet 3 -> InternetGatewayRouteTable -> InternetGateway
                # So instead of having 3 route tables, we have only one
                # Let's import the very first one, and let the other 2 be created
                # The dangling InternetGatewayRouteTable2 and InternetGatewayRouteTable3 can be removed
                route_table_id = route_table["RouteTableId"]
                associations = route_table.get("Associations", [])
                if len(associations) != 1:
                    raise Exception(
                        "InternetGatewayRouteTable1 should have only one association"
                    )
                association = associations[0]["SubnetId"]
                self.process(
                    "module.spacelift.module.network[0].aws_route_table.internet_gateway",
                    route_table_id,
                )
                self.process(
                    "module.spacelift.module.network[0].aws_route_table_association.internet_gateway[0]",
                    f"{association}/{route_table_id}",
                )

            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "NATGatewayRouteTable1"
            ):
                self.process(
                    "module.spacelift.module.network[0].aws_route_table.nat_gateway[0]",
                    route_table["RouteTableId"],
                )
                associations = route_table.get("Associations", [])
                if len(associations) != 1:
                    raise Exception(
                        "NATGatewayRouteTable1 should have only one association"
                    )
                self.process(
                    "module.spacelift.module.network[0].aws_route_table_association.nat_gateway[0]",
                    f"{associations[0]['SubnetId']}/{route_table['RouteTableId']}",
                )
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "NATGatewayRouteTable2"
            ):
                self.process(
                    "module.spacelift.module.network[0].aws_route_table.nat_gateway[1]",
                    route_table["RouteTableId"],
                )
                associations = route_table.get("Associations", [])
                if len(associations) != 1:
                    raise Exception(
                        "NATGatewayRouteTable2 should have only one association"
                    )
                self.process(
                    "module.spacelift.module.network[0].aws_route_table_association.nat_gateway[1]",
                    f"{associations[0]['SubnetId']}/{route_table['RouteTableId']}",
                )
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "NATGatewayRouteTable3"
            ):
                self.process(
                    "module.spacelift.module.network[0].aws_route_table.nat_gateway[2]",
                    route_table["RouteTableId"],
                )
                associations = route_table.get("Associations", [])
                if len(associations) != 1:
                    raise Exception(
                        "NATGatewayRouteTable3 should have only one association"
                    )
                self.process(
                    "module.spacelift.module.network[0].aws_route_table_association.nat_gateway[2]",
                    f"{associations[0]['SubnetId']}/{route_table['RouteTableId']}",
                )

    def elastic_ip_to_terraform(self, allocation_id: str, tags: List[Dict]):
        for tag in tags:
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "NATGatewayEIP1"
            ):
                self.process(
                    "module.spacelift.module.network[0].aws_eip.eips[0]", allocation_id
                )
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "NATGatewayEIP2"
            ):
                self.process(
                    "module.spacelift.module.network[0].aws_eip.eips[1]", allocation_id
                )
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "NATGatewayEIP3"
            ):
                self.process(
                    "module.spacelift.module.network[0].aws_eip.eips[2]", allocation_id
                )

    def nat_gateway_to_terraform(self, nat_gateway: Dict, tags: List[Dict]):
        for tag in tags:
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "NATGateway1"
            ):
                self.process(
                    "module.spacelift.module.network[0].aws_nat_gateway.nat_gateways[0]",
                    nat_gateway["NatGatewayId"],
                )
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "NATGateway2"
            ):
                self.process(
                    "module.spacelift.module.network[0].aws_nat_gateway.nat_gateways[1]",
                    nat_gateway["NatGatewayId"],
                )
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "NATGateway3"
            ):
                self.process(
                    "module.spacelift.module.network[0].aws_nat_gateway.nat_gateways[2]",
                    nat_gateway["NatGatewayId"],
                )

    def security_group_to_terraform(
        self, security_group_id: str, rules: List[Dict], tags: List[Dict]
    ):
        for tag in tags:
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "SchedulerSecurityGroup"
            ):
                self.process(
                    "module.spacelift.module.network[0].aws_security_group.scheduler_sg",
                    security_group_id,
                )
                for rule in rules:
                    if rule["IsEgress"] == True:
                        self.process(
                            "module.spacelift.module.network[0].aws_vpc_security_group_egress_rule.scheduler_sg_egress_rule",
                            rule["SecurityGroupRuleId"],
                        )
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "DrainSecurityGroup"
            ):
                self.process(
                    "module.spacelift.module.network[0].aws_security_group.drain_sg",
                    security_group_id,
                )
                for rule in rules:
                    if rule["IsEgress"] == True:
                        self.process(
                            "module.spacelift.module.network[0].aws_vpc_security_group_egress_rule.drain_sg_egress_rule",
                            rule["SecurityGroupRuleId"],
                        )
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "ServerSecurityGroup"
            ):
                self.process(
                    "module.spacelift.module.network[0].aws_security_group.server_sg",
                    security_group_id,
                )
                for rule in rules:
                    if rule["IsEgress"] == True:
                        self.process(
                            "module.spacelift.module.network[0].aws_vpc_security_group_egress_rule.server_sg_egress_rule",
                            rule["SecurityGroupRuleId"],
                        )
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "DatabaseSecurityGroup"
            ):
                self.process(
                    "module.spacelift.module.network[0].aws_security_group.database_sg[0]",
                    security_group_id,
                )
                for rule in rules:
                    if (
                        rule["IsEgress"] == False
                        and "from the drain" in rule["Description"]
                    ):
                        self.process(
                            "module.spacelift.module.network[0].aws_vpc_security_group_ingress_rule.database_drain_ingress_rule[0]",
                            rule["SecurityGroupRuleId"],
                        )
                    if (
                        rule["IsEgress"] == False
                        and "from the server" in rule["Description"]
                    ):
                        self.process(
                            "module.spacelift.module.network[0].aws_vpc_security_group_ingress_rule.database_server_ingress_rule[0]",
                            rule["SecurityGroupRuleId"],
                        )
                    if (
                        rule["IsEgress"] == False
                        and "from the scheduler" in rule["Description"]
                    ):
                        self.process(
                            "module.spacelift.module.network[0].aws_vpc_security_group_ingress_rule.database_scheduler_ingress_rule[0]",
                            rule["SecurityGroupRuleId"],
                        )
