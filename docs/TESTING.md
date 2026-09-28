# Testing

Install backend dependencies plus `pytest`, then run `pytest -q`. The suite checks grouped split isolation, recommendation transparency, unauthorized access, and unsupported upload rejection. CI additionally compiles Python and builds the TypeScript client. GPU training is intentionally excluded from normal CI.
