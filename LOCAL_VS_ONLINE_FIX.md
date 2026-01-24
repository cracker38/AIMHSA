# Fix: Local Works, Online Doesn't

## The Problem

✅ **Local**: Works because `.env` file has `OLLAMA_API_KEY`  
❌ **Online**: Doesn't work because Hugging Face Spaces **ignores `.env` files**

## Why This Happens

Hugging Face Spaces runs in a Docker container and:
- Does NOT read `.env` files from your repository
- Requires secrets to be added through their web UI
- Secrets are injected as environment variables at runtime

## The Fix (Do This Now!)

### Step 1: Open Space Settings
👉 **Click**: https://huggingface.co/spaces/CYPADILtd/aimhsa-chatbot/settings

### Step 2: Add Repository Secret
1. Click **"Repository secrets"** (left sidebar)
2. Click **"New secret"** button
3. Enter:
   - **Name**: `OLLAMA_API_KEY`
   - **Value**: `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`
4. Click **"Add secret"**

### Step 3: Restart Space
1. Still in Settings
2. Click **"Restart this Space"**
3. Wait 2-5 minutes

### Step 4: Verify
Visit: https://cypadiltd-aimhsa-chatbot.hf.space/api/config-status

Should show:
```json
{
  "ai_service": {
    "available": true,
    "api_key_set": true
  }
}
```

## Quick Test

After restarting, check the **Logs** tab. You should see:
```
OLLAMA_API_KEY: SET (length: 73)
AI Service: AVAILABLE
```

If you see:
```
OLLAMA_API_KEY: NOT SET
AI Service: UNAVAILABLE
```

Then the secret wasn't added correctly. Try again!

## Important Notes

- `.env` file is **gitignored** (won't be pushed to Spaces)
- Secrets must be added **manually** in Hugging Face UI
- Each Space has its own secrets (not shared)
- Secrets are **encrypted** and secure

---

**Your local setup is correct. You just need to replicate it in Hugging Face Spaces settings!**

