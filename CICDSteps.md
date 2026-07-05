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

## 4. Set Up AWS Resources on the Console

### 4.1 Create an ECR repository
In AWS Console:
1. Open Amazon ECR
2. Click Create repository
3. Name it, for example: `incident-intelligence`
4. Create the repository

Note: Amazon ECR does not support private repository credentials as a GitHub Actions authentication method. Use IAM-based authentication through OIDC and the AWS role configured in the workflow instead.

### 4.2 Create an ECS cluster
1. Open the AWS Console and go to Amazon ECS.
2. In the left menu, click Clusters.
3. Click Create cluster.
4. Choose the Networking only (Fargate) option.
5. Enter a cluster name, for example: `incident-intelligence-cluster`.
6. Leave the default settings as they are for the first setup.
7. Click Create.
8. If you see an error such as:
   - `A CloudFormation stack already exists for a failed cluster with the same name`
   then do the following:
   - Open the CloudFormation console.
   - Find the failed stack whose name starts with `Infra-ECS-Cluster-`.
   - Review the failure reason.
   - Delete the failed stack if it is no longer needed.
   - Retry the cluster creation with a new name, such as `incident-intelligence-cluster-2`.
9. Wait until the cluster appears in the list.

### 4.3 Create an ECS task definition
1. In the ECS console, open Task definitions.
2. Click Create new task definition.
3. Choose Fargate.
4. Enter a task definition family name, for example: `incident-intelligence-task`.
5. Set CPU to `0.5 vCPU` (512 CPU units).
6. Set Memory to `1 GB`.
7. In the container definition section, click Add container.
8. Enter the container name, for example: `incident-intelligence`.
9. Set the image to the ECR image URI that will be pushed by the workflow, for example:
   `123456789012.dkr.ecr.us-east-1.amazonaws.com/incident-intelligence:latest`
10. Set the port mapping to `8000`.
11. Add environment variables if needed:
   - `PYTHONUNBUFFERED=1`
   - `TASK_NAME=full`
   - `MODEL=gpt-4o-mini`
12. If you use a secret such as `OPENAI_API_KEY`, add it under Secrets and select the AWS Secrets Manager value.
    - Open the Secrets Manager console.
    - Click Store a new secret.
    - Choose Other type of secret.
    - Add a key/value pair such as `OPENAI_API_KEY` and the actual value.
    - Click Next, give the secret a name such as `incident-intelligence/openai-api-key`.
    - Click Store.
    - Go back to the ECS task definition page.
    - In the container definition, open the Secrets section.
    - Click Add secret.
    - Set the Name to `OPENAI_API_KEY`.
    - Set the ValueFrom field to the full ARN of the secret you just created.
13. Set the logging driver to `awslogs`.
    - In the container definition, open the Logging section.
    - Choose `awslogs` from the Log driver dropdown.
    - Set the Log group name to `/ecs/incident-intelligence`.
    - Set the Stream prefix to `ecs`.
    - If the log group does not exist, AWS will create it automatically when the task starts.
14. Configure CloudWatch log group, for example: `/ecs/incident-intelligence`.
    - Open CloudWatch.
    - Go to Log groups.
    - Confirm the group `/ecs/incident-intelligence` exists.
    - If needed, create it manually before starting the task.
15. Click Add.
16. Click Create.

### 4.4 Create an ECS service
1. Open the cluster you created earlier.
2. Click Create under the Services tab.
3. Choose Launch type: FARGATE.
4. Select the task definition you just created.
5. Set the desired number of tasks to `1`.
6. Choose the VPC, subnets, and security group for the service.
7. For public access, make sure the subnets are public subnets and the security group allows inbound traffic on port `8000`.
8. If you want the service to be reachable from the internet, create or attach an Application Load Balancer.
9. Configure the target group and listener for port `80` or `443`.
10. Click Next and review the settings.
11. Click Create Service.

### 4.5 Verify the service and task
1. After the service is created, wait until the task reaches the RUNNING state.
2. Open the service details.
3. Click the task ID to inspect the task.
4. Review the Events tab for any startup issues.
5. Check CloudWatch logs if the container fails.

### 4.6 Optional: create a public endpoint with ALB
1. In the EC2 console, create an Application Load Balancer.
2. Choose internet-facing.
3. Select the public subnets.
4. Create a target group for port `8000`.
5. Add the ECS service as a target.
6. Configure the listener to forward HTTP (port `80`) to the target group.
7. After the ALB is active, note the DNS name and use it as the public endpoint.

### 4.4 Create the GitHub Actions IAM role (OIDC)
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
   Suggested role name: `github-actions-incident-intelligence-role`
9. Attach permissions for ECR and ECS. A simple approach is to attach:
   - `AmazonEC2ContainerRegistryPowerUser`
   - `AmazonECS_FullAccess`
10. If you prefer a narrower policy, use an inline policy with these actions:
    - `ecr:GetAuthorizationToken`
    - `ecr:BatchCheckLayerAvailability`
    - `ecr:CompleteLayerUpload`
    - `ecr:InitiateLayerUpload`
    - `ecr:PutImage`
    - `ecr:UploadLayerPart`
    - `ecs:DescribeServices`
    - `ecs:DescribeTaskDefinition`
    - `ecs:RegisterTaskDefinition`
    - `ecs:UpdateService`
    - `ecs:DescribeClusters`
    - `iam:PassRole`
11. Click Create role.
12. Open the new role and copy the Role ARN.
13. Save that ARN in GitHub as the secret `AWS_ROLE_TO_ASSUME`.

### 4.5 Create the ECS task execution role
This role is used by ECS when launching the container. It must be able to pull the image from ECR and send logs to CloudWatch.

1. Open IAM -> Roles -> Create role.
2. Choose AWS service -> Elastic Container Service.
3. Choose the use case: `Elastic Container Service Task`.
4. Name the role, for example: `ecsTaskExecutionRole-incident-intelligence`.
   Suggested role name: `ecsTaskExecutionRole-incident-intelligence`
5. Click Create role.
6. Attach the managed policy `AmazonECSTaskExecutionRolePolicy`.
7. Confirm the role ARN and copy it into GitHub as `AWS_ECS_EXECUTION_ROLE_ARN`.

### 4.6 Create the ECS task role (optional but recommended)
This role is used by the container itself if the application needs to call AWS services such as S3, Secrets Manager, or DynamoDB.

1. Open IAM -> Roles -> Create role.
2. Choose AWS service -> Elastic Container Service.
3. Choose the use case: `Elastic Container Service Task`.
4. Name the role, for example: `ecsTaskRole-incident-intelligence`.
   Suggested role name: `ecsTaskRole-incident-intelligence`
5. Attach only the policies your application needs.
6. Copy the role ARN into GitHub as `AWS_ECS_TASK_ROLE_ARN`.

If your application does not call AWS APIs, you can use the same ARN as the execution role for this project.

### 4.7 Create a secret in AWS Secrets Manager (optional)
If the app needs runtime secrets such as `OPENAI_API_KEY`, store them in AWS Secrets Manager and reference the ARN in the workflow and task definition.

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
