# 🚀 Spacelift Self-Hosted V2 to V3 Migration Tool

This repository contains a Python tool that converts Cloudformation-based Spacelift self-hosted installations (V2) into Terraform-managed deployments (V3), enabling a smooth migration with zero downtime.

## 📋 Overview

This migration tool analyzes your existing Spacelift V2 infrastructure deployed with CloudFormation and generates equivalent Terraform code that can be applied to create new V3 resources while preserving your application's functionality. The process scans all relevant AWS resources, creates proper `import` statements, and sets up a new ECS cluster with a load balancer, allowing you to redirect traffic once the new infrastructure is ready.

Key features:
- Scans and imports existing AWS resources (VPC, EC2, ECR, RDS, S3, KMS, IoT, SQS, etc.)
- Generates all necessary Terraform configurations
- Creates a first-step script to handle infrastructure differences between V2 and V3
- Provides a modular approach to deploy the new V3 infrastructure
- Enables zero-downtime migration

## 📦 Requirements

- Python 3.8+
- AWS credentials with appropriate permissions
  - read access for the Python script that scans the existing resources
  - administrator access when applying the generated Terraform code
- boto3 (see `requirements.txt`)
- For development: black v23.12.1 (see `requirements-dev.txt`)

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/spacelift-io/self-hosted-v2-to-v3-kit.git
cd self-hosted-v2-to-v3-kit

# Create a Python 3 virtual environment
python -m venv env

# Activate the virtual environment
# On Unix/Linux:
source env/bin/activate
# On Windows:
# env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

## 🛠️ Usage

### Step 1: Generate Terraform project

#### Prerequisites

Run the main script with your AWS region:

```bash
python main.py --region <aws-region>
```

Additional arguments:
- `--profile`: AWS profile to use (optional)
- `--output`: Output directory path for Terraform files (default: `dist`)

The script will:
1. Scan for all relevant AWS resources in your current Spacelift deployment
2. Get the unique suffix from SSM Parameter Store (from `/spacelift/random-suffix`)
3. Get the certificate ARN from the existing load balancer
4. Generate Terraform files
5. Create a `first_step.sh` script for the migration

### Step 2: Apply the Generated Terraform Code

Navigate to the output directory and follow these steps:

1. Prepare the environment:
   ```bash
   chmod +x ./first_step.sh
   ./first_step.sh
   ```
   This script adjusts a small infrastructure difference between V2 and V3: consolidating multiple internet gateways into one shared gateway for all public subnets. Since the commands in the scripts are executed in an instant, the existing application should not be affected - at maximum having a one-second blip for outbound traffic.

   > The reason this step is a separate script instead of being part of the Terraform code is that Terraform has troubles properly ordering the removal and additions of internet gateway subnet associations, and AWS is very picky about the order of these operations.

2. Configure the variables in `main.tf`:
   - Set `local.license_token` with your Spacelift license token
   - Set `local.spacelift_version` to the appropriate Docker tag uploaded to the ECR repositories

3. Initialize Terraform:
   ```bash
   terraform init
   ```

4. Create and review the execution plan:
   ```bash
   terraform plan -out=plan
   ```
   
   For easier review of the extensive plan:
   ```bash
   terraform show plan > plan.txt
   # or in JSON format
   terraform show -json plan > plan.json
   ```

   The plan should include:
   - 100+ resource imports
   - ECR lifecycle policy replacements
   - A global RDS cluster creation (for high availability)
   - Various in-place changes (mostly tag-related)

   When reviewing, look for important changes:
   - `replaced` resources
   - `updated in-place` changes
   - `created` resources
   - `destroy` operations

5. Apply the changes:
   ```bash
   terraform apply plan
   ```

6. Update the Terraform configuration:
   - Uncomment the `spacelift_services` module in `main.tf`
   - Comment out the entire contents of `imports.tf` (they're no longer needed after the imports are done)

7. Re-initialize and plan the new resources:
   ```bash
   terraform init
   terraform plan -out=plan
   ```
   
   This plan will create:
   - A new ECS cluster with the same set of services as the old cluster
   - A new load balancer
   - You should only `creation` operations in the plan, unless you've modified the code

8. Apply the second plan:
   ```bash
   terraform apply plan
   ```

9. Redirect traffic:
   - Update your `CNAME` record to point to the new load balancer DNS name (available as an output)
   - To make sure the traffic is properly routed, you can scale down the old ECS cluster's `server` service to 0 tasks

10. Clean up obsolete resources:
    - TODO(spacelift): add delete commands for the Cloudformation stacks with proper retention parameters
    - If you want to retain more resources than the Terraform code does, feel free to `import` those

11. (Optional) Reorganize Terraform code as needed:
    - The terraform `move` block can be useful for restructuring

## ✨ Customization

The generated Terraform code serves as a starting point that you can customize according to your needs. Feel free to adjust the resource configurations before applying to meet your specific requirements.

## 🧪 Development

For code formatting:
```bash
pip install -r requirements-dev.txt
black --line-length 100 .
```
