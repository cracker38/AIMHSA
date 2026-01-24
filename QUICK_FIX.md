# Quick Fix Guide - Hugging Face Spaces

## The Problem
Your chatbot is showing fallback messages because the `OLLAMA_API_KEY` environment variable is not set.

## The Solution (3 Steps)

### Step 1: Add the Secret
1. Open: https://huggingface.co/spaces/CYPADILtd/aimhsa-chatbot/settings
2. Click **"Repository secrets"** (left sidebar)
3. Click **"New secret"**
4. Enter:
   - **Name**: `OLLAMA_API_KEY`
   - **Value**: `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`
5. Click **"Add secret"**

### Step 2: Restart the Space
1. Still in Settings
2. Scroll down and click **"Restart this Space"**
3. Wait 2-5 minutes for rebuild

### Step 3: Verify It Works
1. Check the **Logs** tab - you should see:
   - `OLLAMA_API_KEY: SET`
   - `AI Service: AVAILABLE`

2. Or visit this URL to check status:
   - https://cypadiltd-aimhsa-chatbot.hf.space/api/config-status
   - Should show: `"ai_service": { "available": true }`

3. Try chatting - you should get real AI responses!

## Still Not Working?

Check the diagnostic endpoint:
- https://cypadiltd-aimhsa-chatbot.hf.space/api/config-status

This will show you exactly what's configured and what's missing.

