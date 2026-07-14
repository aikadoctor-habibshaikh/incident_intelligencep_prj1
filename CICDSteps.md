# CI/CD Implementation Steps

This document explains how to implement the CI/CD workflow for this project and deploy it on AWS using GitHub Actions, Amazon ECR, and Amazon ECS.

## 1. Prerequisites

Before starting, make sure you have:
- A GitHub repository connected to this project
- An AWS account
- Docker installed locally
- Python 3.11 installed
- Access to AWS Console

## 2. Prepare the Project Repository

### 2.1 Confirm the project structure
The repository already contains:
- Dockerfile
- pyproject.toml
- src/incident_intelligencep_prj1/main.py
- .github/workflows/ci-cd.yml
- infra/ecs-task-definition.json

### 2.2 Install local test dependencies
Run:
```bash
python -m pip install -e '.[dev]'
```

### 2.3 Verify tests locally
Run:
```bash
pytest -q
```

Expected result:
- At least one smoke test should pass.

## 3. Create GitHub Repository Secrets

In GitHub, go to:
- Repository Settings -> Secrets and variables -> Actions

Add these secrets:
- AWS_ROLE_TO_ASSUME
- AWS_REGION
- AWS_ECR_REPOSITORY
- AWS_ECS_CLUSTER
- AWS_ECS_SERVICE
- AWS_ECS_EXECUTION_ROLE_ARN
- AWS_ECS_TASK_ROLE_ARN
- AWS_ECS_SECRET_ARN (optional)

Do not add username/password credentials for Amazon ECR. The workflow authenticates to ECR through AWS IAM and OIDC using the role in `AWS_ROLE_TO_ASSUME`.

For `AWS_ECS_SERVICE`, use the exact name of the ECS service you create in the cluster. You can find it in the Amazon ECS console under the cluster -> Services tab.

## 4. Set Up AWS Resources on the Console (ordered to avoid startup errors)

This section orders the console/CLI steps so IAM roles, Secrets Manager, and KMS permissions are created before you register task definitions or start services. Follow the sequence exactly to avoid `AccessDenied` or `ResourceInitializationError` when tasks start.

### 4.1 Create the GitHub Actions IAM role (OIDC)
Create a role that GitHub Actions can assume through OpenID Connect.

1. Open the AWS Console and go to IAM.
2. Click Roles -> Create role.
3. Choose Trusted entity type: Web identity.
4. Select the GitHub Actions OIDC provider, usually `token.actions.githubusercontent.com`.
5. For Audience, choose `sts.amazonaws.com`.
6. In the Subject field, enter your repository in this format:
   - `repo:YOUR_GITHUB_USERNAME/incident_intelligencep_prj1:ref:refs/heads/main`
7. Click Next.
8. Give the role a name such as `github-actions-incident-intelligence-role`.
9. Attach permissions for ECR and ECS (or use a narrower inline policy). Example managed policies:
   - `AmazonEC2ContainerRegistryPowerUser`
   - `AmazonECS_FullAccess`
10. Click Create role and copy the Role ARN. Save it in GitHub as the secret `AWS_ROLE_TO_ASSUME`.

### 4.2 Create the ECS task execution role
This role is used by ECS when launching the container. It must be able to pull the image from ECR and send logs to CloudWatch.

1. Open IAM -> Roles -> Create role.
2. Choose AWS service -> Elastic Container Service.
3. Choose the use case: `Elastic Container Service Task`.
4. Name the role, for example: `ecsTaskExecutionRole-incident-intelligence`.
5. Click Create role.
6. Attach the managed policy `AmazonECSTaskExecutionRolePolicy`.
7. Confirm the role ARN and copy it into GitHub as `AWS_ECS_EXECUTION_ROLE_ARN`.

### 4.3 Create the ECS task role (optional but recommended)
This role is assumed by the container process. If your app calls AWS APIs directly (Secrets Manager, S3, DynamoDB), grant those permissions here.

1. Open IAM -> Roles -> Create role.
2. Choose AWS service -> Elastic Container Service.
3. Choose the use case: `Elastic Container Service Task`.
4. Name the role, for example: `ecsTaskRole-incident-intelligence`.
5. Attach only the policies your application needs.
6. Copy the role ARN into GitHub as `AWS_ECS_TASK_ROLE_ARN`.

### 4.4 Create an ECR repository
1. Open Amazon ECR
2. Click Create repository
3. Name it, for example: `incident-intelligence`
4. Create the repository

Note: The workflow authenticates to ECR through OIDC and the `AWS_ROLE_TO_ASSUME` role — do not store raw ECR credentials in GitHub.

### 4.5 Create a Secrets Manager secret (if you need runtime secrets)
1. Open the Secrets Manager console.
2. Click Store a new secret.
3. Choose Other type of secret.
4. Add a key/value pair such as `OPENAI_API_KEY` and the actual value.
5. Click Next and give the secret a name such as `incident-intelligence/openai-api-key`.
6. Click Store.

After creating the secret, run this to discover which KMS key encrypts it (optional but required if it's a customer-managed key):

```bash
aws secretsmanager describe-secret --secret-id <SECRET_ARN_OR_NAME> --region <REGION> --query KmsKeyId --output text
```

- If the result is empty or `alias/aws/secretsmanager`, the AWS-managed key is used and you generally do not need to modify KMS policies.
- If the result is a CMK ARN (e.g. `arn:aws:kms:us-east-1:123456789012:key/abcd-...`), grant `kms:Decrypt` for that key to the appropriate role (execution role if ECS fetches the secret at startup, or task role if the app fetches it at runtime).

### 4.6 Prepare IAM policy for secret access (example)
Create `policy.json` with this template and replace `<SECRET_ARN>` and `<KMS_KEY_ARN>` as necessary. If no CMK is used, remove the KMS statement.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSecretsManagerRead",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "<SECRET_ARN>"
    },
    {
      "Sid": "AllowKMSDecryptIfNeeded",
      "Effect": "Allow",
      "Action": ["kms:Decrypt"],
      "Resource": "<KMS_KEY_ARN>"
    }
  ]
}
```

Attach it to the execution role (or task role when appropriate):

```bash
aws iam put-role-policy \
  --role-name ecsTaskExecutionRole-incident-intelligence \
  --policy-name AllowSecretsManagerGet \
  --policy-document file://policy.json
```

### 4.7 Create an ECS cluster
1. In the AWS Console go to Amazon ECS.
2. Click Clusters -> Create cluster.
3. Choose the Networking only (Fargate) option.
4. Enter a cluster name, for example: `incident-intelligence-cluster`.
5. Click Create and wait until the cluster appears in the list.

### 4.8 Create an ECS task definition
1. In the ECS console, open Task definitions.
2. Click Create new task definition.
3. Choose Fargate.
4. Enter the task family name, for example: `incident-intelligence-task`.
5. Set CPU to `0.5 vCPU` (512 CPU units) and Memory to `1 GB`.
6. In the container definition section, click Add container.
7. Enter the container name (e.g. `incident-intelligence`) and set the image to the ECR image URI.
8. Set the port mapping to `8000`.
9. Add environment variables if needed (e.g. `PYTHONUNBUFFERED=1`, `TASK_NAME=full`, `MODEL=gpt-4o-mini`).
10. In the Secrets section, click Add secret and set the Name to `OPENAI_API_KEY` and ValueFrom to the secret ARN you created earlier.
11. Set the logging driver to `awslogs` and configure the log group `/ecs/incident-intelligence` with Stream prefix `ecs`.
12. Click Add and then Create.

### 4.9 Create an ECS service
1. Open the cluster you created earlier.
2. Click Create under the Services tab.
3. Choose Launch type: FARGATE.
4. Select the task definition you just created.
5. Set the desired number of tasks to `1`.
6. Choose the VPC, subnets, and security group for the service.
7. For public access, make sure the subnets are public and the security group allows inbound traffic on port `8000`.
8. If you want the service to be reachable from the internet, create or attach an Application Load Balancer and configure the target group and listener.
9. Click Next, review the settings and Create Service.

If you make IAM changes after the service is created, force a new deployment so the tasks pick up updated permissions:

```bash
aws ecs update-service --cluster <CLUSTER_NAME> --service <SERVICE_NAME> --force-new-deployment --region <REGION>
```

### 4.10 Verify the service and task
1. After the service is created, wait until the task reaches the RUNNING state.
2. Open the service details and click the task ID to inspect the task.
3. Review the Events tab for any startup issues.
4. Check CloudWatch logs if the container fails.

### 4.11 Optional: create a public endpoint with ALB
1. In the EC2 console, create an Application Load Balancer.
2. Choose internet-facing and select the public subnets.
3. Create a target group for port `8000` and add the ECS service as a target.
4. Configure the listener to forward HTTP (port `80`) to the target group.
5. After the ALB is active, note the DNS name and use it as the public endpoint.

### 4.8 Prepare IAM, Secrets Manager and KMS (required before creating ECS service)
Before you create a task definition that references a Secrets Manager secret or create an ECS service, ensure the IAM roles and KMS permissions are in place. If these are missing, tasks will fail at startup with AccessDenied/ResourceInitializationError.

Follow this sequence precisely:

1. Create or confirm the ECS task execution role exists and attach the managed policy:

```bash
# Example: create role via Console or use an existing role name below
# Attach managed policy (if not already attached)
aws iam attach-role-policy \
   --role-name ecsTaskExecutionRole-incident-intelligence \
   --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

2. Create the Secrets Manager secret (if not created):

```bash
aws secretsmanager create-secret \
   --name incident-intelligence/openai-api-key \
   --secret-string '{"OPENAI_API_KEY":"<your-key-here>"}' \
   --region <REGION>
```

3. Discover the KMS key used to encrypt the secret (if any). Run:

```bash
aws secretsmanager describe-secret \
   --secret-id <SECRET_ARN_OR_NAME> \
   --region <REGION> --query KmsKeyId --output text
```

- If this returns an ARN like `arn:aws:kms:...:key/<key-id>` or an alias, the secret uses a customer-managed CMK.
- If it returns empty or `alias/aws/secretsmanager`, the AWS-managed Secrets Manager key is used (no KMS policy changes needed).

4. If a customer-managed KMS key is used, grant `kms:Decrypt` to the role. You can either update the key policy in the KMS console or attach an inline IAM policy to the role. Example inline policy JSON (`policy.json`):

```json
{
   "Version": "2012-10-17",
   "Statement": [
      {
         "Sid": "AllowSecretsManagerRead",
         "Effect": "Allow",
         "Action": [
            "secretsmanager:GetSecretValue",
            "secretsmanager:DescribeSecret"
         ],
         "Resource": "<SECRET_ARN>"
      },
      {
         "Sid": "AllowKMSDecryptIfNeeded",
         "Effect": "Allow",
         "Action": ["kms:Decrypt"],
         "Resource": "<KMS_KEY_ARN>"
      }
   ]
}
```

5. Attach the inline policy to the execution role (replace the role name as needed):

```bash
aws iam put-role-policy \
   --role-name ecsTaskExecutionRole-incident-intelligence \
   --policy-name AllowSecretsManagerGet \
   --policy-document file://policy.json
```

Notes on roles:
- `execution role` (executionRoleArn in task definition) is used by ECS to pull images, fetch secrets at startup, and write logs. Give the SecretsManager and (if needed) KMS permissions to the execution role.
- `task role` (taskRoleArn) is assumed by the running container process; if your application fetches secrets itself via SDK calls, grant it SecretsManager/KMS permissions instead of, or in addition to, the execution role.

6. Create or update the ECS task definition and add the secret under the container `Secrets` section using the secret ARN.

7. Create the ECS service. If you made IAM changes after the service was created, force a new deployment so tasks pick up the updated role permissions:

```bash
aws ecs update-service --cluster <CLUSTER_NAME> --service <SERVICE_NAME> --force-new-deployment --region <REGION>
```

Verification checklist:
- Task reaches `RUNNING` state (no ResourceInitializationError).
- CloudWatch logs show container startup output.
- AWS CloudTrail or IAM Access Advisor shows `secretsmanager:GetSecretValue` calls by the role.

If you want, paste your secret ARN, region, and the exact role name and I will generate a ready-to-run `policy.json` and the CLI commands filled with your values.

## 5. Configure the GitHub Actions Workflow

The workflow file is already created at:
- .github/workflows/ci-cd.yml

It performs:
1. Test job
2. Build and push Docker image
3. Render ECS task definition
4. Register task definition
5. Update ECS service
6. Wait for deployment to complete

## 6. Push Changes to GitHub

Run:
```bash
git add .
git commit -m "Add CI/CD pipeline"
git push origin main
```

## 7. Verify GitHub Actions Run

In GitHub:
1. Open the Actions tab
2. Check the workflow run
3. Confirm the test job passes
4. Confirm the deployment job succeeds

## 8. Verify AWS Deployment

After deployment:
1. Open Amazon ECS
2. Check the service status
3. Open the task details
4. Review CloudWatch logs
5. Confirm the app is healthy

## 9. Troubleshooting

### Common issue: GitHub Actions cannot assume AWS role
Check:
- OIDC trust relationship is configured correctly
- The role ARN is correct in GitHub secret `AWS_ROLE_TO_ASSUME`

### Common issue: ECS service does not update
Check:
- Task definition registration succeeded
- The cluster and service names are correct
- The task execution role has sufficient permissions

### Common issue: Container fails to start
Check:
- Environment variables are set correctly
- Secrets ARN is valid
- The image exists in ECR
- Logs are available in CloudWatch

## 10. Recommended Next Improvements

After the basic deployment works, you can add:
- Environment-based deployment stages
- Automatic rollback on failure
- Docker image vulnerability scanning
- Better health checks and alerts
