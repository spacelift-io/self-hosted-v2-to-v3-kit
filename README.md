# 🚀 Spacelift Self-Hosted V2 to V3 Migration Tool

This repository contains a Python tool that converts Cloudformation-based Spacelift self-hosted installations (V2) into Terraform-managed deployments (V3), enabling a smooth migration with zero downtime.

## 📋 Overview

This migration tool analyzes your existing Spacelift V2 infrastructure deployed with CloudFormation and generates equivalent Terraform code that can be applied to create new V3 resources while preserving your application's functionality. The process scans all relevant AWS resources, creates proper `import` statements, and sets up a new ECS cluster with a load balancer, allowing you to redirect traffic once the new infrastructure is ready.

Key features:
- Scans and imports existing AWS resources (VPC, EC2, ECR, RDS, S3, KMS, IoT, SQS, etc.)
- Generates all necessary Terraform files
- Creates a script to handle a small infrastructural difference between V2 and V3 (NAT gateway refactoring)
- Creates a script to tear down the old CloudFormation stacks with retaining resources
- Enables zero-downtime migration (flipping the CNAME record to the new load balancer)

## 📦 Requirements

- At least Self-hosted v2.6.0 installed
- Python 3.8+
- AWS credentials with appropriate permissions
  - read access for the Python script (`main.py`) that scans the existing resources
  - administrator access for running the `nat_gateway_refactor.py` script
  - administrator access when applying the generated Terraform code
  - administrator access when running the `delete_cf_stacks.py` cleanup script
- A few pip packages (see [requirements.txt](./requirements.txt))
- For development: code formatter and linter (see [requirements-dev.txt](./requirements-dev.txt))

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

# For development (code formatting and linting)
pip install -r requirements-dev.txt
```

## 🛠️ Usage

### Step 1: Generate Terraform project

#### Prerequisites

> Make sure the virtualenv is activated when running the Python scripts as they depend on `boto3`.

Run the main script with your AWS region:

```bash
python main.py --region <aws-region>
```

Additional arguments:
- `--profile`: AWS profile to use (optional)
- `--output`: Output directory path for the Terraform project (default: `dist`)

The script will:
1. Scan for all relevant AWS resources in your current Spacelift deployment
2. Get the unique suffix from SSM Parameter Store (from `/spacelift/random-suffix`)
3. Get the certificate ARN from the existing load balancer
4. Generate Terraform files
5. Create 2 scripts: NAT gateway refactoring, and the CloudFormation deletion script

### Step 2: Apply the Generated Terraform Code

Navigate to the output directory and follow these steps:

1. Prepare the environment:
   ```bash
   python <output-folder>/nat_gateway_refactor.py [--profile AWS_PROFILE (optional)]
   ```
   This script adjusts a small infrastructural difference between V2 and V3: consolidating multiple internet gateways into one shared gateway for all public subnets. Since the commands in the scripts are executed in an instant, the existing application should not be affected - at maximum having a one-second blip for outbound traffic.

   > The reason this step is a separate script instead of being part of the Terraform code is that Terraform has troubles properly ordering the removal and additions of internet gateway subnet associations, and AWS is very picky about the order of these operations.

2. Configure the variables in `main.tf`:
   - Set `local.license_token` with your Spacelift license token
   - Set `local.spacelift_version` to the appropriate Docker tag uploaded to the ECR repositories
  
3. (Optional) Backend and resource tagging:
   - You could optionally set up [a remote backend](https://developer.hashicorp.com/terraform/language/backend) for Terraform state management in `main.tf`. The generated code uses a local backend by default, but you can change it to use S3 or any other supported backend.
   - You could set up tags for all resources adding a `default_tags` section to the `provider` block in `main.tf` file. See an example [here](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#default_tags-configuration-block). Note that this'll generate in-place changes to resources, but those should be safe to apply.

4. Initialize Terraform:
   ```bash
   terraform init
   ```

5. Create and review the execution plan:
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
   
   Pay extra attention `replaced` and `destroy` operations, as they may indicate potential downtime or data loss. **Remember that you can always adjust the generated code, as it serves as a starting point**.

6. Apply the changes:
   ```bash
   terraform apply plan
   ```

7. Update the Terraform configuration:
   - Uncomment the `spacelift_services` module in `main.tf`
   - Comment out the entire contents of `imports.tf` file (they're no longer needed after the imports are done)

8. Re-initialize and plan the new resources:
   ```bash
   terraform init
   terraform plan -out=plan
   ```
   
   This plan will create:
   - A new ECS cluster with the same set of services as the old cluster
   - A new load balancer
   - You should only see `creation` operations in the plan, unless you've manually modified the code
  
   Troubleshooting:
   - If the `aws_ecs_service`s don't stabilize in ~2 minutes, it's probably in a crash loop. In that case, open the ECS cluster in the AWS console, open the failing service, and look at the **Logs** tab. You could also look at stopped tasks and open them, they typically include the reason for the failure.

9.  Apply the second plan:
   ```bash
   terraform apply plan
   ```

10. Redirect traffic:
   - Update your `CNAME` record to point to the new load balancer DNS name (available as an output)
   - To make sure the traffic is properly routed, you can scale down the old ECS cluster's `server` service to 0 tasks

   In case you're experiencing issues, you can just revert the DNS change and scale up the old ECS cluster's `server` service.

11.  Clean up obsolete resources:

> ‼️ Before executing this step, make sure that the traffic is properly routed to the new load balancer and everything is working as expected. Ideally, scale down the old cluster's `server`/`drain`/`scheduler` services to 0 tasks, and leave the environment for a few days to ensure everything is functioning correctly.

   - Use the CloudFormation stack deletion script to get rid of the old Cloudformation stacks while retaining the resources you want to keep:
      ```bash
      python <output-folder>/delete_cf_stacks.py --region AWS_REGION [--profile AWS_PROFILE (optional)]
      ```
   - If you want to retain more resources than the Terraform code does, feel free to `import` those and adjust the `delete_cf_stacks.py` script accordingly.

12. (Optional) Reorganize Terraform code as needed:
    - The terraform `move` block can be useful for restructuring
  
13. (Optional) The following resources are retained by the Cloudformation stacks but **not** managed by the generated Terraform code:
  - `/spacelift/random-suffix` SSM parameter - this isn't used in V3 anymore. You can delete it.
  - `/spacelift/install-version` SSM parameter - this isn't used in V3 anymore. You can delete it.
  - `BootstrapBucket` S3 bucket - this isn't used in V3 anymore. *Cloudformation can't delete the bucket as it's not empty, so you'll need to purge the bucket, then remove it.*
  - `AccessLogsBucket` S3 bucket - this isn't used in V3 anymore. You're free to set up access logging for the load balancer yourself, but the Terraform modules don't do that by default.
  - `BucketLogsBucket` S3 bucket - this isn't used in V3 anymore. You're free to set up access logging for S3 yourself, but the Terraform modules don't do that by default. *Cloudformation can't delete the bucket as it's not empty, so you can either delete it manually or leave it as is.*
    - There's access logging enabled for all 11 buckets. If you delete the BucketLogsBucket, make sure to manually remove the access logging configuration from these buckets as well. The setting can be found in the AWS console under the **Properties** tab of the bucket, under **Server access logging** section.
  - `XrayECRRepository` ECR repository - XRay is not part of the V3 ECS deployment by default. You can add it yourself if you want to keep using it, but the Terraform modules don't do that by default. *Cloudformation can't delete the repository as it's not empty, so you can either delete it manually or leave it as is.*
  - `BastionSecurityGroup` security group - bastion host is not part of the V3 ECS deployment by default. If you use a bastion host, ideally you should add it to your Terraform project and then `import` it. If you don't use a bastion host, you can manually delete it.
  - `InstallationTaskSecurityGroup` security group - this was used for the installation task, which is not part of the V3 ECS infrastructure anymore. Cloudformation can't delete it because the database security group's inbound rules reference it. You can manually clean it up.

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
