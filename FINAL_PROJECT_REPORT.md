# Final Project Report

## What was built

SoilWise is a working React/FastAPI agricultural AI application with secure authentication, image upload validation, persistent private analysis history, sourced measurements, configurable crop compatibility scoring, model information, protected Grad-CAM visualization, Docker/Alembic/CI configuration, and automated tests.

## Dataset and split

The immutable `Orignal-Dataset` contains 1,189 valid images in seven classes. The audit found 50 exact duplicate pairs, 47 near duplicate pairs, four cross-class candidates, imbalance, and mixed capture contexts. Duplicates and cross-class candidates were excluded from the derived set. Following explicit user approval of the pending review records, `soil_dataset_v1_cleaned` contains 1,133 images: 792 train, 171 validation, and 170 isolated test. Every related-image group occurs in one split only.

## Final model and real results

`soil_classifier_v1.0` is a pretrained MobileNetV3-Small fine-tuned with weighted sampling/loss, controlled training-only augmentation, scheduler, checkpointing, early stopping criteria, and deterministic seed. It was chosen on validation macro-F1 (0.8947), not test accuracy.

| Model | Validation macro-F1 | Test accuracy | Test macro-F1 | Test weighted-F1 | Top-3 |
| --- | ---: | ---: | ---: | ---: | ---: |
| HSV histogram logistic-regression baseline | 0.6519 | 0.7235 | 0.6920 | N/A | N/A |
| MobileNetV3-Small | 0.8947 | 0.8471 | 0.8012 | 0.8478 | 0.9765 |

The mean warm CPU inference time across 10 runs was 24.02 ms. Evaluation evidence is in `ml/reports/model_evaluation/metrics.json`, `per_class_metrics.csv`, `confusion_matrix.csv`, `confusion_matrix.png`, and `inference_latency.json`.

## API, database, and security

The `/api/v1` API offers registration/login, secure JPEG/PNG/WEBP decode validation, analysis, private history/detail, protected explanation rendering, sourced properties, configurable crops/recommendations, model metadata, and health. PostgreSQL entities and the Alembic initial migration cover users, analyses, properties, recommendations, and model versions. Passwords use scrypt; tokens use signed HMAC payloads; upload storage uses generated filenames and does not trust client paths.

## Validation and run commands

`python -m pytest -q` passed 4 tests, `npm test --prefix frontend` passed 1 test, Python compilation passed, and `npm run build --prefix frontend` passed. The local backend and frontend are running at `http://127.0.0.1:8000` and `http://127.0.0.1:5173`. Docker images are authored but Docker is not installed in this environment.

```powershell
Copy-Item .env.example .env
docker compose -f infra/docker-compose.yml up --build
```

## Limitations and future work

The model classifies the supplied folder labels; its mixed source contexts and small classes (especially Alluvial) limit generalization. It cannot infer pH, NPK, moisture, organic carbon, or EC from images. Crop guidance is generic until verified measurements and regional data are supplied. Predictions and Grad-CAM are decision-support aids, not laboratory or agronomic proof.
