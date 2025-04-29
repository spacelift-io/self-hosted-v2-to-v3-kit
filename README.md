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
- Creates a script to handle a small infrastructural difference between V2 and V3 (Internet gateway refactoring)
- Creates a script to tear down the old CloudFormation stacks with retaining resources
- Enables zero-downtime migration (flipping the CNAME record to the new load balancer)
- Supports custom VPC configurations (using existing VPC resources instead of creating new ones)
- Supports bi-regional disaster recovery setups

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

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/spacelift-io/self-hosted-v2-to-v3-kit.git
cd self-hosted-v2-to-v3-kit

# Create a Python 3 virtual environment (requires Python 3.8+)
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

### Notes for two-regions (disaster recovery) setups

When you have a [bi-regional setup with a primary and a secondary region](https://docs.spacelift.io/self-hosted/latest/product/administration/disaster-recovery.html), you'll need to execute everything twice. First for the primary region, then for the secondary one. Don't forget to have the outputs in different folders, eg.:

```bash
python main.py --config "<sh-v2-primary-config-file-path.json>" --output dist-eu-west-1-primary
python main.py --config "<sh-v2-secondary-config-file-path.json>" --output dist-eu-west-2-secondary
```

As per the [official documentation](https://docs.spacelift.io/self-hosted/latest/product/administration/disaster-recovery.html), with such a setup, you already handle your RDS setup outside of the Cloudformation realm, and you just pass in a SecretsManager Secret holding the connection string and a KMS ARN encrypting the Secret (specifically `database.connection_string_ssm_arn` and `database.connection_string_ssm_kms_arn` config options).

This migration tool has the same approach: it'll just inject your custom secret into the app, but will leave you to manage your database setup yourself. However, you are welcome to define those RDS resources and import them to the project.

### Step 1: Generate Terraform project

#### Prerequisites

> Make sure the virtualenv is activated when running the Python scripts as they depend on `boto3`.

Run the main script with your config file path:

```bash
python main.py --config "<sh-v2-config-file-path.json>"
```

Additional arguments:
- `--profile`: AWS profile to use (optional)
- `--output`: Output directory path for the Terraform project (default: `dist`)

The script will:
1. Scan for all relevant AWS resources in your current Spacelift deployment
2. Get the unique suffix from SSM Parameter Store (from `/spacelift/random-suffix`)
3. Generate Terraform files in the output folder
4. Create 2 scripts in the output folder: Internet gateway refactoring, and the CloudFormation deletion script

### Step 2: Apply the Generated Terraform Code

Navigate to the output directory and follow these steps:

1. ❗️ You only need to do this step if you don't use a custom VPC, but the one packaged with Self-Hosted. This isn't a really functional change, but a small simplification we did for SelfHosted V3. Nothing really happens if you don't do it for your custom VPC.
   This script adjusts a small infrastructural difference between V2 and V3: consolidating multiple internet gateways into one shared gateway for all public subnets. Since the commands in the scripts are executed in an instant, the existing application should not be affected - at maximum having a one-second blip for outbound traffic.

   > The reason this step is a separate script instead of being part of the Terraform code is that Terraform has troubles properly ordering the removal and additions of internet gateway subnet associations, and AWS is very picky about the order of these operations.

   Old infrastructure (SelfHosted V2):
   ```mermaid
   graph TD;
      A("PublicSubnet1")-->B("InternetGateway1");
      C("PublicSubnet2")-->D("InternetGateway3");
      E("PublicSubnet3")-->F("InternetGateway3");
   ```
   New infrastructure (SelfHosted V3):
   ```mermaid
   graph TD;
      A("PublicSubnet1")-->B("InternetGateway1");
      C("PublicSubnet2")-->B;
      E("PublicSubnet3")-->B;
   ```
   Run the internet gateway refactoring script by:
   ```bash
   python <output-folder>/internet_gateway_refactor.py [--profile AWS_PROFILE (optional)]
   ```

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
   - 100+ resource imports (a bit less for custom VPC users)
   - ECR lifecycle policy replacements
   - A global RDS cluster creation (for high availability)
   - Various in-place changes (mostly tag-related)

   When reviewing, look for important changes:
   - `replaced` resources
   - `updated in-place` changes
   - `created` resources
   - `destroy` operations
   
   Keep an eye on any `replaced` or `destroy` actions - they might cause downtime or wipe out data. **The generated code isn’t set in stone, so feel free to tweak it**. Just be especially careful with the persistence layer, like RDS and S3 - if those get destroyed, your data’s gone for good. That said, you’re safe with S3 since buckets can’t be deleted if they still have objects in them. Plus, deletion protection is turned on by default for the RDS cluster, which helps prevent accidental data loss as well.

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
   - If you confirmed that the new `drain` and `scheduler` services are up and running (the services are stable, the logs look good), scale down the old `drain` and `scheduler` services as well

   In case you're experiencing issues, you can just revert the DNS change and scale up the old ECS cluster's services.

11.  Clean up obsolete resources:

> ‼️ Before executing this step, make sure that the traffic is properly routed to the new load balancer and everything is working as expected. Ideally, scale down the old cluster's `server`/`drain`/`scheduler` services to 0 tasks, and leave the environment for a few days to ensure everything is functioning correctly.

   - Use the CloudFormation stack deletion script to get rid of the old Cloudformation stacks while retaining the resources you want to keep:
      ```bash
      python <output-folder>/delete_cf_stacks.py --region AWS_REGION [--profile AWS_PROFILE (optional)]
      ```
   - The script will delete all Cloudformation stacks, but retain those resources that are part of the V3 infrastructure and part of the Terraform code.
     - It'll delete the entirety of the old ECS cluster, including the load balancer and all the services.
     - Note that it'll delete the monitoring stack as well. The CloudWatch dashboard this stack created will be partially useless since the underlying ECS cluster and load balancer is getting deleted anyway. If you'd like to keep it, add the logical IDs of the resources next to the `spacelift-monitoring` part of the script in the `delete_stacks` method. The logical IDs can be found in the `spacelift-monitoring` stack's **Resources** tab in the AWS console, or by running `aws cloudformation describe-stack-resources --stack-name spacelift-monitoring --query 'StackResources[*].LogicalResourceId' --region <aws-region>` command.
   - If you want to retain more resources than the Terraform code does, feel free to `import` those and adjust the `delete_cf_stacks.py` script accordingly.

12.  (Optional) Reorganize Terraform code as needed:

- The Terraform [`moved` block](https://developer.hashicorp.com/terraform/tutorials/configuration-language/move-config) can be useful for restructuring
  
13.  (Optional) The following resources are retained by the Cloudformation stacks but **not** managed by the generated Terraform code:
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
