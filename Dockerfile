# Use AWS Python 3.11 Lambda base image
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements
COPY src/requirements.txt ${LAMBDA_TASK_ROOT}/

# Install dependencies
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy Lambda function code
COPY src/app.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD [ "app.lambda_handler" ]
