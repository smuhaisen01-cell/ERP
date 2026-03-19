# ═══════════════════════════════════════════════════════════════
# CI/CD Setup Guide — GitHub Actions + Railway
# ═══════════════════════════════════════════════════════════════

## What the Pipeline Does

On every push to `main` or pull request:

1. **Backend** — Installs Python deps, runs Ruff linter, checks syntax of all .py files, 
   validates Django config
2. **Frontend** — Installs Node deps, builds React with Vite, verifies dist/ output
3. **Docker** — Builds full Docker image (runs after backend + frontend pass)
4. **Deploy** — Auto-deploys to Railway (only on push to main, not PRs)

## Setup Steps

### 1. Add Railway Token to GitHub Secrets

1. Go to Railway dashboard → Account Settings → Tokens
2. Create a new token (or use existing project token)
3. Go to GitHub repo → Settings → Secrets and variables → Actions
4. Click "New repository secret"
5. Name: RAILWAY_TOKEN
6. Value: paste the Railway token
7. Save

### 2. Verify Workflow File

The workflow file is at: `.github/workflows/ci.yml`
GitHub auto-detects it on push.

### 3. Test It

1. Make a small change (e.g., add a comment to any file)
2. Push to main: `git push origin main`
3. Go to GitHub repo → Actions tab → watch the pipeline run
4. All 4 jobs should pass (backend, frontend, docker, deploy)

### 4. Pull Request Workflow

1. Create a branch: `git checkout -b feature/my-change`
2. Make changes, commit, push: `git push origin feature/my-change`
3. Create PR on GitHub
4. CI runs automatically — backend, frontend, docker checks
5. Deploy does NOT run on PRs (only on main merge)
6. Merge PR → deploy triggers automatically

## Pipeline Duration

Typical run times:
- Backend: ~1-2 minutes
- Frontend: ~1-2 minutes  
- Docker: ~3-5 minutes
- Deploy: ~2-3 minutes
- Total: ~5-8 minutes

## Troubleshooting

**Backend fails on Django check:**
- Usually warnings, not errors. Check if `--deploy` flag shows critical issues.

**Frontend build fails:**
- Check for duplicate imports, missing dependencies in package.json.

**Docker build fails:**
- Check Dockerfile, requirements.txt, and .dockerignore.

**Deploy fails:**
- Verify RAILWAY_TOKEN secret is set correctly.
- Check Railway dashboard for deployment logs.
