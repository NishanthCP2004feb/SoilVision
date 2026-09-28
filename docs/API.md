# API Documentation

All endpoints are under `/api/v1`.
Response format: `{success, data, message, error}`

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | /auth/register | No | Create user |
| POST | /auth/login | No | Issue token |
| POST | /auth/logout | Yes | Logout |
| GET | /auth/me | Yes | Current user |
| POST | /soil/analyze | Yes | Image classification + property ranges |
| GET | /soil/analyses | Yes | Owner-scoped history |
| GET | /soil/analyses/{id} | Yes | Analysis detail |
| GET | /soil/analyses/{id}/explanation | Yes | Grad-CAM image |
| POST | /soil/analyses/{id}/properties | Yes | Save measured property |
| POST | /soil/properties | Yes | Alias for property save |
| GET | /crops | No | List crop profiles |
| GET | /crops/{name} | No | Crop profile detail |
| POST | /recommendations | Yes | Crop compatibility scoring |
| POST | /chat | Yes | AI chatbot message |
| GET | /chat/languages | No | Supported chatbot languages |
| GET | /models | No | Model metadata |
| GET | /health | No | Service status |
