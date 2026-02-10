# 🚀 Spacelift Self-Hosted V2 to V3 Migration Tool

This repository contains a Python tool that converts Cloudformation-based Spacelift self-hosted installations (V2) into Terraform-managed deployments (V3), enabling a smooth migration with zero downtime.

## 📋 Overview

This migration tool analyzes your existing Spacelift V2 infrastructure deployed with CloudFormation and generates equivalent Terraform code that can be applied to create new V3 resources while preserving your application's functionality. The process scans all relevant AWS resources, creates proper `import` statements, and sets up a new ECS cluster with a load balancer, allowing you to redirect traffic once the new infrastructure is ready.

The migration workflow follows these steps:
1. Scan existing AWS resources from CloudFormation stacks
2. Generate Terraform import statements and configuration files for each resource type
3. Create helper scripts for special migration cases (internet gateway refactoring)
4. Apply the Terraform configuration to set up the new infrastructure
5. Redirect traffic to the new load balancer
6. Remove old CloudFormation stacks while retaining necessary resources

Key features:
- Scans and imports existing AWS resources (VPC, EC2, ECR, RDS, S3, KMS, IoT, SQS, etc.)
- Generates all necessary Terraform files
- Creates a script to handle a small structural difference between CloudFormation and Terraform (Internet gateway refactoring)
- Creates a script to tear down the old CloudFormation stacks with retaining resources
- Enables zero-downtime migration (flipping the CNAME record to the new load balancer)
- Supports custom VPC configurations (where `.vpc_config.use_custom_vpc` is set to `true`)
- Supports bi-regional disaster recovery setups

## 📊 Compatibility Matrix

### ECS

| Spacelift version | Migration kit version | [AWS Spacelift module](https://github.com/spacelift-io/terraform-aws-spacelift-selfhosted) | [AWS ECS module](https://github.com/spacelift-io/terraform-aws-ecs-spacelift-selfhosted) |
| ----------------- | --------------------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| >= 2.6.0, < 4.0.0 | 1.0.1                 | 1.3.1                                                                                      | 1.1.0                                                                                    |
| >= 2.6.0          | 1.1.0                 | 2.1.1                                                                                      | 2.1.0                                                                                    |
| >= 2.6.0          | 2.0.0                 | 2.1.1                                                                                      | 2.1.0                                                                                    |

### EKS

| Spacelift version | Migration kit version | [AWS EKS module](https://github.com/spacelift-io/terraform-aws-eks-spacelift-selfhosted) |
| ----------------- | --------------------- | ---------------------------------------------------------------------------------------- |
| >= 4.0.0          | 2.0.0                 | 3.4.0                                                                                    |

## 📦 Requirements

- At least Self-hosted v2.6.0 installed
- Python 3.8+
- AWS credentials with appropriate permissions
  - read access for the Python script (`main.py`) that scans the existing resources
  - administrator access for running the `internet_gateway_refactor.py` script
  - administrator access when applying the generated Terraform code
  - administrator access when running the `delete_cf_stacks.py` cleanup script
- A few pip packages (see [requirements.txt](./requirements.txt))
- For development: code formatter and linter (see [requirements-dev.txt](./requirements-dev.txt))

## Migration Guides

- [CloudFormation to ECS](docs/cloudformation_to_ecs.md) - Migrate to Terraform-managed ECS deployment
- [CloudFormation to EKS](docs/cloudformation_to_eks.md) - Migrate to Terraform-managed EKS deployment

## ✨ Customization

The generated Terraform code serves as a starting point that you can customize according to your needs. Feel free to adjust the resource configurations before applying to meet your specific requirements.

## 🧪 Development

If you use VS Code, it'll prompt you to install the recommended extensions in `.vscode/extensions.json`, so that formatting and linting works out of the box. Otherwise you can do it manually, like so:

```bash
# Activate the virtual environment, then
pip install -r requirements-dev.txt

# Code formatting
black --line-length 100 .

# Linting
flake8
```
