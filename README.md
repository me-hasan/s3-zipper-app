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
git clone https://github.com/your-username/s3-zipper-app.git
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

## Cost Analysis

### Scenario: 1,000,000 files per hour, 10 MB average file size

#### Monthly Volume
- **Files per hour**: 1,000,000
- **Files per day**: 24,000,000
- **Files per month**: 720,000,000
- **Total data per month**: 7,200 TB (7.2 PB)

#### Cost Breakdown

#### 1. **S3 Storage Costs**

Given the high volume, we need to consider:
- Both original and compressed files are stored (until original is deleted)
- Compression ratio typically 10-30% for JSON (average ~20%)

```
Average compressed size = 10 MB × 0.20 = 2 MB
Total storage per month = (720M files × 2 MB) = 1,440 TB = 1.44 PB

Storage costs (Standard):
- Price: $0.023 per GB
- Monthly cost = 1,440 TB × 1,024 GB/TB × $0.023
- Monthly cost = $33,947.52

With Intelligent-Tiering to move old files:
- Frequent Tier (first 30 days): $0.0125/GB
- Infrequent Tier (after 30 days): $0.0135/GB
- Archive Tier (after 90 days): $0.004/GB
- Estimated savings: 40-50%
- Adjusted cost ≈ $16,974 - $20,368
```

#### 2. **Lambda Invocation Costs**

```
Invocations: 720,000,000 per month
Price: $0.20 per 1,000,000 invocations

Monthly cost = (720,000,000 / 1,000,000) × $0.20
Monthly cost = 720 × $0.20 = $144.00
```

#### 3. **Lambda Compute Costs (Duration)**

```
Assumptions:
- Average execution time: 8 seconds
- Memory allocation: 1024 MB
- Price: $0.0000166667 per GB-second

Total GB-seconds per month = 720,000,000 invocations × 8 seconds × (1024 MB / 1024)
                            = 5,760,000,000 GB-seconds

Monthly cost = 5,760,000,000 × $0.0000166667
Monthly cost = $96,000.00
```

#### 4. **NAT Gateway Costs (VPC Egress)**

```
Lambda in private subnets requires NAT Gateway for S3 API calls:
- Processing 720M files with ~2 requests each (GET, PUT) = 1.44B requests
- Estimated data transfer out: ~14.4 TB
- Price: $0.45 per GB

NAT Gateway processing: $0.045 per hour × 730 hours = $32.85
Data transfer egress: 14,400 GB × $0.45 = $6,480.00
Total NAT cost ≈ $6,512.85
```

#### 5. **CloudWatch Costs**

```
Logs ingested:
- Average log size per invocation: 2 KB
- Total: 720M × 2 KB = 1,440 TB = 1.44 PB
- Price: $0.50 per GB ingested

Monthly cost = 1,440 TB × 1,024 × $0.50
Monthly cost = $737,280.00

Note: This is extremely high. Recommendation: Use log sampling or filters.
With filtering (log only errors/warnings): ~$10,000-$30,000
```

#### 6. **CloudFormation Costs**
- Free tier: No charges for template processing

#### **Total Estimated Monthly Cost**

| Component | Cost |
|-----------|------|
| S3 Storage (with tiering) | $16,974 - $20,368 |
| Lambda Invocations | $144 |
| Lambda Compute | $96,000 |
| NAT Gateway | $6,513 |
| CloudWatch Logs (filtered) | $10,000 - $30,000 |
| **TOTAL** | **$129,631 - $152,025** |

### Without VPC (Direct S3 access):
- Eliminates NAT Gateway costs: **Save $6,513/month**
- **Revised Total: $123,118 - $145,512**

### Cost Optimization Recommendations

#### 1. **Move to S3 Intelligent-Tiering** ⭐ (Save $16,000+/month)
```
AWS S3 Intelligent-Tiering automatically moves objects between access tiers
Estimated 40-50% savings on storage
```

#### 2. **Use S3 Batch Operations** ⭐ (Save $30,000+/month)
```
Instead of compressing on upload, use S3 Batch Operations to compress
files in bulk during off-peak hours. Reduces Lambda compute costs significantly.
```

#### 3. **Remove VPC Requirement** ⭐ (Save $6,513/month)
```
If not required by compliance, use public S3 API endpoints
Eliminates NAT Gateway costs
Trade-off: Reduced network isolation
```

#### 4. **Implement Log Sampling** ⭐ (Save $20,000+/month)
```
Log only 1-5% of successful invocations
Maintain detailed logs only for errors
Reduce log volume by 95%
```

#### 5. **Use Lambda Concurrency Reservations** (Save 3-5%)
```
Purchase Reserved Concurrency for predictable workload
Estimated savings: $3,000-$5,000/month
```

#### 6. **Compress at Source** (Save 100% Lambda costs)
```
Compress files before uploading to S3
Eliminates need for Lambda processing
Trade-off: Requires client-side changes
Potential savings: $96,144/month
```

#### 7. **Batch Multiple Files into Single Zip** (Save 30-40%)
```
Instead of compressing individual files, batch process
Reduces Lambda invocations and durations
Estimated savings: $35,000-$45,000/month
```

#### 8. **Use Lambda@Edge for Cost Optimization** (Marginal improvement)
```
Process logs closer to compute region
Limited impact on overall costs (~5% savings)
```

### **Realistic Production Estimate with Optimizations**

With recommendations #1, #2, #3, and #4 implemented:

```
S3 Storage (Intelligent-Tiering): $10,000
Lambda Invocations: $0 (eliminated via batch operations)
Lambda Compute: $0 (moved to batch processing)
CloudWatch (sampled): $5,000
NAT Gateway: $0 (removed VPC requirement)
Total: ~$15,000/month (87% savings from baseline)
```

## Scalability & Performance

### Current Capacity Analysis

#### Throughput Assessment

**Current Limits:**
- Lambda concurrent execution limit: 1,000 (default)
- At 1M files/hour = 277 files/second
- Average execution time: 8 seconds
- Concurrent executions needed: 277 × 8 = 2,216 concurrent

**Issue:** Default limit (1,000) insufficient for this workload.

**Solution:** Request concurrent execution increase to 3,000

```bash
# Request quota increase
aws service-quotas request-service-quota-increase \
  --service-code lambda \
  --quota-code L-B99A9384 \
  --desired-value 3000
```

#### Storage Assessment

**Monthly ingest:** 7.2 PB
- S3 can handle this easily (unlimited scale)
- Versioning enabled (best practice for rollback)
- Cross-region replication recommended for disaster recovery

**Performance concern:** Bucket request rate
- 1M files/hour = 277 requests/second
- S3 supports 3,500 PUT/COPY/POST/DELETE and 5,500 GET/HEAD requests per second **per partition**
- Current workload fits within limits
- Future growth may require partitioning strategy

### Bottleneck Analysis

#### 1. **Lambda Concurrency** ⚠️ CRITICAL

```
Current Bottleneck: Default concurrent limit (1,000) vs. needed (2,216)

Impact:
- Lambda will queue excess invocations
- S3 event notifications may timeout after 6 hours
- Files stuck in "processing" state
- Service degradation during peak hours

Solution:
- Increase concurrency limit to 3,000-5,000
- Monitor duration metric to reduce average execution time
- Implement queue with SQS for better control
- Use Lambda provisioned concurrency for predictable baseline
```

#### 2. **S3 Request Rate** ⚠️ MODERATE

```
Current Bottleneck: Approaching S3 partition limits

Impact:
- Throttling (HTTP 503 errors) if single partition
- Degraded performance during peak uploads

Mitigation:
- S3 automatically scales to handle the load (tested up to 100,000 requests/sec)
- Use random prefix in key names to distribute across partitions
- Implement exponential backoff in Lambda
- Monitor throttling metrics
```

#### 3. **NAT Gateway Throughput** ⚠️ MODERATE

```
Current Bottleneck: Single NAT Gateway (5Gbps limit per AZ)

Impact:
- Estimated bandwidth: 7.2 PB / month = 27.7 Gbps average
- Single NAT Gateway bottleneck during peak hours
- Increased latency

Solution:
- Deploy multiple NAT Gateways across subnets
- Route traffic to multiple NAT Gateways
- Consider VPC Endpoint for S3 (direct private connectivity)
- Eliminates NAT Gateway entirely for S3 traffic
```

#### 4. **Network Bandwidth** ⚠️ CRITICAL FOR PRIVATE SUBNETS

```
Current Bottleneck: VPC Endpoint and NAT Gateway capacity

Impact:
- 7.2 PB monthly = 27.7 Gbps average bandwidth
- NAT Gateway limited to 5 Gbps per AZ
- Packet loss and increased latency during peak

Recommended Solution:
- Use AWS PrivateLink with S3 VPC Endpoint (gateway type)
- Provides direct, private connectivity to S3
- No bandwidth limits for VPC Endpoints
- Cost: Free for S3 (but $0.01 per GB for other services)
- Eliminates NAT Gateway entirely

Alternative:
- Deploy to public subnets (eliminates network isolation)
- Reduces latency and cost
```

#### 5. **Lambda Timeout Duration** ⚠️ MODERATE

```
Current Configuration: 300 second timeout

Impact:
- Large files (100MB+) may timeout
- Retry logic would re-invoke and re-charge
- Potential infinite retry loops

Optimization:
- Current 1024 MB memory is adequate for 10 MB files
- For larger files, increase memory to 3008 MB (max)
- Reduces execution time by 3x due to faster CPU
- May increase cost but reduces timeouts
```

#### 6. **CloudWatch Logs Ingestion** ⚠️ MODERATE

```
Current Bottleneck: Log volume (1.44 PB/month)

Impact:
- High CloudWatch API calls
- Increased latency in log retrieval
- Very high cost ($737k/month)

Solution Options:
1. Log sampling (80-90% reduction)
2. Log filtering (errors only)
3. Use third-party logging (Datadog, New Relic)
4. Structured logging with efficient parsing
```

### Recommended Architecture for Scale

```yaml
Optimization Steps:

1. First Phase (Quick Wins):
   - Request Lambda concurrency increase
   - Implement S3 VPC Endpoint (eliminate NAT)
   - Add log sampling/filtering
   - Estimated cost reduction: 50%

2. Second Phase (Medium-term):
   - Implement SQS queue for reliability
   - Use Lambda Provisioned Concurrency (10% of peak)
   - Add Lambda Layer for shared dependencies
   - Enable Lambda Insights for better monitoring

3. Third Phase (Long-term):
   - Migrate to Step Functions for complex workflows
   - Implement batch compression (reduce invocations)
   - Use S3 Select for selective processing
   - Consider AWS Glue for large-scale data transformations
```

### Performance Metrics

```
Metric Target Values:

Lambda Duration: < 10 seconds (currently 8s) ✓
Lambda Memory Utilization: 50-70% (adjust as needed)
Lambda Error Rate: < 0.1%
S3 Request Success Rate: > 99.95%
End-to-end latency: < 30 seconds
Cost per GB processed: < $0.02 (with optimizations)
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
