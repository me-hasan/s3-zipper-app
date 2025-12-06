# S3 Object Compression Lambda Application

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup & Deployment](#setup--deployment)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Cost Analysis](#cost-analysis)
- [Scalability & Performance](#scalability--performance)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)

## Overview

This project implements an automated S3 object compression system using AWS Lambda, CloudFormation, and Docker. When files are uploaded to an S3 bucket, a Lambda function automatically compresses them into ZIP format and removes the original objects. The solution is designed for media companies processing large quantities of high-quality videos.

**Key Features:**
- Automatic compression of objects on S3 upload
- Runs in private VPC subnets with network isolation
- Dockerized Lambda function for consistency
- Versioning and rollback capability
- CloudWatch monitoring and alarms
- Infrastructure as Code using AWS SAM

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                      AWS Cloud                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              VPC (10.0.0.0/16)                         │ │
│  │                                                        │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │        Private Subnet 1 (10.0.1.0/24)           │ │ │
│  │  │  ┌────────────────────────────────────────────┐  │ │ │
│  │  │  │  Lambda Function (Dockerized)            │  │ │ │
│  │  │  │  - Compression Logic                      │  │ │ │
│  │  │  │  - S3 Client Operations                   │  │ │ │
│  │  │  └────────────────────────────────────────────┘  │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │        Private Subnet 2 (10.0.2.0/24)           │ │ │
│  │  │  (Used for high availability)                   │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         S3 Bucket (Versioned)                        │  │
│  │  - Original Files → uploads/                         │  │
│  │  - Compressed Files → uploads/*.zip                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    CloudWatch Logs & Alarms                          │  │
│  │  - Function Errors                                   │  │
│  │  - Execution Duration                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **File Upload**: Client uploads a JSON processing result to `s3://bucket/uploads/file.json`
2. **S3 Event Trigger**: S3 sends notification to Lambda function
3. **Compression**: Lambda function:
   - Downloads the object from S3
   - Compresses it using ZIP format
   - Uploads the compressed file as `file.json.zip`
   - Deletes the original `file.json`
4. **Monitoring**: CloudWatch logs all operations and triggers alarms on errors

## Prerequisites

### Local Development
- macOS (or Linux/Windows with WSL2)
- AWS CLI v2 configured with credentials
- Docker installed
- Python 3.11+
- SAM CLI: `pip install aws-sam-cli`
- Git

### AWS Account Requirements
- AWS account with Free Tier eligibility
- IAM permissions for:
  - Lambda
  - S3
  - CloudFormation
  - VPC
  - CloudWatch
  - EC2 (for VPC resources)
  - IAM (for role creation)

### Installation of Prerequisites

```bash
# Install SAM CLI
pip install --upgrade aws-sam-cli

# Configure AWS credentials
aws configure

# Verify AWS CLI connection
aws sts get-caller-identity
```

## Setup & Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/me-hasan/s3-zipper-app.git
cd s3-zipper-app
```

### 2. Configure AWS Region and S3 Bucket Name

```bash
# Set your AWS region
export AWS_REGION=us-east-1

# Set your bucket name (must be globally unique)
export S3_BUCKET_NAME=s3-zipper-app-$(date +%s)
```

### 3. Build the Application

```bash
# Build the SAM application with Docker
sam build --use-container

# Optional: Validate the template
sam validate
```

### 4. Deploy to AWS

```bash
# First deployment (interactive)
sam deploy --guided \
  --parameter-overrides \
    S3BucketName=$S3_BUCKET_NAME \
    EnvironmentName=dev

# Subsequent deployments (non-interactive)
sam deploy \
  --parameter-overrides \
    S3BucketName=$S3_BUCKET_NAME \
    EnvironmentName=dev
```

### Guided Deployment Options

When running `sam deploy --guided`, you'll be prompted for:
- Stack name: `s3-zipper-app-stack`
- AWS Region: `us-east-1` (or your preferred region)
- Confirm changes before deploy: `Y`
- Allow SAM to create IAM roles: `Y`
- Allow SAM to create Lambda function URL: `N`
- Save parameters to samconfig.toml: `Y`

### 5. Verify Deployment

```bash
# List CloudFormation stacks
aws cloudformation list-stacks \
  --query 'StackSummaries[?StackStatus==`CREATE_COMPLETE`]'

# Get stack outputs
aws cloudformation describe-stacks \
  --stack-name s3-zipper-app-stack \
  --query 'Stacks[0].Outputs' \
  --output table
```

## Usage

### Uploading Files to S3

```bash
# Get the bucket name from stack outputs
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name s3-zipper-app-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
  --output text)

# Create a test JSON file
cat > test-file.json <<EOF
{
  "video_id": "12345",
  "processing_status": "completed",
  "duration": 3600,
  "resolution": "4K",
  "codec": "h264",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

# Upload to the bucket (uploads/ prefix is required)
aws s3 cp test-file.json s3://$BUCKET/uploads/test-file.json

# Check the bucket for both original and compressed file
aws s3 ls s3://$BUCKET/uploads/ --recursive
```

### Monitoring Lambda Execution

```bash
# View recent log streams
aws logs describe-log-streams \
  --log-group-name /aws/lambda/dev-s3-zipper-function \
  --order-by LastEventTime \
  --descending \
  --max-items 5

# View logs from the latest execution
LATEST_STREAM=$(aws logs describe-log-streams \
  --log-group-name /aws/lambda/dev-s3-zipper-function \
  --order-by LastEventTime \
  --descending \
  --max-items 1 \
  --query 'logStreams[0].logStreamName' \
  --output text)

aws logs get-log-events \
  --log-group-name /aws/lambda/dev-s3-zipper-function \
  --log-stream-name $LATEST_STREAM
```

### Lambda Metrics

```bash
# Get Lambda invocation metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=dev-s3-zipper-function \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum

# Get Lambda error metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=dev-s3-zipper-function \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

## Project Structure

```
s3-zipper-app/
├── README.md                    # This file
├── template.yaml               # SAM CloudFormation template
├── Dockerfile                  # Lambda container image definition
├── src/
│   ├── app.py                 # Lambda handler function
│   └── requirements.txt        # Python dependencies
├── .gitignore                 # Git ignore patterns
└── .github/
    └── workflows/             # GitHub Actions workflows (optional)
```

## Troubleshooting

### Lambda Not Triggering

```bash
# 1. Verify S3 notification configuration
aws s3api get-bucket-notification-configuration \
  --bucket $BUCKET

# 2. Check Lambda permissions
aws lambda get-policy \
  --function-name dev-s3-zipper-function

# 3. Verify event filter (uploads/ prefix required)
# File must be in: s3://bucket/uploads/filename
```

### Lambda Execution Errors

```bash
# 1. Check recent errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=dev-s3-zipper-function \
  --statistics Sum \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600

# 2. Review Lambda logs
aws logs tail /aws/lambda/dev-s3-zipper-function --follow

# 3. Test Lambda locally
sam local invoke S3ZipperFunction -e test-event.json
```

### S3 Permission Denied Errors

```bash
# Verify IAM role policy
aws iam get-role-policy \
  --role-name s3-zipper-app-stack-S3ZipperLambdaRole-XXXXX \
  --policy-name S3BucketAccess

# Check bucket policy
aws s3api get-bucket-policy --bucket $BUCKET
```

### VPC Connectivity Issues

```bash
# Verify subnet routing
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=$VPC_ID"

# Check security group rules
aws ec2 describe-security-groups \
  --group-ids $SG_ID
```

## Deployment Management

### Updating Lambda Code

```bash
# Make changes to src/app.py
# Build and deploy

sam build --use-container
sam deploy

# New version automatically created via template
```

### Rolling Back to Previous Version

```bash
# List available versions
aws lambda list-versions-by-function \
  --function-name dev-s3-zipper-function

# Update alias to previous version
aws lambda update-alias \
  --function-name dev-s3-zipper-function \
  --name live \
  --function-version 3
```

### Deleting the Stack

```bash
# Delete CloudFormation stack (also deletes all resources)
aws cloudformation delete-stack \
  --stack-name s3-zipper-app-stack

# Monitor deletion progress
aws cloudformation wait stack-delete-complete \
  --stack-name s3-zipper-app-stack

# Verify deletion
aws cloudformation describe-stacks \
  --stack-name s3-zipper-app-stack
```

## Future Improvements

### 1. Parallel Compression with AWS Batch
- Use AWS Batch for large-scale off-peak compression
- Significantly reduce Lambda costs
- Better for batch workloads

### 2. Smart Compression Selection
- Detect file type (JSON, HTML, Text)
- Skip compression for already-compressed formats (video, images)
- Use zstd or brotli for better compression ratios

### 3. Multi-Region Failover
- Replicate buckets across regions
- Failover to secondary region on primary failure
- Improve disaster recovery (RTO/RPO)

### 4. Advanced Monitoring
- Custom CloudWatch dashboards
- X-Ray tracing for detailed request flow
- Cost anomaly detection

### 5. Serverless Event Replay
- Store failed events for replay
- Implement dead-letter queue (DLQ)
- Better error handling and retry logic

### 6. Step Functions Orchestration
- Complex multi-step compression workflows
- Parallel processing with fan-out patterns
- Better visibility and error handling

### 7. Lambda Layers
- Extract common code into layers
- Reusable dependencies across functions
- Reduce cold start time

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions:
- Create an issue in the GitHub repository
- Review CloudWatch logs for error details
- Check AWS service health dashboard

## References

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [AWS CloudFormation Best Practices](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html)
