from typing import List


def get_resources_from_cf_stack(cloudformation, stack_name: str, logical_ids: List[str]) -> tuple:
    stack_resources = cloudformation.describe_stack_resources(StackName=stack_name)

    # This is a trick to make sure the returned ids are in the same order as the logical_ids:

    resource_map = {
        res["LogicalResourceId"]: res["PhysicalResourceId"]
        for res in stack_resources["StackResources"]
    }

    resource_ids = []

    for logical_id in logical_ids:
        if logical_id not in resource_map:
            raise ValueError(f"Missing required resource '{logical_id}' in CloudFormation stack")
        resource_ids.append(resource_map[logical_id])

    return resource_ids
