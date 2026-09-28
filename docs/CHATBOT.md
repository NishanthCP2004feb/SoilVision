# Chatbot Architecture

## Overview
AI agricultural assistant using NVIDIA NIM API.

## Architecture
- Request Flow: React → FastAPI `/chat` endpoint → NVIDIA NIM API (`meta/llama-3.1-8b-instruct`)

## Supported Languages
- English
- Kannada (ಕನ್ನಡ)
- Tamil (தமிழ்)
- Telugu (తెలుగు)
- Hindi (हिन्दी)
- Malayalam (മലയാളം)

## API Key Security
- Stored and accessed server-side only via `NVIDIA_API_KEY` environment variable.
- Never exposed to the browser.

## Analysis Context Awareness
- Passes context to the LLM: soil type, confidence, property ranges, and recommendations.

## System Prompt Rules
- Never invent lab results
- Acknowledge uncertainty
- Keep technical terms intact

## Conversation History
- Maintains the last 10 messages for context.

## Suggested Prompts
- 6 predefined questions available for quick interaction.

## Error Handling
- Graceful fallback when the API key is not configured.

## Language Handling
- Technical values (pH, NPK, dS/m) remain in their original form across all supported languages.
