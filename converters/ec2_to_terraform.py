from typing import List, Dict

from converters.terraformer import Terraformer

from .migration_context import MigrationContext


class EC2Terraformer(Terraformer):
    def __init__(self, file_path: str, migration_context: MigrationContext):
        super().__init__(file_path, migration_context)

        self.vpc_resource_name = "module.spacelift.module.network[0].aws_vpc.spacelift_vpc"
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

        # Internet Gateway
        self.internet_gateway_resource_name = (
            "module.spacelift.module.network[0].aws_internet_gateway.main"
        )

        # Route Tables
        self.internet_gateway_route_table_resource_name = (
            "module.spacelift.module.network[0].aws_route_table.internet_gateway"
        )
        self.internet_gateway_route_table_assoc1_resource_name = (
            "module.spacelift.module.network[0].aws_route_table_association.internet_gateway[0]"
        )
        self.internet_gateway_route_table_assoc2_resource_name = (
            "module.spacelift.module.network[0].aws_route_table_association.internet_gateway[1]"
        )
        self.internet_gateway_route_table_assoc3_resource_name = (
            "module.spacelift.module.network[0].aws_route_table_association.internet_gateway[2]"
        )

        self.nat_gateway_route_table_resource_name_one = (
            "module.spacelift.module.network[0].aws_route_table.nat_gateway[0]"
        )
        self.nat_gateway_route_table_resource_name_two = (
            "module.spacelift.module.network[0].aws_route_table.nat_gateway[1]"
        )
        self.nat_gateway_route_table_resource_name_three = (
            "module.spacelift.module.network[0].aws_route_table.nat_gateway[2]"
        )

        self.nat_gateway_route_table_assoc_resource_name_one = (
            "module.spacelift.module.network[0].aws_route_table_association.nat_gateway[0]"
        )
        self.nat_gateway_route_table_assoc_resource_name_two = (
            "module.spacelift.module.network[0].aws_route_table_association.nat_gateway[1]"
        )
        self.nat_gateway_route_table_assoc_resource_name_three = (
            "module.spacelift.module.network[0].aws_route_table_association.nat_gateway[2]"
        )

        # EIPs
        self.eip_resource_name_one = "module.spacelift.module.network[0].aws_eip.eips[0]"
        self.eip_resource_name_two = "module.spacelift.module.network[0].aws_eip.eips[1]"
        self.eip_resource_name_three = "module.spacelift.module.network[0].aws_eip.eips[2]"

        # NAT Gateways
        self.nat_gateway_resource_name_one = (
            "module.spacelift.module.network[0].aws_nat_gateway.nat_gateways[0]"
        )
        self.nat_gateway_resource_name_two = (
            "module.spacelift.module.network[0].aws_nat_gateway.nat_gateways[1]"
        )
        self.nat_gateway_resource_name_three = (
            "module.spacelift.module.network[0].aws_nat_gateway.nat_gateways[2]"
        )

        # Security Groups
        self.scheduler_sg_resource_name = (
            "module.spacelift.module.network[0].aws_security_group.scheduler_sg"
        )
        self.scheduler_sg_egress_rule_resource_name = "module.spacelift.module.network[0].aws_vpc_security_group_egress_rule.scheduler_sg_egress_rule"

        self.drain_sg_resource_name = (
            "module.spacelift.module.network[0].aws_security_group.drain_sg"
        )
        self.drain_sg_egress_rule_resource_name = "module.spacelift.module.network[0].aws_vpc_security_group_egress_rule.drain_sg_egress_rule"

        self.server_sg_resource_name = (
            "module.spacelift.module.network[0].aws_security_group.server_sg"
        )
        self.server_sg_egress_rule_resource_name = "module.spacelift.module.network[0].aws_vpc_security_group_egress_rule.server_sg_egress_rule"

        self.database_sg_resource_name = (
            "module.spacelift.module.network[0].aws_security_group.database_sg[0]"
        )
        self.database_drain_ingress_rule_resource_name = "module.spacelift.module.network[0].aws_vpc_security_group_ingress_rule.database_drain_ingress_rule[0]"
        self.database_server_ingress_rule_resource_name = "module.spacelift.module.network[0].aws_vpc_security_group_ingress_rule.database_server_ingress_rule[0]"
        self.database_scheduler_ingress_rule_resource_name = "module.spacelift.module.network[0].aws_vpc_security_group_ingress_rule.database_scheduler_ingress_rule[0]"

    def vpc_to_terraform(self, vpc_id: str, cidr_block: str, tags: List[Dict]):
        for tag in tags:
            if tag["Key"] == "aws:cloudformation:logical-id" and tag["Value"] == "VPC":
                self.migration_context.vpc_cidr_block = cidr_block
                self.process(self.vpc_resource_name, vpc_id)

    def subnet_to_terraform(self, subnet_id: str, cidr_block: str, tags: List[Dict]):
        for tag in tags:
            if tag["Key"] == "Name" and tag["Value"] == "Spacelift PrivateSubnet1":
                self.migration_context.private_subnet_cidr_blocks[0] = cidr_block
                self.process(self.private_subnet_resource_name_one, subnet_id)
            elif tag["Key"] == "Name" and tag["Value"] == "Spacelift PrivateSubnet2":
                self.migration_context.private_subnet_cidr_blocks[1] = cidr_block
                self.process(self.private_subnet_resource_name_two, subnet_id)
            elif tag["Key"] == "Name" and tag["Value"] == "Spacelift PrivateSubnet3":
                self.migration_context.private_subnet_cidr_blocks[2] = cidr_block
                self.process(self.private_subnet_resource_name_three, subnet_id)
            elif tag["Key"] == "Name" and tag["Value"] == "Spacelift PublicSubnet1":
                self.migration_context.public_subnet_id_1 = subnet_id
                self.migration_context.public_subnet_cidr_blocks[0] = cidr_block
                self.process(self.public_subnet_resource_name_one, subnet_id)
            elif tag["Key"] == "Name" and tag["Value"] == "Spacelift PublicSubnet2":
                self.migration_context.public_subnet_id_2 = subnet_id
                self.migration_context.public_subnet_cidr_blocks[1] = cidr_block
                self.process(self.public_subnet_resource_name_two, subnet_id)
            elif tag["Key"] == "Name" and tag["Value"] == "Spacelift PublicSubnet3":
                self.migration_context.public_subnet_id_3 = subnet_id
                self.migration_context.public_subnet_cidr_blocks[2] = cidr_block
                self.process(self.public_subnet_resource_name_three, subnet_id)

    def internet_gateway_to_terraform(self, igw_id: str):
        self.process(
            self.internet_gateway_resource_name,
            igw_id,
        )

    def route_table_to_terraform(self, route_table: Dict, route_table_name: str):
        if route_table_name == "Spacelift InternetGatewayRouteTable1":
            route_table_id = route_table["RouteTableId"]
            self.migration_context.gateway1_route_table_id = route_table_id
            associations = route_table.get("Associations", [])

            if len(associations) != 1 and len(associations) != 3:
                raise Exception(
                    "InternetGatewayRouteTable1 should have only one association, or three if the first_step.sh script was run"
                )
            self.process(
                self.internet_gateway_route_table_resource_name,
                route_table_id,
            )
            self.process(
                self.internet_gateway_route_table_assoc1_resource_name,
                f"{self.migration_context.public_subnet_id_1}/{route_table_id}",
            )
        elif route_table_name == "Spacelift InternetGatewayRouteTable2":
            route_table_id = route_table["RouteTableId"]
            self.migration_context.gateway2_route_table_id = route_table_id
            associations = route_table.get("Associations", [])

            # The script was already ran, igw2 is now empty
            if not associations:
                self.process(
                    self.internet_gateway_route_table_assoc2_resource_name,
                    f"{self.migration_context.public_subnet_id_2}/{self.migration_context.gateway1_route_table_id}",
                )
                return

            if len(associations) != 1:
                raise Exception("InternetGatewayRouteTable2 should have only one association")

            self.process(
                self.internet_gateway_route_table_assoc2_resource_name,
                f"{self.migration_context.public_subnet_id_2}/{self.migration_context.gateway1_route_table_id}",
            )
            self.migration_context.gateway2_association_id = associations[0][
                "RouteTableAssociationId"
            ]
        elif route_table_name == "Spacelift InternetGatewayRouteTable3":
            route_table_id = route_table["RouteTableId"]
            associations = route_table.get("Associations", [])

            # The script was already ran, igw3 is now empty
            if not associations:
                self.process(
                    self.internet_gateway_route_table_assoc3_resource_name,
                    f"{self.migration_context.public_subnet_id_3}/{self.migration_context.gateway1_route_table_id}",
                )
                return

            if len(associations) != 1:
                raise Exception("InternetGatewayRouteTable3 should have only one association")

            self.process(
                self.internet_gateway_route_table_assoc3_resource_name,
                f"{self.migration_context.public_subnet_id_3}/{self.migration_context.gateway1_route_table_id}",
            )
            self.migration_context.gateway3_association_id = associations[0][
                "RouteTableAssociationId"
            ]
        elif route_table_name == "Spacelift NATGatewayRouteTable1":
            self.process(
                self.nat_gateway_route_table_resource_name_one,
                route_table["RouteTableId"],
            )
            associations = route_table.get("Associations", [])
            if len(associations) != 1:
                raise Exception("NATGatewayRouteTable1 should have only one association")
            self.process(
                self.nat_gateway_route_table_assoc_resource_name_one,
                f"{associations[0]['SubnetId']}/{route_table['RouteTableId']}",
            )
        elif route_table_name == "Spacelift NATGatewayRouteTable2":
            self.process(
                self.nat_gateway_route_table_resource_name_two,
                route_table["RouteTableId"],
            )
            associations = route_table.get("Associations", [])
            if len(associations) != 1:
                raise Exception("NATGatewayRouteTable2 should have only one association")
            self.process(
                self.nat_gateway_route_table_assoc_resource_name_two,
                f"{associations[0]['SubnetId']}/{route_table['RouteTableId']}",
            )
        elif route_table_name == "Spacelift NATGatewayRouteTable3":
            self.process(
                self.nat_gateway_route_table_resource_name_three,
                route_table["RouteTableId"],
            )
            associations = route_table.get("Associations", [])
            if len(associations) != 1:
                raise Exception("NATGatewayRouteTable3 should have only one association")
            self.process(
                self.nat_gateway_route_table_assoc_resource_name_three,
                f"{associations[0]['SubnetId']}/{route_table['RouteTableId']}",
            )

    def elastic_ip_to_terraform(self, allocation_id: str, tags: List[Dict]):
        for tag in tags:
            if tag["Key"] == "aws:cloudformation:logical-id" and tag["Value"] == "NATGatewayEIP1":
                self.process(self.eip_resource_name_one, allocation_id)
            elif tag["Key"] == "aws:cloudformation:logical-id" and tag["Value"] == "NATGatewayEIP2":
                self.process(self.eip_resource_name_two, allocation_id)
            elif tag["Key"] == "aws:cloudformation:logical-id" and tag["Value"] == "NATGatewayEIP3":
                self.process(self.eip_resource_name_three, allocation_id)

    def nat_gateway_to_terraform(self, gateway_logical_id: str, gateway_id: str):
        if gateway_logical_id == "NATGateway1":
            self.process(self.nat_gateway_resource_name_one, gateway_id)
        elif gateway_logical_id == "NATGateway2":
            self.process(self.nat_gateway_resource_name_two, gateway_id)
        elif gateway_logical_id == "NATGateway3":
            self.process(self.nat_gateway_resource_name_three, gateway_id)

    def security_group_to_terraform(
        self, security_group_id: str, rules: List[Dict], tags: List[Dict]
    ):
        for tag in tags:
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "SchedulerSecurityGroup"
            ):
                self.process(
                    self.scheduler_sg_resource_name,
                    security_group_id,
                )
                for rule in rules:
                    if rule["IsEgress"] == True:
                        self.process(
                            self.scheduler_sg_egress_rule_resource_name,
                            rule["SecurityGroupRuleId"],
                        )
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "DrainSecurityGroup"
            ):
                self.process(
                    self.drain_sg_resource_name,
                    security_group_id,
                )
                for rule in rules:
                    if rule["IsEgress"] == True:
                        self.process(
                            self.drain_sg_egress_rule_resource_name,
                            rule["SecurityGroupRuleId"],
                        )
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "ServerSecurityGroup"
            ):
                self.process(
                    self.server_sg_resource_name,
                    security_group_id,
                )
                for rule in rules:
                    if rule["IsEgress"] == True:
                        self.process(
                            self.server_sg_egress_rule_resource_name,
                            rule["SecurityGroupRuleId"],
                        )
            if (
                tag["Key"] == "aws:cloudformation:logical-id"
                and tag["Value"] == "DatabaseSecurityGroup"
            ):
                self.process(
                    self.database_sg_resource_name,
                    security_group_id,
                )
                for rule in rules:
                    if rule["IsEgress"] == False and "from the drain" in rule["Description"]:
                        self.process(
                            self.database_drain_ingress_rule_resource_name,
                            rule["SecurityGroupRuleId"],
                        )
                    if rule["IsEgress"] == False and "from the server" in rule["Description"]:
                        self.process(
                            self.database_server_ingress_rule_resource_name,
                            rule["SecurityGroupRuleId"],
                        )
                    if rule["IsEgress"] == False and "from the scheduler" in rule["Description"]:
                        self.process(
                            self.database_scheduler_ingress_rule_resource_name,
                            rule["SecurityGroupRuleId"],
                        )
