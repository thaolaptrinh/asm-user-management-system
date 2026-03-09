# Backend

FastAPI backend with layered architecture (Routes → Services → Repositories → DB).

## Quick Start

```bash
make dev              # Start all services with Docker
make shell-be         # Open shell in backend container
```

**API Documentation:** http://localhost:8000/api/v1/docs

---

## Architecture

```
Routes (HTTP) → Services (Business Logic) → Repositories (Data) → DB
```

**Benefits:** Testability, reusability, maintainability.

---

## Structure

```
app/
├── api/v1/routes/      # Endpoints (auth, users, items)
├── services/           # Business logic
├── repositories/       # Data access (CRUD)
├── models/             # SQLAlchemy ORM
├── schemas/            # Pydantic validation
├── core/               # Config, security, exceptions
└── db/                 # Session, seed
```

---

## Adding a Feature

**1. Model** → `app/models/feature.py`

```python
class Feature(UUIDMixin, TimestampMixin, Base):
    name: Mapped[str] = mapped_column(String(255))
```

**2. Repository** → `app/repositories/feature.py`

```python
class FeatureRepository(BaseRepository[Feature]):
    # Inherits CRUD: get_by_id, get_all, create, update, delete
    pass
```

**3. Service** → `app/services/feature.py`

```python
class FeatureService:
    async def create(self, data: FeatureCreate):
        return await self._repo.create(**data.model_dump())
```

**4. Schema** → `app/schemas/feature.py`

```python
class FeatureCreate(BaseModel):
    name: str
```

**5. Route** → `app/api/v1/routes/feature.py`

```python
@router.post("/", response_model=FeaturePublic)
async def create(
    data: FeatureCreate,
    service: FeatureServiceDep,  # Auto-injected
):
    return await service.create(data)
```

**6. Register** → `app/api/v1/router.py`

```python
from app.api.v1.routes import feature
api_router.include_router(feature.router)
```

**7. Migrate** → From repo root

```bash
make migrate-make m="create_feature_table"
make migrate
```

---

## Tests

```bash
make test-be            # Backend tests with coverage
```

Tests run in Docker container with dedicated test database.

---

## Migrations

```bash
make migrate               # Run pending
make migrate-rollback      # Rollback last
make migrate-status        # Show version
make migrate-make m="add_field"   # Generate from model
```

**Seed data:** `make seed`

---

## Environment

Required in `.env` (generate with `make secrets`):

```bash
APP_KEY=
JWT_SECRET_KEY=
DB_PASSWORD=
DB_ROOT_PASSWORD=
FIRST_SUPERUSER_PASSWORD=
```

---

## Container Commands

```bash
make shell-be         # Backend shell
make shell-db         # Database shell
make logs-be          # Backend logs
make logs-be -f       # Follow logs
```

**Inside container:**

```bash
python -m app.main    # Run server
pytest tests/ -v      # Run tests
python --version     # Check version
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **DB issues** | `make db-reset` |
| **Container not starting** | `make ps` → check status |
| **Tests fail** | `make test-be` |
| **Migration issues** | `make migrate-status` |
| **Import errors** | `make dev-build` |
| **Everything stuck** | `make down && make dev` |
