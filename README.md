---
title: AIMHSA
emoji: 🧠
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# AIMHSA - AI Mental Health Support Assistant

AI-powered mental health support platform for Rwanda with automated counseling booking and SMS notifications.

## Features

- 🤖 AI-powered mental health chatbot
- 📅 Automated therapy session booking
- 📱 SMS notifications via HDEV SMS Gateway
- 👨‍⚕️ Professional dashboard for counselors
- 📊 Admin dashboard for management
- 🌍 Multilingual support (English, French, Kinyarwanda, Kiswahili)

## Setup

1. Clone this repository
2. Create a `.env` file with your configuration:
```env
HDEV_SMS_API_ID=your_api_id
HDEV_SMS_API_KEY=your_api_key
```

3. Run locally:
```bash
python run_aimhsa.py
```

## Hugging Face Spaces

### Run Docker image locally
```bash
docker run -it -p 7860:7860 --platform=linux/amd64 \
  registry.hf.space/cypadiltd-aimhsa-chatbot:latest
```

### Get container logs (SSE)
```bash
curl -N \
  -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/spaces/CYPADILtd/aimhsa-chatbot/logs/run"
```

### Get build logs (SSE)
```bash
curl -N \
  -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/spaces/CYPADILtd/aimhsa-chatbot/logs/build"
```

> Set `HF_TOKEN` to your Hugging Face token before running the curl commands.

## Requirements

- Python 3.9+
- Ollama (for local AI inference)
- SQLite database

## License

MIT License
