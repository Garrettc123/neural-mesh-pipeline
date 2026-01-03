# Deployment Guide

This guide covers multiple deployment options for the Neural Mesh Pipeline.

## Table of Contents

1. [Quick Deployment (Local)](#quick-deployment-local)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Termux Deployment (Android)](#termux-deployment-android)
5. [CI/CD Integration](#cicd-integration)
6. [Health Checks](#health-checks)
7. [Troubleshooting](#troubleshooting)

## Quick Deployment (Local)

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- OpenAI API key

### Automated Deployment

```bash
# Clone the repository
git clone https://github.com/Garrettc123/neural-mesh-pipeline.git
cd neural-mesh-pipeline

# Run deployment script
./deploy.sh
```

### Manual Deployment

```bash
# 1. Create directory structure
mkdir -p ~/neural-mesh/{src/tests,logs,storage}

# 2. Copy files
cp pipeline_enhanced.py ~/neural-mesh/
cp requirements-termux.txt ~/neural-mesh/
cp .env.example ~/neural-mesh/.env

# 3. Install dependencies
cd ~/neural-mesh
pip install -r requirements-termux.txt

# 4. Configure environment
nano .env  # Add your OPENAI_API_KEY

# 5. Run the pipeline
python pipeline_enhanced.py
```

## Docker Deployment

### Prerequisites

- Docker 20.10 or higher
- docker-compose 1.29 or higher

### Quick Start with Docker

```bash
# 1. Clone repository
git clone https://github.com/Garrettc123/neural-mesh-pipeline.git
cd neural-mesh-pipeline

# 2. Configure environment
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY

# 3. Deploy with Docker
./deploy-docker.sh
```

### Manual Docker Deployment

```bash
# Build image
docker build -t neural-mesh-pipeline .

# Run container
docker run -d \
  --name neural-mesh-pipeline \
  -e OPENAI_API_KEY="your-key-here" \
  -v $(pwd)/data/storage:/app/storage \
  -v $(pwd)/data/logs:/app/logs \
  -v $(pwd)/src:/app/src \
  neural-mesh-pipeline
```

### Using docker-compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart
docker-compose restart
```

## Cloud Deployment

### AWS EC2

```bash
# 1. Launch EC2 instance (Amazon Linux 2 or Ubuntu)
# 2. SSH into instance
ssh -i your-key.pem ec2-user@your-instance-ip

# 3. Install dependencies
sudo yum update -y
sudo yum install python3 python3-pip git -y

# 4. Clone and deploy
git clone https://github.com/Garrettc123/neural-mesh-pipeline.git
cd neural-mesh-pipeline
./deploy.sh

# 5. Set up as service (optional)
sudo cp neural-mesh-pipeline.service /etc/systemd/system/
sudo systemctl enable neural-mesh-pipeline
sudo systemctl start neural-mesh-pipeline
```

### Google Cloud Platform

```bash
# Using Cloud Run
gcloud run deploy neural-mesh-pipeline \
  --image gcr.io/PROJECT_ID/neural-mesh-pipeline \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY="your-key"
```

### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name neural-mesh-pipeline \
  --image neural-mesh-pipeline:latest \
  --dns-name-label neural-mesh \
  --ports 80 \
  --environment-variables OPENAI_API_KEY="your-key"
```

### Heroku

```bash
# 1. Create Heroku app
heroku create neural-mesh-pipeline

# 2. Set environment variables
heroku config:set OPENAI_API_KEY="your-key"

# 3. Deploy
git push heroku main
```

## Termux Deployment (Android)

### Installation

```bash
# 1. Install Termux from F-Droid (recommended) or Play Store

# 2. Update packages
pkg update && pkg upgrade -y

# 3. Install required packages
pkg install python python-pip git -y

# 4. Set up storage access
termux-setup-storage

# 5. Clone and deploy
cd ~
git clone https://github.com/Garrettc123/neural-mesh-pipeline.git
cd neural-mesh-pipeline
./deploy.sh
```

### Running in Background

```bash
# Using termux-services
pkg install termux-services
sv-enable neural-mesh-pipeline

# Or using nohup
nohup python ~/neural-mesh/pipeline_enhanced.py > /dev/null 2>&1 &
```

### Keep Alive

To prevent Android from killing the process:

1. Install Termux:Boot
2. Create startup script:

```bash
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/neural-mesh.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/neural-mesh
python pipeline_enhanced.py --mode continuous
EOF
chmod +x ~/.termux/boot/neural-mesh.sh
```

## CI/CD Integration

### GitHub Actions

The repository includes a `.github/workflows/deploy.yml` file that:

- Runs tests on push/PR
- Builds Docker image
- Deploys documentation

To enable:

1. Add `OPENAI_API_KEY` to GitHub Secrets
2. Push to main branch
3. Check Actions tab for deployment status

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements-termux.txt
    - python -m py_compile pipeline_enhanced.py

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t neural-mesh-pipeline .
    - docker push $CI_REGISTRY_IMAGE:latest

deploy:
  stage: deploy
  script:
    - ./deploy.sh
  only:
    - main
```

### Jenkins

```groovy
pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/Garrettc123/neural-mesh-pipeline.git'
            }
        }
        
        stage('Test') {
            steps {
                sh 'python -m py_compile pipeline_enhanced.py'
            }
        }
        
        stage('Deploy') {
            steps {
                sh './deploy.sh'
            }
        }
    }
}
```

## Health Checks

### Manual Health Check

```bash
python health_check.py
```

### Automated Monitoring

```bash
# Add to crontab for regular checks
crontab -e

# Add this line (check every 5 minutes)
*/5 * * * * cd ~/neural-mesh && python health_check.py >> logs/health.log 2>&1
```

### Docker Health Check

The Docker container includes built-in health checks:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' neural-mesh-pipeline

# View health check logs
docker inspect neural-mesh-pipeline | jq '.[0].State.Health'
```

## Configuration Options

### Environment Variables

All deployments support these environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for AI repair |
| `AI_MODEL` | No | `gpt-4` | OpenAI model to use |
| `AI_TEMPERATURE` | No | `0.1` | Model temperature |
| `MAX_RETRIES` | No | `3` | Maximum retry attempts |
| `TEST_TIMEOUT` | No | `300` | Test timeout in seconds |
| `MAX_REPAIR_ATTEMPTS` | No | `2` | Max AI repair attempts |

### Volume Mounts (Docker)

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./data/storage` | `/app/storage` | Persistent state |
| `./data/logs` | `/app/logs` | Log files |
| `./src` | `/app/src` | Source code |

## Troubleshooting

### Common Issues

**Issue: "Module not found" error**
```bash
pip install -r requirements-termux.txt
```

**Issue: "Permission denied" on scripts**
```bash
chmod +x deploy.sh deploy-docker.sh health_check.py
```

**Issue: API key not recognized**
```bash
export OPENAI_API_KEY="sk-your-key"
# Or add to .env file
```

**Issue: Docker container won't start**
```bash
# Check logs
docker logs neural-mesh-pipeline

# Ensure .env file exists
cp .env.example .env
nano .env
```

**Issue: Port already in use**
```bash
# Find and kill process using the port
lsof -ti:8080 | xargs kill -9
```

### Getting Help

1. Check logs: `tail -f ~/neural-mesh/logs/*.log`
2. Run health check: `python health_check.py`
3. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
4. Open GitHub issue with logs and error messages

## Security Best Practices

1. **Never commit API keys** - Use environment variables
2. **Restrict file permissions**: `chmod 600 .env`
3. **Use HTTPS** for external connections
4. **Regular updates**: `pip install --upgrade -r requirements-termux.txt`
5. **Monitor logs** for suspicious activity
6. **Rotate API keys** periodically

## Updating

### Local Installation

```bash
cd ~/neural-mesh-pipeline
git pull
./deploy.sh
```

### Docker

```bash
cd neural-mesh-pipeline
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

## Backup and Recovery

### Backup

```bash
# Backup state and logs
tar -czf neural-mesh-backup-$(date +%Y%m%d).tar.gz \
  ~/neural-mesh/storage \
  ~/neural-mesh/logs \
  ~/neural-mesh/src

# Move to safe location
mv neural-mesh-backup-*.tar.gz ~/backups/
```

### Recovery

```bash
# Extract backup
tar -xzf neural-mesh-backup-YYYYMMDD.tar.gz -C ~/neural-mesh/
```

## Monitoring and Alerts

### Setup Email Alerts

Add to `.env`:
```bash
EMAIL_ALERTS=true
EMAIL_TO=admin@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Setup Slack Notifications

Add to `.env`:
```bash
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Performance Tuning

### For Limited Resources

```bash
# Use lighter model
export AI_MODEL=gpt-3.5-turbo

# Reduce retries
export MAX_RETRIES=2

# Shorter timeouts
export TEST_TIMEOUT=60
```

### For High Performance

```bash
# Use latest model
export AI_MODEL=gpt-4

# More retries for reliability
export MAX_RETRIES=5

# Longer timeouts
export TEST_TIMEOUT=600
```

## Support

- Documentation: [README.md](README.md)
- Quick Reference: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- Implementation Guide: [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
- GitHub Issues: https://github.com/Garrettc123/neural-mesh-pipeline/issues
