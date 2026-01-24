# Hugging Face Spaces Configuration Guide

## Required Environment Variables

Add these in **Hugging Face Spaces Settings → Repository secrets**:

### Critical (Required for AI to work):
```
OLLAMA_API_KEY=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
```

### Optional (for full functionality):
```
HDEV_SMS_API_ID=your_sms_api_id
HDEV_SMS_API_KEY=your_sms_api_key
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## How to Add Secrets

1. Go to: https://huggingface.co/spaces/CYPADILtd/aimhsa-chatbot/settings
2. Click **"Repository secrets"** in the left sidebar
3. Click **"New secret"**
4. Add each variable:
   - **Name**: `OLLAMA_API_KEY`
   - **Value**: `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`
5. Click **"Add secret"**
6. **Restart the Space** (Settings → Restart this Space)

## Verify Configuration

After restarting, check the Logs tab. You should see:
- ✅ `OLLAMA_API_KEY: SET`
- ✅ `AI Service: AVAILABLE`

If you see warnings, the AI service will use fallback responses.

## Current Status

Your Space is deployed but needs the `OLLAMA_API_KEY` secret to enable AI responses.

