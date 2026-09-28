# SoilWise Project Audit

## Current Architecture
- Frontend: React + TypeScript
- Backend: FastAPI (Python)
- Machine Learning: PyTorch (MobileNetV3-Small)
- Database: SQLite (Development), PostgreSQL (Production)

## Current Frontend
- Comprehensive single-page application (SPA) with React Router
- 6 primary views: Landing, Auth, Analyze, History, About
- Floating AI chatbot with multilingual support
- Professional redesign complete with an earth-tone color palette

## Current Backend
- FastAPI framework
- Endpoints for authentication, image upload, analysis, history, recommendations, and chat

## Current ML Models
- Model: MobileNetV3-Small classifier
- Classes: 7 soil types (Alluvial, Arid, Black, Laterite, Mountain, Red, Yellow)
- Accuracy: 84.71%
- Macro-F1: 80.12%

## Current Dataset
- 1,189 RGB images in 7 classes

## Current Database
- Development: SQLite
- Production: PostgreSQL
- Entities: users, soil_analyses, soil_properties, crop_recommendations, model_versions

## Current API Endpoints
- POST /api/v1/auth/register - Create user
- POST /api/v1/auth/login - Issue token
- POST /api/v1/auth/logout - Logout
- GET /api/v1/auth/me - Current user
- POST /api/v1/soil/analyze - Image classification + property ranges
- GET /api/v1/soil/analyses - Owner-scoped history
- GET /api/v1/soil/analyses/{id} - Analysis detail
- GET /api/v1/soil/analyses/{id}/explanation - Grad-CAM image
- POST /api/v1/soil/analyses/{id}/properties - Save measured property
- POST /api/v1/soil/properties - Alias for property save
- GET /api/v1/crops - List crop profiles
- GET /api/v1/crops/{name} - Crop profile detail
- POST /api/v1/recommendations - Crop compatibility scoring
- POST /api/v1/chat - AI chatbot message
- GET /api/v1/chat/languages - Supported chatbot languages
- GET /api/v1/models - Model metadata
- GET /api/v1/health - Service status

## Current Authentication
- Hashing: scrypt password hashing
- Tokens: HMAC-signed tokens

## Current Chatbot
- Integration: NVIDIA NIM integration
- Languages (6): English, Kannada, Tamil, Telugu, Hindi, Malayalam

## Current UI Status
- Status: Professional redesign complete with earth-tone palette

## Known Limitations
- No paired image-property data
- Property ranges are literature references only

## Missing Features
- Docker not tested locally
- Weather/location integration (optional feature)
