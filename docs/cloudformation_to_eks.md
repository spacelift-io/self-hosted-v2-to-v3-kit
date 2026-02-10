# CloudFormation to EKS Migration

This guide walks you through migrating a Spacelift Self-Hosted V2 (CloudFormation) installation to V3 using the EKS Terraform module.

The EKS module ([terraform-aws-eks-spacelift-selfhosted](https://github.com/spacelift-io/terraform-aws-eks-spacelift-selfhosted)) bundles all base infrastructure (VPC, S3, RDS, ECR) together with the EKS cluster, IAM roles (IRSA), and Helm value generation into a single module. This is different from the ECS path where base infra and services are two separate modules.

## Installation

```bash
# Clone the repository
git clone https://github.com/spacelift-io/self-hosted-v2-to-v3-kit.git
cd self-hosted-v2-to-v3-kit

# Create a Python 3 virtual environment (requires Python 3.8+)
python -m venv env

# Activate the virtual environment
# On Unix/Linux/MacOS:
source env/bin/activate
# On Windows:
# env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Step 1: Generate Terraform project

> Make sure the virtualenv is activated when running the Python scripts as they depend on `boto3`.

Run the main script with your config file path and `--target-module eks`:

```bash
python main.py --config "<sh-v2-config-file-path.json>" --target-module eks
```

Additional arguments:
- `--profile`: AWS profile to use (optional)
- `--output`: Output directory path for the Terraform project (default: `dist`)

The script will:
1. Scan for all relevant AWS resources in your current Spacelift deployment
2. Get the unique suffix from SSM Parameter Store (from `/spacelift/random-suffix`)
3. Generate Terraform files in the output folder with a single `module "spacelift_eks"` block that wraps all base infrastructure and EKS resources
4. Generate import blocks for existing resources (S3 buckets, RDS, VPC, ECR, KMS, SQS, IoT, SecretsManager)
5. Create a script to tear down the old CloudFormation stacks while retaining imported resources

#### Internet gateway refactoring

If you don't use a custom VPC (i.e. you use the one packaged with Self-Hosted), run the internet gateway refactoring script. This consolidates multiple internet gateway route tables into a single table with a route for each public subnet - a small structural difference between CloudFormation and Terraform. The commands execute instantly; the existing application should not be affected beyond a potential one-second blip for outbound traffic.

```bash
python <output-folder>/internet_gateway_refactor.py [--profile AWS_PROFILE (optional)]
```

> The reason this is a separate script instead of being part of the Terraform code is that Terraform has trouble properly ordering the removal and addition of internet gateway subnet associations, and AWS is very picky about the order of these operations.

#### Configure the generated Terraform files

After generation, open `main.tf` in the output directory and fill in the following values:

- `local.license_token` - set this to the license token you received from Spacelift.
- `server_acm_arn` in the `module "spacelift_eks"` block - set this to the ARN of your ACM certificate for the Spacelift server domain. You can reuse the same certificate from your existing V2 load balancer (`load_balancer.certificate_arn` in your V2 config file).

### Step 2: Apply the Generated Terraform Code

_In the steps below we use OpenTofu. Feel free to swap `tofu` for `terraform` if you prefer._

Navigate to the output directory, initialize and apply:

```bash
tofu init
tofu plan -out=plan
```

Review the plan carefully. It should include 100+ resource imports, some in-place changes (mostly tags), and creation of the EKS cluster and its associated resources. Watch out for any `replaced` or `destroy` actions on stateful resources like RDS and S3.

```bash
tofu apply plan
```

Once applied, source the shell output to export all required environment variables for the next steps:

```shell
$(tofu output -raw shell)
```

> Keep the same shell open for the remaining steps since the exported variables are needed throughout.

### Step 3: Upload Container Images and Binaries

With the shell variables sourced, push the container images and launcher binary. Make sure you have the Self-Hosted release .tar.gz file available:

```shell
# Login to the private ECR
aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${PRIVATE_ECR_LOGIN_URL}"

tar -xzf self-hosted-${SPACELIFT_VERSION}.tar.gz -C .

docker image load --input="self-hosted-${SPACELIFT_VERSION}/container-images/spacelift-launcher.tar"
docker tag "spacelift-launcher:${SPACELIFT_VERSION}" "${LAUNCHER_IMAGE}:${SPACELIFT_VERSION}"
docker push "${LAUNCHER_IMAGE}:${SPACELIFT_VERSION}"

docker image load --input="self-hosted-${SPACELIFT_VERSION}/container-images/spacelift-backend.tar"
docker tag "spacelift-backend:${SPACELIFT_VERSION}" "${BACKEND_IMAGE}:${SPACELIFT_VERSION}"
docker push "${BACKEND_IMAGE}:${SPACELIFT_VERSION}"

# Only needed if you plan to run workers outside of Kubernetes
aws s3 cp --no-guess-mime-type "./self-hosted-${SPACELIFT_VERSION}/bin/spacelift-launcher" "s3://${BINARIES_BUCKET_NAME}/spacelift-launcher"
```

### Step 4: Deploy Spacelift to EKS

Configure kubectl to talk to the new EKS cluster:

```shell
export KUBECONFIG=${HOME}/.kube/config_spacelift
aws eks update-kubeconfig --name ${EKS_CLUSTER_NAME} --region ${AWS_REGION}
```

> Make sure the `KUBECONFIG` variable stays set for all kubectl and helm commands below.

Create the Kubernetes namespace:

```shell
kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: "$K8S_NAMESPACE"
  labels:
    eks.amazonaws.com/pod-readiness-gate-inject: "enabled"
EOF
```

Create the IngressClass (configures the ALB with your ACM certificate and subnets):

```shell
tofu output -raw kubernetes_ingress_class | kubectl apply -f -
```

Create the Kubernetes secrets used by Spacelift services:

```shell
tofu output -raw kubernetes_secrets | kubectl apply -f -
```

> [!IMPORTANT]
> The generated K8s secrets do not automatically include values from the following SecretsManager secrets. If you use any of these, retrieve their values and add them to the appropriate K8s secret before deploying:
> - `spacelift/slack-application` - copy `SLACK_APP_CLIENT_ID`, `SLACK_APP_CLIENT_SECRET`, and `SLACK_SECRET` into the K8s `spacelift-shared` secret
> - `spacelift/additional-root-ca-certificates` - only relevant if you configured custom CA certificates in your V2 installation (via `tls_config.ca_certificates` in the config file), for example when using self-signed TLS certificates. The secret contains the `ADDITIONAL_ROOT_CAS` env var, which should be copied into the `spacelift-shared` K8s secret. The format is double-base64-encoded: a JSON object `{"caCertificates": ["<base64-pem>", ...]}` that is itself base64-encoded. You can retrieve the current value with:
> ```shell
> aws secretsmanager get-secret-value --secret-id "spacelift/additional-root-ca-certificates" --region "${AWS_REGION}" --query SecretString --output text
> ```

#### Migrate SAML credentials

> [!WARNING]
> Only relevant if your V2 installation uses SAML SSO. If you don't use SAML, skip this step.
> If you do use SAML, you **must** complete this before deploying, otherwise SAML authentication will not work.

The V2 CloudFormation stack stores the SAML certificate and signing key in the `spacelift/saml-credentials` SecretsManager secret (with JSON keys `certificate` and `key`, both base64-encoded). These need to be added to the `spacelift-server` K8s secret as `SAML_CERT` and `SAML_KEY`:

```shell
SAML_SECRET=$(aws secretsmanager get-secret-value --secret-id "spacelift/saml-credentials" --region "${AWS_REGION}" --query SecretString --output text)

kubectl patch secret spacelift-server -n "$K8S_NAMESPACE" --type merge -p "{\"stringData\": {
  \"SAML_CERT\": $(echo "$SAML_SECRET" | jq '.certificate'),
  \"SAML_KEY\": $(echo "$SAML_SECRET" | jq '.key')
}}"
```

Generate the Helm values and deploy Spacelift:

```shell
tofu output -raw helm_values > spacelift-values.yaml

helm upgrade \
  --repo https://downloads.spacelift.io/helm \
  spacelift \
  spacelift-self-hosted \
  --install --wait --timeout 20m \
  --namespace "$K8S_NAMESPACE" \
  --values "spacelift-values.yaml"
```

> You can follow deployment progress with: `kubectl logs -n ${K8S_NAMESPACE} deployments/spacelift-server`

### Step 5: Redirect Traffic

Once the Helm chart is deployed, get the load balancer address for Spacelift:

```shell
kubectl get ingresses --namespace "$K8S_NAMESPACE"
```

Update your `CNAME` record to point your Spacelift domain to the ingress `ADDRESS`.

Since your V2 installation uses AWS IoT Core as the MQTT broker, external workers will continue to connect through IoT Core and no additional MQTT DNS setup is needed.

To verify the traffic is properly routed, you can scale down the old ECS cluster's `server` service to 0 tasks. If you confirmed that the new `drain` and `scheduler` services are up and running (the services are stable, the logs look good), scale down the old `drain` and `scheduler` services as well.

In case you're experiencing issues, you can revert the DNS change and scale up the old ECS cluster's services.

### Step 6: Clean Up Obsolete Resources

> Before executing this step, make sure that the traffic is properly routed to the new deployment and everything is working as expected. Ideally, scale down the old cluster's services to 0 tasks and leave the environment for a few days to make sure everything is functioning correctly.

Use the CloudFormation stack deletion script to get rid of the old CloudFormation stacks while retaining the resources managed by Terraform:

```bash
python <output-folder>/delete_cf_stacks.py --region AWS_REGION [--profile AWS_PROFILE (optional)]
```

The script will delete all CloudFormation stacks, but retain those resources that are part of the V3 infrastructure and managed by the Terraform code.
- It will delete the entirety of the old ECS cluster, including the load balancer and all the services.
- It will delete the monitoring stack as well. The CloudWatch dashboard this stack created will be partially useless since the underlying ECS cluster and load balancer are getting deleted anyway. If you'd like to keep it, add the logical IDs of the resources next to the `spacelift-monitoring` part of the script in the `delete_stacks` method. The logical IDs can be found in the `spacelift-monitoring` stack's **Resources** tab in the AWS console, or by running `aws cloudformation describe-stack-resources --stack-name spacelift-monitoring --query 'StackResources[*].LogicalResourceId' --region <aws-region>`.

If you want to retain more resources than the Terraform code does, feel free to `import` those and adjust the `delete_cf_stacks.py` script accordingly.

### Retained but Unmanaged Resources

The following resources are retained by the CloudFormation stacks but **not** managed by the generated Terraform code:
- `/spacelift/random-suffix` SSM parameter - not used by Terraform-managed deployments. You can delete it.
- `/spacelift/install-version` SSM parameter - not used by Terraform-managed deployments. You can delete it.
- `BootstrapBucket` S3 bucket - not used by Terraform-managed deployments. CloudFormation can't delete the bucket as it's not empty, so you'll need to purge the bucket and then remove it.
- `AccessLogsBucket` S3 bucket - not used by Terraform-managed deployments. You're free to set up access logging for the load balancer yourself, but the Terraform module doesn't do that by default.
- `BucketLogsBucket` S3 bucket - not used by Terraform-managed deployments. You're free to set up S3 access logging yourself, but the Terraform module doesn't do that by default. CloudFormation can't delete the bucket as it's not empty, so you can either delete it manually or leave it as is.
  - There's access logging enabled for all 11 buckets. If you delete the BucketLogsBucket, make sure to manually remove the access logging configuration from these buckets as well. The setting can be found in the AWS console under the **Properties** tab of the bucket, under **Server access logging**.
- `XrayECRRepository` ECR repository - XRay is not part of the Terraform-managed deployment by default. CloudFormation can't delete the repository as it's not empty, so you can either delete it manually or leave it as is.
- `BastionSecurityGroup` security group - bastion host is not part of the Terraform-managed deployment. If you use a bastion host, add it to your Terraform project and `import` it. Otherwise, you can manually delete it.
- `InstallationTaskSecurityGroup` security group - this was used for the installation task, which no longer exists in Terraform-managed deployments. CloudFormation can't delete it because the database security group's inbound rules reference it. You can manually clean it up.
- SecretsManager secrets - once their values have been migrated to K8s secrets (see Step 4), the following can be safely removed: `spacelift/slack-application`, `spacelift/additional-root-ca-certificates`, `spacelift/external`, `spacelift/saml-credentials`, `DBMasterCredentials-*`. **Do not** delete `spacelift/db-password` as it is referenced by the RDS cluster resource itself. Similarly, `spacelift/db-conn-string` is created by the underlying Terraform module so refrain from deleting it as well.
