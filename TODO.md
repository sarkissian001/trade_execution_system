# To-Do List

## High Priority
- [x] Set Up Project (MVP)
- [x] Create SQLAlchemy models with ORM to create schemas
- [x] Setup Conftest fixture to use in memory db for automated tests
- [ ] Implement loguru logging 
- [ ] Set up OAuth 2.0 with OpenID Connect for authentication.
- [ ] Configure user model and rbac
- [ ] Implement TLS encryption for secure communication.
- [ ] Set up PostgreSQL with `asyncpg` for asynchronous database access.
- [ ] Add migration support using `Alembic`.
- [ ] Set up GitHub Actions/GitLab CI for CI/CD pipeline.

## Medium Priority
- [x] Add Poetry linting and formatting checks using `black`
- [x] Dockerise the application
- [ ] Create Kubernetes manifests for deployment, services, and ingress.
- [ ] Set up a PostgreSQL instance in Kubernetes (or use a managed service like AWS RDS).
- [ ] Configure secrets management for sensitive data (e.g., API keys, database credentials).
- [ ] Set up monitoring and logging (e.g., Prometheus, Grafana, ELK stack).

## Low Priority

- [ ] Add reporting and analytics endpoints:
  - `GET /reports/trades` - Generate a report of all trades.
  - `GET /reports/profit-loss` - Calculate profit/loss for a user or period.
- [ ] Add admin endpoints:
  - `GET /admin/users` - List all users (admin-only).
  - `PUT /admin/users/{user_id}` - Update user roles (admin-only).
  - `DELETE /admin/users/{user_id}` - Delete a user (admin-only).
- [ ] Organise workspace and project structure.
