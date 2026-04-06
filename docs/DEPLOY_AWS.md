# AWS Deployment Notes

This repo now ships with Dockerfiles and a production Compose stack, so AWS deployment is straightforward.

## Recommended AWS architecture
- EC2 instance or ECS service for the compose stack
- Route 53 for DNS
- Optional RDS MySQL if you want to move off CSV data

## Simple path
1. Launch an Ubuntu EC2 instance
2. Install Docker and Docker Compose
3. Clone the repo
4. Copy `.env.production.example` to `.env.production`
5. Set `DOMAIN`, admin credentials, and `DATA_SOURCE`
6. Point your Route 53 record to the instance IP
7. Run `docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build`

## ECS path
1. Build and push the frontend and backend images to ECR
2. Run the services on ECS Fargate
3. Put an ALB in front
4. Terminate TLS at the ALB
5. Set `API_URL` for the frontend task to the backend service DNS name
6. If using RDS, set `DATA_SOURCE=mysql` and provide `MYSQL_URL`

## Security
- Restrict inbound traffic to `80/443`
- Store secrets in Secrets Manager or SSM Parameter Store
- Use a stronger `ADMIN_PASSWORD` and keep `SEED_DEMO_DATA=false`
