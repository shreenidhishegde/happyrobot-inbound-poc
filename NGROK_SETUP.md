# 🚀 Quick ngrok Setup for HappyRobot Webhook

## **Step 1: Install ngrok**
```bash
# Mac (with Homebrew)
brew install ngrok

# Or download from https://ngrok.com/download
```

## **Step 2: Start Your Local Server**
```bash
# In one terminal
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## **Step 3: Get Your ngrok URL**
```bash
# In another terminal
ngrok http 8000
```

You'll see output like:
```
Forwarding    https://abc123.ngrok.io -> http://localhost:8000
```

## **Step 4: Use This URL in HappyRobot**

- **Webhook URL**: `https://abc123.ngrok.io/webhook/happyrobot`
- **Header**: `X-API-Key: your-secret-api-key`

## **Step 5: Test Your Webhook**

Run the helper script:
```bash
python get_ngrok_url.py
```

## **🎯 Your Deploy URL is Ready!**

**Right now, you can use:**
- **Webhook URL**: `https://[your-ngrok-id].ngrok.io/webhook/happyrobot`
- **API Key**: Set in your `.env` file

## **⚠️ Important Notes**

1. **ngrok URLs change** each time you restart ngrok (unless you have a paid account)
2. **For production**, deploy to a real cloud service (Railway, Fly.io, etc.)
3. **ngrok is perfect** for development and POC demonstrations

## **🔧 Quick Test**

Test your webhook immediately:
```bash
curl -X POST "https://[your-ngrok-id].ngrok.io/webhook/happyrobot" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key" \
  -d '{
    "conversation_id": "test_001",
    "carrier_mc": "MC123456",
    "carrier_response": "",
    "event": "conversation_start"
  }'
```

## **🚀 Next Steps**

1. **Copy your ngrok URL** to HappyRobot webhook configuration
2. **Test the conversation flow** with the test script
3. **Demonstrate to Carlos** using your ngrok URL
4. **Deploy to production** when ready for real use

**Your deploy URL is ready right now! 🎉**
