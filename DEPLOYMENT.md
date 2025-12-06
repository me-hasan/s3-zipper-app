# Deployment Guide

## Quick Start

### Prerequisites
- AWS CLI configured with credentials
- Docker installed
- SAM CLI installed: `pip install aws-sam-cli`

### Step 1: Clone Repository
```bash
git clone https://github.com/me-hasan/s3-zipper-app.git
cd s3-zipper-app
```

### Step 2: Build Application
```bash
sam build --use-container
```

### Step 3: Deploy
```bash
# First deployment (interactive)
sam deploy --guided

# Subsequent deployments
sam deploy
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

# Check for compressed file
aws s3 ls s3://$BUCKET/uploads/ --recursive
```

## Deployment Parameters

When running `sam deploy --guided`, use these parameters:

```
Stack Name: s3-zipper-app-stack
Region: us-east-1 (or your preferred region)
Environment Name: dev (or prod for production)
VPC CIDR: 10.0.0.0/16
Private Subnet 1 CIDR: 10.0.1.0/24
Private Subnet 2 CIDR: 10.0.2.0/24
S3 Bucket Name: s3-zipper-app-XXXXXXXXXX (must be globally unique)
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
# List available function versions
aws lambda list-versions-by-function --function-name dev-s3-zipper-function

# Rollback to previous version
aws lambda update-alias \
  --function-name dev-s3-zipper-function \
  --name live \
  --function-version 2
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
