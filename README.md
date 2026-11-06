# Online Library Management System

A student-friendly library web application with a DevOps practice setup.

## Features
- Admin login and student registration/login
- Add, edit, delete and search books
- Issue and return books
- Loan history for students and admin
- Automatic overdue fine calculation (default ₹5 per day)
- Configurable loan period (default 14 days)
- Pytest tests and optional Selenium browser test
- Git/GitHub workflow, Jenkins pipeline, Docker and Kubernetes manifests

## Requirements
- Python 3.10+ (Python 3.12 recommended)
- Git
- Docker Desktop (for Docker)
- Jenkins with a Python 3 and Docker-capable agent (for Jenkins pipeline)
- Kubernetes cluster such as Minikube or Docker Desktop Kubernetes (for Kubernetes)
- Chrome browser (for optional Selenium test)

## Run locally (Windows PowerShell)
```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

Default demo admin:
- Email: `admin@library.com`
- Password: `admin123`

Change these credentials before using outside a local demo. The database is created in `data/library.db` automatically.

## Run tests
```powershell
pytest -v
```

## Selenium browser test
Start the app in one terminal:
```powershell
python app.py
```
In another terminal:
```powershell
$env:RUN_SELENIUM="1"
$env:APP_URL="http://127.0.0.1:5000"
pytest -m selenium tests/test_selenium.py -v
```
Selenium 4 can manage compatible browser drivers in supported environments. If browser setup fails, run the regular pytest suite first.

## Git and GitHub
Create an empty repository on GitHub, then run these commands from this project folder:
```bash
git init
git add .
git commit -m "Initial Online Library Management System"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/online-library-management-system.git
git push -u origin main
```
Replace `YOUR-USERNAME` with your GitHub username. Do not commit passwords, tokens, database files or `.env` files.

## Docker
```bash
docker compose up --build
```
Open http://localhost:5000. Stop with:
```bash
docker compose down
```
The named Docker volume keeps the SQLite database when the container is recreated.

## Jenkins
1. Install Jenkins and ensure the agent has Python 3, pip and Docker installed.
2. Add this project to GitHub.
3. In Jenkins choose **New Item → Pipeline**.
4. Select **Pipeline script from SCM**, choose Git, enter your repository URL and branch `main`.
5. Set Script Path to `Jenkinsfile`, save and choose **Build Now**.
6. The pipeline checks out code, installs requirements, runs pytest and builds a Docker image.

The Jenkins agent needs permission to run Docker commands. Configure credentials securely if your Git repository is private.

## Kubernetes (Minikube example)
Build the image in Minikube's Docker environment:
```bash
minikube start
minikube image build -t online-library-management:latest .
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl get pods
minikube service online-library-service
```
For Docker Desktop Kubernetes, build the image with `docker build -t online-library-management:latest .` and apply the same YAML files.
Check status:
```bash
kubectl get deployments,services,pvc
kubectl logs deployment/online-library
```
This demo uses SQLite and one replica. For a production multi-replica deployment, move to PostgreSQL/MySQL and use Kubernetes Secrets for credentials.

## Configuration
| Environment variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | demo value | Flask session signing |
| `ADMIN_EMAIL` | admin@library.com | Initial admin email |
| `ADMIN_PASSWORD` | admin123 | Initial admin password |
| `DATABASE_PATH` | data/library.db | SQLite database path |
| `FINE_PER_DAY` | 5 | Fine per overdue day (₹) |
| `LOAN_DAYS` | 14 | Allowed loan period |

## Test cases
| Test ID | Test case | Expected result |
|---|---|---|
| TC01 | Admin login | Login successful |
| TC02 | Add a new book | Book added |
| TC03 | Search for a book | Matching book displayed |
| TC04 | Update book details | Details updated |
| TC05 | Issue a book | Book issued |
| TC06 | Return a book | Book returned and fine calculated |
| TC07 | Search unavailable book | Appropriate message displayed |

## Important
This is an educational starter project, not a production-ready library system. Before real deployment, add CSRF protection, rate limiting, secure secret management, HTTPS, database backups, stronger admin setup, audit logging and more complete validation.
