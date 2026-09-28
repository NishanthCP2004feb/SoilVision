# ML Pipeline

Raw images are immutable. Run `python ml/src/inspection/dataset_inspector.py Orignal-Dataset`, then `python ml/src/preprocessing/clean_dataset.py`. The resulting manifest intentionally has no `USABLE` records until a reviewer makes a documented context-quality decision.

After review, mark accepted rows `status=USABLE` and `context_review=APPROVED`, then run `python ml/src/preprocessing/split_dataset.py`. It will refuse to split otherwise and assigns every related-image `group_id` to exactly one split. The approved `soil_dataset_v1_cleaned` split is 792 / 171 / 170 (train / validation / test).

Train candidates only from the derived split: `python -m ml.src.training.train --architecture mobilenet_v3_small`. Select using validation macro-F1, then run the test evaluation once: `python -m ml.src.evaluation.evaluate ml/artifacts/mobilenet_v3_small_best.pt --architecture mobilenet_v3_small`. MobileNetV3-Small was selected at validation macro-F1 0.8947; its isolated test macro-F1 is 0.8012. The predeclared HSV histogram logistic-regression baseline reached test macro-F1 0.6920.

Export a selected model with `python -m ml.src.inference.export_model ...`. Serving reads the exported `metadata.json`, image size, normalization, class order, and TorchScript weights together. Grad-CAM is an optional visual explanation only; it does not establish scientific validity.
