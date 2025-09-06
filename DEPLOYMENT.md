# Deployment Guide - HappyRobot Inbound Carrier Sales

## 🚀 Quick Deployment Options

### 1. Railway (Recommended for POC)

Railway is perfect for quick deployment and testing:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

**Environment Variables in Railway Dashboard:**
```env
WEBHOOK_API_KEY=your-secret-api-key-here
DATABASE_URL=postgresql://username:password@host:port/database
```

### 2. Fly.io

Great for global distribution:

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch app
fly launch

# Deploy
fly deploy
```

### 3. Render

Simple deployment with free tier:

1. Connect your GitHub repository
2. Choose "Web Service"
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables

## 🔧 Production Deployment

### AWS ECS Deployment

1. **Create ECR Repository:**
```bash
aws ecr create-repository --repository-name happyrobot-inbound
```

2. **Build and Push Image:**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
docker build -t happyrobot-inbound .
docker tag happyrobot-inbound:latest your-account.dkr.ecr.us-east-1.amazonaws.com/happyrobot-inbound:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/happyrobot-inbound:latest
```

3. **Create ECS Task Definition:**
```json
{
  "family": "happyrobot-inbound",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "happyrobot-inbound",
      "image": "your-account.dkr.ecr.us-east-1.amazonaws.com/happyrobot-inbound:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "WEBHOOK_API_KEY",
          "value": "your-secret-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/happyrobot-inbound",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Run

1. **Build and Push:**
```bash
gcloud builds submit --tag gcr.io/your-project/happyrobot-inbound
```

2. **Deploy:**
```bash
gcloud run deploy happyrobot-inbound \
  --image gcr.io/your-project/happyrobot-inbound \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars WEBHOOK_API_KEY=your-secret-api-key
```

### Azure Container Instances

1. **Build and Push to ACR:**
```bash
az acr build --registry yourregistry --image happyrobot-inbound .
```

2. **Deploy:**
```bash
az container create \
  --resource-group your-rg \
  --name happyrobot-inbound \
  --image yourregistry.azurecr.io/happyrobot-inbound:latest \
  --ports 8000 \
  --environment-variables WEBHOOK_API_KEY=your-secret-api-key
```

## 🔐 SSL/HTTPS Setup

### Let's Encrypt with Nginx

1. **Install Certbot:**
```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

2. **Get Certificate:**
```bash
sudo certbot --nginx -d yourdomain.com
```

3. **Auto-renewal:**
```bash
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Cloudflare SSL

1. Add your domain to Cloudflare
2. Set DNS A record to your server IP
3. Enable "Always Use HTTPS" in SSL/TLS settings
4. Set SSL mode to "Full (strict)"

## 📊 Monitoring & Logging

### Application Logs

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Health Checks

The application includes built-in health checks:

```bash
curl https://yourdomain.com/health
```

### Metrics Collection

Use the dashboard endpoints for monitoring:

- `/dashboard/metrics` - Overall system health
- `/dashboard/conversations` - Recent activity
- `/dashboard/sentiment-trends` - Performance trends

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker build -t happyrobot-inbound .
      
      - name: Deploy to Railway
        run: |
          echo ${{ secrets.RAILWAY_TOKEN }} | railway login
          railway up
```

### GitLab CI Example

```yaml
stages:
  - build
  - deploy

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t happyrobot-inbound .
    - docker push registry.gitlab.com/your-group/happyrobot-inbound:latest

deploy:
  stage: deploy
  script:
    - fly deploy
```

## 🚨 Troubleshooting

### Common Issues

1. **Webhook Not Receiving Calls:**
   - Check API key in HappyRobot configuration
   - Verify webhook URL is accessible
   - Check server logs for errors

2. **Database Connection Issues:**
   - Verify DATABASE_URL environment variable
   - Check database server accessibility
   - Ensure proper permissions

3. **Load Matching Not Working:**
   - Check if loads exist in database
   - Verify load data format
   - Check load service logic

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload --log-level debug
```

### Performance Tuning

1. **Database Optimization:**
   - Add indexes on frequently queried fields
   - Use connection pooling
   - Implement query caching

2. **API Optimization:**
   - Enable response compression
   - Implement request rate limiting
   - Add response caching headers

## 📈 Scaling Considerations

### Horizontal Scaling

- Use load balancer for multiple instances
- Implement session sharing or stateless design
- Use external database (PostgreSQL/MySQL)

### Vertical Scaling

- Increase container resources
- Optimize database queries
- Implement caching layers

### Auto-scaling

- Set up auto-scaling groups in cloud platforms
- Monitor CPU/memory usage
- Set appropriate scaling thresholds
