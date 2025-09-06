# HappyRobot Inbound Carrier Sales POC

## 🚚 Overview

Proof-of-concept for automating inbound carrier load sales using HappyRobot platform. Handles carrier calls, verifies MC numbers, matches loads, and provides analytics.

## ✨ Features

- **MC Verification**: FMCSA API integration
- **Load Matching**: Smart search and matching
- **Call Analytics**: Dashboard with metrics
- **Webhook Integration**: Three dedicated endpoints

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker 
- HappyRobot platform access

### Local Development

1. **Setup**
   ```bash
   git clone <your-repo-url>
   cd Happyrobot-inbound
   python -m venv venv
   source venv/bin/activate  
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access**
   - Dashboard: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 🛠️ Essential Commands

### Server Management
```bash
# Start server
source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Kill server
pkill -f "uvicorn app.main:app"
```

### Database Management
```bash
# Clean database
rm -f happyrobot.db
source venv/bin/activate && python3 -c "from app.database import engine, Base; Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)"

# Seed database
source venv/bin/activate && python3 seed.py
```

### Testing
```bash
# Run tests
source venv/bin/activate && python3 test_webhook.py

# Test endpoints
curl -X POST "http://localhost:8000/webhook/happyrobot/verify_mc" \
  -H "X-API-Key: super-secret-happyrobot-key" \
  -d '{"mc_number": "1515", "conversation_id": "test_001"}'
```

## 🐳 Docker Deployment

### Local Docker
```bash
docker-compose up --build
```

### Railway Deployment (Recommended)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
./deploy.sh
```

## 🔧 Webhook Endpoints

### 1. MC Verification
- **URL**: `/webhook/happyrobot/verify_mc`
- **Purpose**: Verify carrier MC number

### 2. Load Search  
- **URL**: `/webhook/happyrobot/load_search`
- **Purpose**: Search for matching loads

### 3. Summary
- **URL**: `/webhook/happyrobot/summary`
- **Purpose**: Save call summary and analytics

**Headers**: `X-API-Key: super-secret-happyrobot-key`

## 📊 Dashboard

Real-time metrics dashboard at `/` showing:
- Load management
- Call outcomes
- Success rates
- Carrier analytics

## 🧪 Testing

The `test_webhook.py` script tests all endpoints with assertions:
- MC verification (valid/invalid)
- Load search (found/not found)
- Summary saving
- Security (API key validation)

## 🔮 Future Enhancements

- Machine learning for better load matching
- Advanced sentiment analysis using NLP
- Real-time load updates
- Carrier preference learning