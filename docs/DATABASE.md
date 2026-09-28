# Database

PostgreSQL is the deployment database. The normalized schema contains `users`, `soil_analyses`, `soil_properties`, `crop_recommendations`, and `model_versions`. Analysis history is always filtered by authenticated user ID.

For development, SQLite is allowed only when `DATABASE_URL` is omitted. For PostgreSQL, copy `.env.example`, set `DATABASE_URL`, and run `alembic -c backend/alembic.ini upgrade head`. The initial migration is `0001_initial_schema`; reverse with `alembic -c backend/alembic.ini downgrade -1`.
