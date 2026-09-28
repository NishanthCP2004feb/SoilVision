# SoilWise — AI-Based Soil Detection, Property Analysis and Intelligent Crop Recommendation System

## What it does
Upload soil image → classify → property reference ranges → crop recommendations → multilingual AI chatbot

## Key features
- 7-class soil classifier
- Literature-based property ranges
- 15 crop profiles
- 6-language chatbot
- Grad-CAM explainability
- Secure auth

## Tech stack
- Frontend: React + TypeScript
- Backend: FastAPI
- Machine Learning: PyTorch (MobileNetV3-Small)
- Database: SQLite/PostgreSQL
- Chatbot: NVIDIA NIM

## Quick start
### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Dataset stats and model metrics
- Dataset: 1,189 RGB images across 7 classes
- Accuracy: 84.71%
- Macro-F1: 80.12%

## Scientific limitations notice
This system uses RGB images for soil type classification. Soil properties provided are reference ranges from literature based on the classified soil type, NOT predicted values. For accurate soil property measurements, laboratory testing is required. See [LIMITATIONS.md](docs/LIMITATIONS.md) and [SOIL_PROPERTY_MODEL.md](docs/SOIL_PROPERTY_MODEL.md) for details.

## Documentation Links
- [Project Audit](docs/PROJECT_AUDIT.md)
- [API Documentation](docs/API.md)
- [Chatbot Architecture](docs/CHATBOT.md)
- [Soil Property Model](docs/SOIL_PROPERTY_MODEL.md)
- [Limitations](docs/LIMITATIONS.md)
