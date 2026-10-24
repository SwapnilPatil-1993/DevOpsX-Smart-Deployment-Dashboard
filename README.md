# DevOpsX — Smart Software Deployment and Monitoring Dashboard

DevOpsX is a student minor-project prototype for tracking deployment records and displaying the result of a GitHub Actions CI test workflow.

## Implemented features
- Dashboard metrics for total, successful, failed, and running deployment records.
- Add and delete deployment records with repository URL, environment, status, and notes.
- SQLite database initialized automatically at application startup for local development.
- Optional PostgreSQL backend using the `DATABASE_URL` environment variable, with `psycopg` support for persistent hosting.
- Responsive dashboard UI and a health endpoint at `/health`.
- Five automated Flask application tests in `tests/test_app.py`.
- GitHub Actions workflow at `.github/workflows/ci.yml` runs the tests on pushes and pull requests targeting `main`.
- On pushes to `main`, the workflow can report the CI result, run URL, and commit SHA to the dashboard's `/api/ci-status` endpoint when the repository secret is configured.

## Live demo and source
- Live dashboard: https://devopsx-smart-deployment-dashboard.onrender.com
- GitHub repository: https://github.com/SwapnilPatil-1993/DevOpsX-Smart-Deployment-Dashboard

## Technology stack
- Python 3.10+
- Flask and Gunicorn
- SQLite
- HTML and CSS
- GitHub Actions
- Render hosting

## Run locally
1. Install Python 3.10 or newer.
2. (Recommended) Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the application:
   ```bash
   python app.py
   ```
5. Open http://127.0.0.1:5000.

The app creates `devopsx.db` and inserts sample records when the database is empty. The sample records are demonstration data, not real deployments.

## PostgreSQL setup (optional)
1. Open the `devopsx-free-postgres` database in the Render Dashboard.
2. Copy its **Internal Database URL** (keep it private).
3. Open the `devopsx-smart-deployment-dashboard` web service, then **Environment**.
4. Add `DATABASE_URL` with the copied Internal Database URL and save. Both resources are in Singapore, so use the internal URL.
5. Wait for Render to redeploy, then open `/health`; it should return `\"database\": \"postgresql\"` when the app is connected.

Do not paste the database URL into GitHub or commit it to the repository. The current SQLite records are not automatically migrated to PostgreSQL; the app initializes sample data in the new database.

## CI status integration setup
1. In Render, configure `DEVOPSX_SECRET` with a strong random value and `DEVOPSX_MONITOR_TOKEN` with a separate strong random token.
2. In GitHub, open **Settings → Secrets and variables → Actions → New repository secret**.
3. Set the secret name to `DEVOPSX_MONITOR_TOKEN` and its value to exactly match the token configured on Render. Never commit or share the token publicly.
4. Push a commit to `main` and inspect the repository's **Actions** tab. The workflow's final step reports the CI result to the dashboard.
5. If the secret is missing, tests can still run, but the workflow skips reporting the result to the dashboard.

## Important limitations
- Most deployment records are still entered manually. The project does not trigger real deployments to external providers.
- CI result reporting is implemented in code, but its end-to-end operation depends on the GitHub repository secret being configured and the workflow passing.
- Without `DATABASE_URL`, the hosted app still uses SQLite on Render's ephemeral filesystem, so records may be lost during a restart or redeploy.
- A free Render PostgreSQL instance has been created for evaluation, but Render marks it to expire on **November 23, 2026**. The app will not use it until its Internal Database URL is configured as `DATABASE_URL` on the web service. The free database is temporary, not permanent storage.
- The dashboard is a learning prototype and does not yet include user authentication or role-based access control.

## Automated tests
Run locally with:
```bash
python -m unittest discover -s tests -v
```

The GitHub Actions workflow runs the same command on pushes and pull requests targeting `main`.

## Academic presentation
Describe implemented functionality separately from limitations and planned improvements. Future scope can include durable database storage, authentication, deployment-provider integrations, build-log display, and richer monitoring.
