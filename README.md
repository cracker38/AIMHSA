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

## Requirements

- Python 3.9+
- Ollama (for local AI inference)
- SQLite database

## License

MIT License
