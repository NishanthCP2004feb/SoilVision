# Final Project Status — SoilWise

## 1. Current Architecture

```
React + TypeScript (Vite) → FastAPI → PyTorch (MobileNetV3-Small) → SQLite/PostgreSQL
                         → NVIDIA NIM API (chatbot)
                         → ICAR/NBSS&LUP reference data (property ranges)
```

## 2. Existing Problems Found

- Single monolithic `App.tsx` (25 lines of JSX) — no components, no router
- Season hardcoded to "Kharif" — no user selection
- No chatbot, no multilingual support
- No soil property information returned to the user
- No logout endpoint
- No `.env` file for local development
- No NVIDIA API integration
- Crop profiles covered only 6 crops with no nutrient requirements
- Grad-CAM failure silently ignored
- Basic functional CSS, not professional

## 3. Problems Fixed

- ✅ Frontend completely redesigned with React Router, 6 views, professional design system
- ✅ Season selector (Kharif/Rabi/Zaid) — no longer hardcoded
- ✅ Logout endpoint added
- ✅ `.env` file created for local development
- ✅ NVIDIA API key configuration added
- ✅ Chatbot implemented with 6-language support
- ✅ Soil property reference ranges returned with analysis
- ✅ Crop profiles expanded to 15 crops with documented requirements
- ✅ Professional CSS design system with earth-tone palette
- ✅ Floating chatbot UI with language selector and suggested questions
- ✅ Analysis context passed to chatbot for intelligent responses
- ✅ Confidence meters and property visualizations in result dashboard

## 4. Dataset Statistics

| Metric | Value |
|---|---|
| Total valid images | 1,189 |
| Classes | 7 (Alluvial, Arid, Black, Laterite, Mountain, Red, Yellow) |
| Class range | 52 (Alluvial) to 284 (Arid) |
| Formats | 1,187 JPEG + 2 WEBP |
| All RGB | Yes |
| Exact duplicate pairs | 50 |
| Near-duplicate pairs | 47 |
| Cross-class candidates | 4 |
| Cleaned split | 792 train / 171 val / 170 test |
| Paired property labels | **NONE** |

## 5. Soil Classification Model

| Metric | Value |
|---|---|
| Architecture | MobileNetV3-Small (pretrained, fine-tuned) |
| Version | soil_classifier_v1.0 |
| Input | 224×224 RGB, ImageNet normalization |
| Training | WeightedRandomSampler, weighted CrossEntropy, AdamW, ReduceLROnPlateau |
| Selection criterion | Validation macro-F1 |
| Validation macro-F1 | 0.8947 |
| Test accuracy | 84.71% |
| Test macro-F1 | 80.12% |
| Test weighted-F1 | 84.78% |
| Top-3 accuracy | 97.65% |
| Baseline (HSV logistic regression) | 72.35% accuracy, 69.20% macro-F1 |
| Inference latency | ~24ms CPU |
| Explainability | Grad-CAM |

### Per-Class Test Results

| Class | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| Alluvial Soil | 0.429 | 0.429 | 0.429 | 7 |
| Arid Soil | 0.919 | 0.810 | 0.861 | 42 |
| Black Soil | 0.969 | 0.886 | 0.925 | 35 |
| Laterite Soil | 0.788 | 0.813 | 0.800 | 32 |
| Mountain Soil | 0.813 | 0.929 | 0.867 | 28 |
| Red Soil | 0.882 | 0.938 | 0.909 | 16 |
| Yellow Soil | 0.750 | 0.900 | 0.818 | 10 |

## 6. Soil-Property Models

**Status: NOT AVAILABLE as direct predictions.**

The current dataset contains NO paired image→property labels. Direct RGB image-based prediction of pH, N, P, K, moisture, organic carbon, or EC is not scientifically supported.

### What Is Provided Instead

Literature-based reference ranges from ICAR (Indian Council of Agricultural Research), NBSS&LUP (National Bureau of Soil Survey), and state agriculture university publications. These are clearly labeled as `REFERENCE_RANGE` and are never presented as predictions.

## 7. Properties Actually Supported (as Reference Ranges)

| Property | Status | Source |
|---|---|---|
| pH | REFERENCE_RANGE | ICAR - Soils of India |
| Nitrogen (N) | REFERENCE_RANGE | ICAR Soil Fertility Maps |
| Phosphorus (P) | REFERENCE_RANGE | ICAR Soil Fertility Maps |
| Potassium (K) | REFERENCE_RANGE | ICAR Soil Fertility Maps |
| Moisture | REFERENCE_RANGE | NBSS&LUP Soil Survey |
| Organic Carbon | REFERENCE_RANGE | ICAR Soil Health Card norms |
| Electrical Conductivity | REFERENCE_RANGE | NBSS&LUP Soil Survey |

## 8. Properties Not Supported (as Predictions)

All seven properties above are NOT predicted from the uploaded image. They are typical ranges for the detected soil type from published literature.

## 9. Actual Model Metrics

All metrics are from `ml/reports/model_evaluation/metrics.json` and were computed on the isolated 170-image test partition that was never seen during training or model selection.

## 10. Crop Recommendation System

- 15 crop profiles with documented requirements
- Scoring based on: soil type compatibility + season + measured property ranges
- Sources: ICAR publications, state agriculture university recommendations
- Returns: compatibility score, matched factors, limiting factors, warnings
- Covers both Kharif and Rabi seasons
- Crops: Rice, Wheat, Maize, Groundnut, Millet, Cotton, Soybean, Sugarcane, Potato, Tea, Coffee, Barley, Mustard, Chickpea, Turmeric

## 11. Chatbot Implementation

- **Implemented**: Yes
- **API**: NVIDIA NIM (meta/llama-3.1-8b-instruct)
- **Architecture**: React → FastAPI /chat → NVIDIA NIM API (API key server-side only)
- **Context-aware**: Passes soil type, confidence, property ranges, recommendations to LLM
- **Error handling**: Graceful fallback when API key not configured
- **Security**: API key never exposed to browser

## 12. Six Supported Languages

| Code | Language | Script |
|---|---|---|
| en | English | Latin |
| kn | Kannada | ಕನ್ನಡ |
| ta | Tamil | தமிழ் |
| te | Telugu | తెలుగు |
| hi | Hindi | हिन्दी |
| ml | Malayalam | മലയാളം |

Technical values (pH, NPK, dS/m) remain in their original form across all languages.

## 13. UI Improvements

- Professional design system with Inter font and earth-tone palette
- React Router for URL-based navigation (bookmarkable pages)
- Landing page with features, how-it-works, and CTA
- Auth page with login/register toggle
- Analysis page with upload, season selector, results dashboard
- Confidence meters and property range visualizations
- Crop recommendation cards with compatibility scores
- History page with analysis list
- Floating chatbot with language selector and suggested prompts
- Responsive design for desktop, tablet, and mobile
- Scientific limitation notices throughout
- Loading states and error handling

## 14. Authentication Status

- ✅ Registration (email + password, 12+ chars)
- ✅ Login (scrypt password verification, HMAC-signed token)
- ✅ Logout (token cleared client-side + backend endpoint)
- ✅ Session persistence (localStorage)
- ✅ Protected routes (redirect to /auth if not authenticated)
- ✅ Owner-scoped history

## 15. API Status

All endpoints under `/api/v1`:

| Method | Endpoint | Status |
|---|---|---|
| POST | /auth/register | ✅ Working |
| POST | /auth/login | ✅ Working |
| POST | /auth/logout | ✅ Implemented |
| GET | /auth/me | ✅ Working |
| POST | /soil/analyze | ✅ Working (returns property_ranges) |
| GET | /soil/analyses | ✅ Working |
| GET | /soil/analyses/{id} | ✅ Working |
| GET | /soil/analyses/{id}/explanation | ✅ Working |
| POST | /soil/analyses/{id}/properties | ✅ Working |
| GET | /crops | ✅ Working (15 profiles) |
| POST | /recommendations | ✅ Working |
| POST | /chat | ✅ Implemented |
| GET | /chat/languages | ✅ Implemented |
| GET | /models | ✅ Working |
| GET | /health | ✅ Working |

## 16. Database Status

- SQLite for development (auto-created)
- PostgreSQL for production (Alembic migrations)
- Entities: users, soil_analyses, soil_properties, crop_recommendations, model_versions

## 17. Testing Status

| Test Suite | Tests | Status |
|---|---|---|
| Backend pytest | 5 | ✅ All pass |
| Frontend vitest | 2 | ✅ All pass |
| Python compilation | All | ✅ Clean |
| Frontend TypeScript build | All | ✅ Clean |

## 18. Security Status

- ✅ scrypt password hashing
- ✅ HMAC-signed access tokens
- ✅ CORS configured for development origins
- ✅ Image decode validation (JPEG/PNG/WEBP only)
- ✅ File size limits
- ✅ Safe generated filenames
- ✅ Owner-scoped data access
- ✅ NVIDIA API key server-side only
- ✅ No secrets in git (.env in .gitignore)
- ✅ Structured error responses (no stack traces to client)

## 19. Remaining Limitations

1. Alluvial class severely underrepresented (52 images, F1=0.429)
2. No paired image→property data — cannot predict pH/NPK from images
3. Property ranges are broad literature references, not sample-specific
4. Crop recommendations are generic ICAR-sourced, not regional prescriptions
5. RGB images cannot replace laboratory soil testing
6. Chatbot requires NVIDIA API key to function
7. Docker images authored but not tested locally
8. Weather/location integration is a protocol boundary only
9. LLM chatbot may occasionally produce inaccurate agricultural advice

## 20. Exact Commands to Run the Project

### Backend
```powershell
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```
Backend runs at: http://127.0.0.1:8000
API docs at: http://127.0.0.1:8000/api/v1/docs

### Frontend
```powershell
npm install --prefix frontend
npm run dev --prefix frontend
```
Frontend runs at: http://127.0.0.1:5173

### Tests
```powershell
python -m pytest -q
npm test --prefix frontend
npm run build --prefix frontend
```

### Environment Setup
```powershell
# Copy and edit .env (or use the created one):
# Set NVIDIA_API_KEY for chatbot functionality
# Leave DATABASE_URL empty for SQLite development
```

### Docker (if Docker is installed)
```powershell
Copy-Item .env.example .env
docker compose -f infra/docker-compose.yml up --build
```
