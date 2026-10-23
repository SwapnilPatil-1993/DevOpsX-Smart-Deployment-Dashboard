# DevOpsX — Smart Software Deployment and Monitoring Dashboard

DevOpsX is a student Minor Project prototype for viewing and recording software deployment activity in one dashboard.

## Current MVP features
- Dashboard metrics for total, successful, failed, and running deployments.
- Add deployment records with repository URL, environment, status, and notes.
- View recent deployment history.
- Delete a deployment record.
- SQLite database storage.
- Responsive dashboard UI.
- Health endpoint at `/health`.

## Tech stack
- Python and Flask
- SQLite
- HTML and CSS

## Run locally
1. Install Python 3.10 or newer.
2. Create and activate a virtual environment (recommended).
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the app:
   ```bash
   python app.py
   ```
5. Open `http://127.0.0.1:5000`.

The app creates `devopsx.db` automatically and seeds sample records for demonstration.

## Important scope note
This first version is a dashboard prototype. Deployment statuses are entered manually; it does **not yet** trigger real builds or connect to GitHub Actions. A planned next phase can add GitHub repository integration, CI workflow status, build logs, authentication, and deployment-provider APIs.

## Suggested project modules
1. Dashboard and deployment history
2. Deployment record management
3. Status and environment tracking
4. Health-check endpoint
5. Future CI/CD integration

## Academic use
Explain which parts are implemented and which are planned. Do not claim automated deployment or live GitHub monitoring until that integration is added and tested.


## Automated checks
GitHub Actions runs the Python unit test suite on pushes and pull requests targeting `main`. Open the repository Actions tab to review the latest run and any failure logs.
