# Deployment Guide

## Quick Start

### Prerequisites
- AWS CLI configured with credentials
- Docker installed
- SAM CLI installed: `pip install aws-sam-cli`
 - GitHub repository with Actions enabled

### Step 1: Clone Repository
```bash
git clone https://github.com/me-hasan/s3-zipper-app.git
cd s3-zipper-app
```

### Step 2: Build Application
```bash
sam build --use-container
```

### Step 3: Set Up CI Secrets
In GitHub → Repository → Settings → Secrets and variables → Actions, add:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### Step 4: Deploy (CI or Local)
#### CI (recommended)
Push to `main` and let the workflow deploy automatically.
#### Local (non-interactive)
```bash
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=s3-zipper-app-$(date +%s)

# Ensure ECR exists and login
aws ecr describe-repositories --repository-names s3-zipper-app --region $AWS_REGION >/dev/null 2>&1 || \
  aws ecr create-repository --repository-name s3-zipper-app --region $AWS_REGION
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com

sam build --use-container --region $AWS_REGION

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
IMAGE_REPO="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/s3-zipper-app"
sam deploy \
  --stack-name s3-zipper-app-stack \
  --region $AWS_REGION \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset \
  --image-repository "$IMAGE_REPO" \
  --parameter-overrides S3BucketName=$S3_BUCKET_NAME EnvironmentName=dev
```

### Step 4: Test
```bash
# Get bucket name
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name s3-zipper-app-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
  --output text)

# Upload a test file
aws s3 cp README.md s3://$BUCKET/uploads/test-file.txt

# Check for compressed file (original deleted)
aws s3 ls s3://$BUCKET/uploads/ --recursive
```

## Deployment Parameters

When running `sam deploy --guided`, use these parameters:

```
Stack Name: s3-zipper-app-stack
Region: us-east-1 (or your preferred region)
Environment Name: dev or prod
S3 Bucket Name: s3-zipper-app-XXXXXXXXXX (must be globally unique)
Note: VPC and Lambda versioning can be reintroduced using `template.yaml.bak` once deployment stabilization is complete.
```

## Troubleshooting

### Lambda not triggered
- Check S3 event notification: `aws s3api get-bucket-notification-configuration --bucket <bucket-name>`
- Ensure file is uploaded to `uploads/` prefix
- Check Lambda CloudWatch logs

### Permission denied errors
- Verify IAM role has S3 permissions
- Check bucket policy allows Lambda execution

### Deployment failed
- Run `sam validate` to check template
- Check IAM permissions in AWS account
- Verify Docker is running if using `--use-container`

## Rollback

```bash
# Use CloudFormation to rollback to a previous stack or redeploy prior image tag.
```

## Clean Up

```bash
# Delete CloudFormation stack (also deletes all resources)
aws cloudformation delete-stack --stack-name s3-zipper-app-stack

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete --stack-name s3-zipper-app-stack
```

## Support

For issues or questions, create an issue on the GitHub repository.
