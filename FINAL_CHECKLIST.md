# Final Checklist

- [x] Raw dataset immutable, inspected, and reported
- [x] Duplicate/near-duplicate/cross-class audit, cleaning records, review sheets
- [x] User-approved derived cleaned manifest and deterministic leakage-safe split
- [x] Baseline and transfer-learning training with real outputs
- [x] Validation selection and single isolated final-test evaluation
- [x] Metrics, per-class results, confusion matrix, model comparison, latency
- [x] Versioned MobileNetV3 artifact with matching preprocessing metadata
- [x] Inference, confidence alternatives, low-confidence warning, protected Grad-CAM
- [x] Honest measured-property module; no fabricated image-to-property prediction
- [x] Sourced configurable crop knowledge base and compatibility scoring
- [x] FastAPI, authentication, authorization, upload security, logging, OpenAPI
- [x] React TypeScript client, loading/errors/results, Grad-CAM display
- [x] SQLAlchemy, PostgreSQL migration, Docker Compose, CI, .env example
- [x] Backend/frontend tests, compilation, production frontend build
- [x] README, architecture, developer, ML, API, database, deployment, testing, academic docs

## Continuing limitations

- [x] Limitations documented: mixed image contexts, limited data, generic regional guidance, no image-based numeric soil-property claims
- [ ] Docker image execution is pending local Docker installation
- [ ] Regional weather/location provider is optional and requires credentials/data
