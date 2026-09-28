# Academic Project Documentation

## Abstract

SoilWise is an image-classification and decision-support system that combines a soil-image classifier with explicitly sourced soil measurements and configurable crop compatibility profiles. It avoids treating RGB imagery as a laboratory instrument.

## Introduction, problem, and objectives

Farmers and students need accessible decision support, but image-only soil claims are easily overstated. The objective is a reproducible seven-class classifier, secure web application, transparent recommendations, and a path for future multimodal data.

## Requirements and proposed system

The client is React/TypeScript; FastAPI serves a PostgreSQL-backed REST API; PyTorch provides classification; derived manifests protect raw data; and crop scoring reveals matched and limiting factors. Functional requirements include secure upload, authentication, history, measured-property sources, recommendations, and model metadata. Non-functional requirements include reproducibility, validation, logging, privacy, and explainability.

## Dataset, cleaning, and leakage prevention

The supplied `Orignal-Dataset` has 1,189 valid RGB images across Alluvial, Arid, Black, Laterite, Mountain, Red, and Yellow classes. It has no paired property labels. The inspection found imbalance, duplicate risk, and mixed contexts. `clean_dataset.py` writes reasons rather than deleting images; human review is required. Grouped splitting preserves duplicate/near-duplicate groups and keeps the final test split isolated.

## ML methodology and evaluation

The planned candidates are MobileNetV3, EfficientNet-B0, and ResNet-50 with controlled augmentation, weighted loss/sampling, early stopping, scheduler, validation macro-F1 selection, and per-class final evaluation. CPU constraints made EfficientNet-B0 impractical, so the cached pretrained MobileNetV3-Small was trained for 10 epochs. It achieved validation macro-F1 0.8947. On the isolated 170-image test partition it achieved accuracy 0.8471, macro-F1 0.8012, weighted-F1 0.8478, and top-3 accuracy 0.9765. The HSV-histogram logistic-regression baseline achieved test macro-F1 0.6920. Confusion-matrix and per-class files are stored in `ml/reports/model_evaluation/`.

## Backend, database, frontend, and security

The API implements JWT-like HMAC signed access tokens, password hashing with scrypt, owner checks, decoded image validation, safe generated filenames, size/type limits, structured response envelopes, and CORS configuration. PostgreSQL entities are Users, SoilAnalyses, SoilProperties, CropRecommendations, and ModelVersions. The frontend uses actual API calls and presents loading/error states.

## Crop recommendation methodology

Profiles are versioned JSON data with source URLs. Scoring evaluates only supplied factors: detected type, selected season, and verified measurements whose profile ranges exist. The current profiles use generic soil/season guidance from ICAR and contain no invented numeric nutrient or moisture ranges. Regional validation and professional advice remain necessary.

## Diagrams

The editable architecture diagram is in `docs/architecture.md`. The user workflow is: Register/Login -> Upload -> validation -> approved model inference -> optional sourced measurements -> compatibility scoring -> saved private history.

## Limitations

1. The current dataset supports seven folder-defined image classes only.
2. It cannot scientifically support image-based pH, NPK, moisture, organic-carbon, EC, weather, or location prediction.
3. Context-heavy images and limited dataset size may harm generalization.
4. Approval of image context was user-authorized rather than independently annotated by an agronomist; mixed capture contexts may still limit generalization.
5. Generic crop profiles do not replace regional agronomic guidance or soil testing.

## Future scope and conclusion

Future work can add paired lab/sensor observations, regional weather/location providers, multilingual UI, ONNX export, and a reviewed larger dataset. The present system prioritizes traceability and scientific validity over fabricated results.
