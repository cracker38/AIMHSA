# ⚠️ CRITICAL: Add Environment Variable

## Your chatbot is running but AI is NOT working!

The fallback message you're seeing means `OLLAMA_API_KEY` is **NOT SET** in Hugging Face Spaces.

## 🔧 FIX IT NOW (5 minutes):

### Step 1: Open Space Settings
👉 **Click here**: https://huggingface.co/spaces/CYPADILtd/aimhsa-chatbot/settings

### Step 2: Add Repository Secret
1. In the left sidebar, click **"Repository secrets"**
2. Click the **"New secret"** button
3. Fill in:
   - **Name**: `OLLAMA_API_KEY`
   - **Value**: `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`
4. Click **"Add secret"**

### Step 3: Restart Space
1. Still in Settings, scroll down
2. Click **"Restart this Space"** button
3. **WAIT 2-5 minutes** for rebuild

### Step 4: Verify
1. Check **Logs** tab - should show:
   ```
   OLLAMA_API_KEY: SET
   AI Service: AVAILABLE
   ```

2. Or visit: https://cypadiltd-aimhsa-chatbot.hf.space/api/config-status
   - Should show: `"available": true`

3. Try chatting - you should get REAL AI responses!

## ❌ Current Status:
- ✅ Code: Deployed
- ✅ Space: Running  
- ✅ Frontend: Working
- ❌ **AI Service: NOT CONFIGURED** ← YOU NEED TO FIX THIS

## ✅ After Fix:
- ✅ AI Service: Will be AVAILABLE
- ✅ Chatbot: Will give real AI responses
- ✅ Everything: Will work perfectly!

---

**The Space cannot access your API key unless you add it in Settings → Repository secrets!**

