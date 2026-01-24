# Hugging Face Spaces Deployment Troubleshooting

## Current Issue: Domain Not Resolving

If you're seeing `ERR_NAME_NOT_RESOLVED` errors, the Space might still be building or needs configuration.

## Steps to Fix

### 1. Check Space Status
- Go to: https://huggingface.co/spaces/CYPADILtd/aimhsa-chatbot
- Check the "Logs" tab to see build status
- Wait for the build to complete (can take 5-10 minutes)

### 2. Set Environment Variables (CRITICAL)

Go to Space Settings → Repository secrets and add:

**Required:**
- `OLLAMA_API_KEY`: `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`

**Optional:**
- `HDEV_SMS_API_ID`: Your SMS API ID
- `HDEV_SMS_API_KEY`: Your SMS API Key
- `SMTP_USERNAME`: Email username
- `SMTP_PASSWORD`: Email password

### 3. Verify Build Success

Check the Logs tab for:
- ✅ "Build successful"
- ✅ "Application running on port 7860"
- ❌ Any error messages

### 4. Restart the Space

After setting environment variables:
- Go to Settings → Restart this Space
- Wait for rebuild (2-5 minutes)

### 5. Access Your Space

Once built, your Space will be available at:
- **URL**: https://cypadiltd-aimhsa-chatbot.hf.space
- **Alternative**: https://huggingface.co/spaces/CYPADILtd/aimhsa-chatbot

## Common Issues

### Build Fails
- Check Dockerfile syntax
- Verify requirements-cloud.txt is correct
- Check logs for specific errors

### Domain Not Resolving
- Space is still building (wait 5-10 minutes)
- Build failed (check logs)
- Environment variables missing (add OLLAMA_API_KEY)

### Application Errors After Build
- Check application logs in the Logs tab
- Verify environment variables are set correctly
- Ensure database can be initialized

## Quick Check Commands

If you have access to the Space terminal:
```bash
# Check if app is running
ps aux | grep python

# Check environment variables
env | grep OLLAMA

# Check logs
tail -f /tmp/app.log
```

