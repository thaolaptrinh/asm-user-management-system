# FastAPI Project - Backend

## Requirements

* [Docker](https://www.docker.com/).
* [uv](https://docs.astral.sh/uv/) for Python package and environment management.

## Docker Compose

Start the local development environment with Docker Compose following the guide in [../docs/implementation/development.md](../docs/implementation/development.md).

## General Workflow

By default, the dependencies are managed with [uv](https://docs.astral.sh/uv/), go there and install it.

From `./backend/` you can install all the dependencies with:

```console
$ uv sync
```

Then you can activate the virtual environment with:

```console
$ source .venv/bin/activate
```

Make sure your editor is using the correct Python virtual environment, with the interpreter at `backend/.venv/bin/python`.

Modify or add SQLModel models for data and SQL tables in `./backend/app/models.py`, API endpoints in `./backend/app/api/`, CRUD (Create, Read, Update, Delete) utils in `./backend/app/crud.py`.

## VS Code

There are already configurations in place to run the backend through the VS Code debugger, so that you can use breakpoints, pause and explore variables, etc.

The setup is also already configured so you can run the tests through the VS Code Python tests tab.

## Docker Compose Override

During development, you can change Docker Compose settings that will only affect the local development environment in the file `compose.override.yml`.

The changes to that file only affect the local development environment, not the production environment. So, you can add "temporary" changes that help the development workflow.

For example, the directory with the backend code is synchronized in the Docker container, copying the code you change live to the directory inside the container. That allows you to test your changes right away, without having to build the Docker image again. It should only be done during development, for production, you should build the Docker image with a recent version of the backend code. But during development, it allows you to iterate very fast.

There is also a command override that runs `fastapi run --reload` instead of the default `fastapi run`. It starts a single server process (instead of multiple, as would be for production) and reloads the process whenever the code changes. Have in mind that if you have a syntax error and save the Python file, it will break and exit, and the container will stop. After that, you can restart the container by fixing the error and running again:

```console
$ docker compose watch
```

There is also a commented out `command` override, you can uncomment it and comment the default one. It makes the backend container run a process that does "nothing", but keeps the container alive. That allows you to get inside your running container and execute commands inside, for example a Python interpreter to test installed dependencies, or start the development server that reloads when it detects changes.

To get inside the container with a `bash` session you can start the stack with:

```console
$ docker compose watch
```

and then in another terminal, `exec` inside the running container:

```console
$ docker compose exec backend bash
```

You should see an output like:

```console
root@7f2607af31c3:/app#
```

that means that you are in a `bash` session inside your container, as a `root` user, under the `/app` directory, this directory has another directory called "app" inside, that's where your code lives inside the container: `/app/app`.

There you can use the `fastapi run --reload` command to run the debug live reloading server.

```console
$ fastapi run --reload app/main.py
```

...it will look like:

```console
root@7f2607af31c3:/app# fastapi run --reload app/main.py
```

and then hit enter. That runs the live reloading server that auto reloads when it detects code changes.

Nevertheless, if it doesn't detect a change but a syntax error, it will just stop with an error. But as the container is still alive and you are in a Bash session, you can quickly restart it after fixing the error, running the same command ("up arrow" and "Enter").

...this previous detail is what makes it useful to have the container alive doing nothing and then, in a Bash session, make it run the live reload server.

## Backend tests

To test the backend run:

```console
$ bash ./scripts/test.sh
```

The tests run with Pytest, modify and add tests to `./backend/tests/`.

If you use GitHub Actions the tests will run automatically.

### Test database (MySQL only)

All tests use **MySQL** with a dedicated test database. Name = **MYSQL_DATABASE from .env + `_test`** (e.g. `app_test`). Each test run **drops and recreates** that DB (clean slate) via bash scripts.

- **Run tests (with coverage):** from repo root: `make test` runs backend **with coverage report** then frontend unit tests with coverage. Backend only: `./scripts/run-backend-tests.sh cov`.
- **Run tests (no coverage):** `./scripts/run-backend-tests.sh` (pytest only).
- **Coverage, fail if < 100%:** `make test-cov-100`.
- **Reset test DB only (no tests):** `./scripts/reset-test-db.sh`.

### Running tests (recommended)

From **repo root**, with stack up (`docker compose up -d`):

```bash
./scripts/run-backend-tests.sh    # reset test DB + pytest
./scripts/run-backend-tests.sh -v # verbose
./scripts/run-backend-tests.sh -x # stop on first failure
```

Or `make test` (backend with coverage + frontend unit tests with coverage; frontend fails if coverage is below threshold).

Run pytest manually inside the container (after resetting the test DB and setting env):

```bash
./scripts/reset-test-db.sh
docker compose exec -e MYSQL_DATABASE=app_test backend pytest tests/ -v
```

### Test Coverage

When the tests are run, a file `htmlcov/index.html` is generated, you can open it in your browser to see the coverage of the tests.

## Migrations

Migrations use **Alembic** with default naming: `{revision_id}_{slug}.py` (e.g. `001_create_user_table.py`). Execution order follows `down_revision`. Prefer one migration per table (or per logical change).

**From repo root (with Docker):**

| Command | Description |
|--------|-------------|
| `make migrate` | Run all pending migrations |
| `make migrate-rollback` | Rollback last migration |
| `make migrate-fresh` | Drop all tables and re-run all migrations |
| `make migrate-status` | Show current revision |
| `make migration create_posts_table` | Generate a new migration from model changes (autogenerate) |

**Creating a new migration:** After changing `app/models.py`, run:

```bash
make migration add_status_to_users_table
```

Then review the generated file in `migrations/versions/`, edit if needed, and run `make migrate`.

Alembic is configured to import SQLModel models from `app/models.py`. Commit new files under `migrations/versions/` to git.

**Best practice:** Do not delete or change the contents of a migration that has already been applied to any database. If you must do so (e.g. squashing migrations on dev only), after removing or editing an applied migration run **once** from the repo root: `make db-reset` (removes DB volume and re-runs prestart) or `make migrate-fresh` (refresh = reset + migrate: stamp head, step-by-step downgrade to base, then upgrade head). Prestart only runs `alembic upgrade head`; it does not fix the version table on failure.

**If you don't want to use migrations at all,** uncomment the lines in the file at `./backend/app/core/db.py` that end in:

```python
SQLModel.metadata.create_all(engine)
```

and comment the line in the file `scripts/prestart.sh` that contains:

```console
$ alembic upgrade head
```

If you don't want to start with the default models and want to remove them / modify them, from the beginning, without having any previous revision, you can remove the revision files (`.py` Python files) under `./backend/migrations/versions/`. And then create a first migration as described above.

## Email Templates

The email templates are in `./backend/app/email-templates/`. Here, there are two directories: `build` and `src`. The `src` directory contains the source files that are used to build the final email templates. The `build` directory contains the final email templates that are used by the application.

Before continuing, ensure you have the [MJML extension](https://github.com/mjmlio/vscode-mjml) installed in your VS Code.

Once you have the MJML extension installed, you can create a new email template in the `src` directory. After creating the new email template and with the `.mjml` file open in your editor, open the command palette with `Ctrl+Shift+P` and search for `MJML: Export to HTML`. This will convert the `.mjml` file to a `.html` file and now you can save it in the build directory.
