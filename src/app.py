"""
S3 Object Compression Lambda Function

This Lambda function is triggered when a new object is added to an S3 bucket.
It compresses the object into a ZIP file and uploads it back to the same bucket,
then deletes the original object.
"""

import json
import boto3
import io
import logging
import os
from zipfile import ZipFile, ZIP_DEFLATED
from urllib.parse import unquote_plus

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3_client = boto3.client('s3')


def lambda_handler(event, context):
    """
    Lambda handler function triggered by S3 bucket events.
    
    Args:
        event: S3 event from bucket
        context: Lambda context object
    
    Returns:
        dict: Status and message of the operation
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract bucket and key from the S3 event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = unquote_plus(event['Records'][0]['s3']['object']['key'])
        
        # Skip if the object is already a ZIP file or is the compressed version
        if key.endswith('.zip'):
            logger.info(f"Skipping {key} - already a ZIP file")
            return {
                'statusCode': 200,
                'body': json.dumps('Object is already a ZIP file')
            }
        
        logger.info(f"Processing object: s3://{bucket}/{key}")
        
        # Download the object from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read()
        file_size = len(file_content)
        
        logger.info(f"Downloaded object. Size: {file_size} bytes")
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with ZipFile(zip_buffer, 'w', compression=ZIP_DEFLATED) as zip_file:
            zip_file.writestr(os.path.basename(key), file_content)
        
        zip_buffer.seek(0)
        zip_size = len(zip_buffer.getvalue())
        
        logger.info(f"Created ZIP file. Size: {zip_size} bytes. Compression ratio: {(1 - zip_size/file_size)*100:.2f}%")
        
        # Upload the ZIP file back to S3
        zip_key = f"{key}.zip"
        s3_client.put_object(
            Bucket=bucket,
            Key=zip_key,
            Body=zip_buffer.getvalue(),
            ContentType='application/zip'
        )
        
        logger.info(f"Uploaded ZIP file: s3://{bucket}/{zip_key}")
        
        # Delete the original object
        s3_client.delete_object(Bucket=bucket, Key=key)
        logger.info(f"Deleted original object: s3://{bucket}/{key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'File compressed and uploaded successfully',
                'original_file': key,
                'compressed_file': zip_key,
                'original_size': file_size,
                'compressed_size': zip_size,
                'compression_ratio': f"{(1 - zip_size/file_size)*100:.2f}%"
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing object: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
