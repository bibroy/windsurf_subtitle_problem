# Running Instructions

This document provides detailed instructions for setting up, running, and deploying the Subtitle Enhancement System.

## Prerequisites

1. Python 3.8 or higher
2. AWS Account with access to:
   - Amazon Transcribe
   - Amazon Translate
   - Amazon Rekognition
3. FFmpeg installed on your system

## Local Development Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd subtitle-enhancement-system
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure AWS credentials:
   ```bash
   aws configure
   # Or set environment variables:
   export AWS_ACCESS_KEY_ID="your-access-key"
   export AWS_SECRET_ACCESS_KEY="your-secret-key"
   export AWS_DEFAULT_REGION="your-region"
   ```

## Running the Application

### CLI Interface

1. Process an existing subtitle file:
   ```bash
   python -m src.cli.main process-subtitle input.vtt -o output.vtt
   ```

2. Process subtitle with video analysis:
   ```bash
   python -m src.cli.main process-subtitle input.vtt -v video.mp4 -o output.vtt
   ```

3. Generate subtitles from video:
   ```bash
   python -m src.cli.main generate-subtitle video.mp4 -o subtitles.vtt
   ```

### Web Interface

1. Start the web server:
   ```bash
   python -m src.web.app
   ```

2. Access the web interface at http://localhost:8000

## Running Tests

1. Run all tests:
   ```bash
   pytest
   ```

2. Run specific test file:
   ```bash
   pytest tests/test_subtitle_processor.py
   ```

3. Run with coverage:
   ```bash
   pytest --cov=src tests/
   ```

## AWS Deployment

### Lambda Function Deployment

1. Package the application:
   ```bash
   pip install --target ./package -r requirements.txt
   cd package
   zip -r ../lambda.zip .
   cd ..
   zip -g lambda.zip src/*
   ```

2. Deploy to AWS Lambda:
   ```bash
   aws lambda create-function \
     --function-name subtitle-processor \
     --runtime python3.8 \
     --handler src.lambda_handler.handler \
     --memory-size 256 \
     --timeout 300 \
     --role arn:aws:iam::your-account-id:role/lambda-role \
     --zip-file fileb://lambda.zip
   ```

### Container Deployment

1. Build Docker image:
   ```bash
   docker build -t subtitle-processor .
   ```

2. Run container locally:
   ```bash
   docker run -p 8000:8000 subtitle-processor
   ```

3. Push to Amazon ECR:
   ```bash
   aws ecr create-repository --repository-name subtitle-processor
   docker tag subtitle-processor:latest your-account.dkr.ecr.region.amazonaws.com/subtitle-processor
   aws ecr get-login-password | docker login --username AWS --password-stdin your-account.dkr.ecr.region.amazonaws.com
   docker push your-account.dkr.ecr.region.amazonaws.com/subtitle-processor
   ```

## Monitoring and Logging

1. View application logs:
   ```bash
   tail -f logs/app.log
   ```

2. Monitor AWS CloudWatch metrics:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Lambda \
     --metric-name Duration \
     --dimensions Name=FunctionName,Value=subtitle-processor \
     --start-time 2023-01-01T00:00:00 \
     --end-time 2023-01-02T00:00:00 \
     --period 3600 \
     --statistics Average
   ```

## Troubleshooting

1. Check AWS credentials:
   ```bash
   aws sts get-caller-identity
   ```

2. Verify FFmpeg installation:
   ```bash
   ffmpeg -version
   ```

3. Test AWS services access:
   ```bash
   aws transcribe list-transcription-jobs
   aws translate list-terminologies
   aws rekognition list-collections
   ```

For additional support or bug reports, please create an issue in the repository.
