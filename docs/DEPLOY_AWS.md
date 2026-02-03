# AWS Deployment Notes

This is a practical outline for deploying the Streamlit frontend + FastAPI backend with MySQL on AWS.

## Recommended Architecture
- Frontend: Streamlit on ECS Fargate or App Runner
- Backend: FastAPI on ECS Fargate or App Runner
- Database: Amazon RDS for MySQL
- Networking: VPC with public subnets for app services and private subnets for RDS
- Monitoring: CloudWatch Logs + X-Ray (optional)

## High-Level Steps
1. Containerize both services with Docker.
2. Push images to ECR.
3. Create an RDS MySQL instance.
4. Deploy FastAPI service first, expose via ALB.
5. Deploy Streamlit service, pointing `API_URL` to FastAPI ALB.
6. Configure autoscaling and logs.

## Environment Variables
FastAPI:
- `DATA_CSV_PATH` (or load from MySQL)

Streamlit:
- `API_URL`

## Security
- Use security groups to allow Streamlit -> FastAPI and FastAPI -> RDS only.
- Store secrets in AWS Secrets Manager.

## Next Step If You Want Full AWS IaC
I can scaffold Terraform or AWS CDK for the full stack.
