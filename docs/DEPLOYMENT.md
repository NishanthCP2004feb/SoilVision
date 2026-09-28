# Deployment

Copy `.env.example` to `.env`, replace `SECRET_KEY` and the PostgreSQL password, and run:

```powershell
docker compose -f infra/docker-compose.yml up --build
```

The API is exposed at port 8000 and the frontend at port 8080. Before enabling image analysis, mount a real exported model in `ml/artifacts/soil_classifier_v1.0/`; metadata and preprocessing must match the deployed weights.
