# DevOpsX — Smart Software Deployment and Monitoring Dashboard

DevOpsX is a student minor-project prototype for tracking deployment records and displaying GitHub Actions CI results. It includes a password-protected dashboard, CSRF-protected form actions, health checks, and optional PostgreSQL storage.

## Features
- Dashboard metrics for total, successful, failed, and running deployment records.
- Add and delete deployment records with repository URL, environment, status, and notes.
- Admin login/logout with session cookies; passwords are supplied through environment variables and are never stored in the repository.
- CSRF token validation on login and state-changing dashboard forms.
- SQLite for local development and optional PostgreSQL using `DATABASE_URL`.
- `/health` endpoint that checks the database connection.
- Automated Flask tests for dashboard behavior, login/logout, CSRF protection, CRUD, and health checks.
- GitHub Actions CI workflow runs tests on pushes and pull requests targeting `main`.
- Optional CI status reporting to `/api/ci-status` using a bearer token.

## Live demo and source
- Live dashboard: https://devopsx-smart-deployment-dashboard.onrender.com
- GitHub repository: https://github.com/SwapnilPatil-1993/DevOpsX-Smart-Deployment-Dashboard

> Authentication changes in the feature branch are not live until the pull request is reviewed/merged and the Render environment variables below are configured.

## Technology stack
Python 3.10+, Flask, Gunicorn, SQLite/PostgreSQL, HTML/CSS, GitHub Actions, and Render.

## Run locally
1. Install Python 3.10 or newer.
2. Create and activate a virtual environment (recommended).
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set a local secret and admin credentials before starting:
   ```bash
   # macOS/Linux
   export DEVOPSX_SECRET="replace-with-a-long-random-secret"
   export DEVOPSX_ADMIN_USERNAME="admin"
   export DEVOPSX_ADMIN_PASSWORD="choose-a-strong-local-password"
   python app.py
   ```
   On Windows PowerShell, use `$env:DEVOPSX_SECRET="..."`, `$env:DEVOPSX_ADMIN_USERNAME="admin"`, and `$env:DEVOPSX_ADMIN_PASSWORD="..."`.
5. Open http://127.0.0.1:5000 and sign in with the username/password you configured.

For local convenience only, if `DEVOPSX_ADMIN_PASSWORD` is not set and Render is not detected, the app uses the development default `admin123`. Do not use this default for a public deployment. The Render service must have explicit admin credentials configured.

The app creates `devopsx.db` and inserts sample records when the database is empty. These are demonstration records, not real deployments.

## Required Render environment variables
Before deploying the authentication-enabled branch, open the Render web service's **Environment** settings and set:
- `DEVOPSX_SECRET`: a long, random secret used to sign sessions.
- `DEVOPSX_ADMIN_USERNAME`: the username for the dashboard administrator.
- `DEVOPSX_ADMIN_PASSWORD`: a strong, unique password. Never commit it to GitHub or paste it into public issues.
- `DEVOPSX_MONITOR_TOKEN`: a separate random token used by GitHub Actions to report CI status.

Save the variables and redeploy. Without the admin username/password, dashboard sign-in will not work in production. Keep all values private.

## PostgreSQL setup (recommended for hosted use)
1. Open the PostgreSQL database in the Render Dashboard.
2. Copy its **Internal Database URL** and keep it private.
3. In the Render web service's **Environment** settings, set `DATABASE_URL` to that Internal Database URL.
4. Save and wait for the service to redeploy.
5. Open `https://devopsx-smart-deployment-dashboard.onrender.com/health`; the response should report `"database": "postgresql"` when connected.

Do not commit a database URL or credentials. Existing SQLite records are not automatically migrated to PostgreSQL; the new database is initialized separately. Check the database's expiry and pricing in Render before relying on it for long-term storage.

## CI status integration
1. Set `DEVOPSX_MONITOR_TOKEN` on Render.
2. In GitHub, open **Settings → Secrets and variables → Actions → New repository secret**.
3. Name the GitHub secret `DEVOPSX_MONITOR_TOKEN` and set it to the same value as the Render token.
4. Push a commit to `main` and inspect the **Actions** tab.
5. If the secret is absent, CI tests can still run but the dashboard report step is skipped.

## Automated tests
Run locally:
```bash
python -m unittest discover -s tests -v
```
The workflow runs this same command on pushes and pull requests targeting `main`.

## Current limitations
- Deployment records are mostly entered manually. The project does not yet start deployments on external hosting providers.
- CI reporting requires matching GitHub and Render secrets and a reachable live service.
- SQLite on an ephemeral hosting filesystem may lose data after restarts; use a persistent PostgreSQL database for hosted use.
- This is a student learning prototype, not a production release-management platform. Consider stronger account management, role-based access, audit logs, rate limiting, and deployment-provider integration as future improvements.

## Academic presentation
Clearly distinguish implemented features from future scope. Demo records are sample data, and deployment tracking should not be presented as proof that external deployments were actually triggered.
