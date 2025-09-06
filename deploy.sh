#!/bin/bash

# HappyRobot Inbound Carrier Sales - Deployment Script
echo "🚚 HappyRobot Inbound Carrier Sales - Deployment"
echo "================================================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Login to Railway
echo "🔐 Logging into Railway..."
railway login

# Create new project
echo "🚀 Creating Railway project..."
railway init

# Set environment variables
echo "⚙️ Setting environment variables..."
railway variables set WEBHOOK_API_KEY=super-secret-happyrobot-key
railway variables set FMCSA_API_KEY=cdc33e44d693a3a58451898d4ec9df862c65b954
railway variables set DATABASE_URL=sqlite:///./happyrobot.db

# Deploy
echo "🚀 Deploying to Railway..."
railway up

# Get deployment URL
echo "🌐 Getting deployment URL..."
DEPLOY_URL=$(railway domain)

echo "✅ Deployment complete!"
echo "🌐 Your app is available at: https://$DEPLOY_URL"
echo "📊 Dashboard: https://$DEPLOY_URL"
echo "📚 API Docs: https://$DEPLOY_URL/docs"
echo "❤️ Health Check: https://$DEPLOY_URL/health"
echo ""
echo "🔧 Webhook URLs for HappyRobot:"
echo "MC Verification: https://$DEPLOY_URL/webhook/happyrobot/verify_mc"
echo "Load Search: https://$DEPLOY_URL/webhook/happyrobot/load_search"
echo "Summary: https://$DEPLOY_URL/webhook/happyrobot/summary"
echo ""
echo "🔑 API Key: super-secret-happyrobot-key"
