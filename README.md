# Scanner — Image Classifier

A web app that classifies images using a real pretrained CNN
(MobileNetV2, trained on ImageNet), served through a FastAPI backend,
containerized with Docker, and shipped through a GitHub Actions CI/CD
pipeline.

This project is deliberately scoped to be **learnable end-to-end** — every
piece is small enough to read in one sitting, but it's a genuine production
pattern, not a toy.

---

## How it works

```
Browser (frontend/)
   │  drag/drop or select an image
   ▼
POST /predict  ──────────────►  FastAPI (backend/app/main.py)
                                       │
                                       ▼
                            MobileNetV2 inference (backend/app/model.py)
                                       │
                                       ▼
                          top-3 (label, confidence) predictions
                                       │
   ◄───────────────────────────────────┘
   results rendered as gauge bars
```

- **Model**: `torchvision.models.mobilenet_v2`, pretrained on ImageNet
  (1000 everyday object classes — animals, vehicles, household items, etc).
  This is *transfer learning's* starting point: you're using a model
  someone else already trained, rather than training one from scratch.
- **Backend**: FastAPI, one `/predict` endpoint that takes an uploaded
  image and returns JSON predictions. Also serves the frontend as static
  files, so the whole app is one process.
- **Frontend**: plain HTML/CSS/JS — no build step, so there's nothing
  extra to containerize or debug.
- **Containerization**: one `Dockerfile`, one container, running everything.
- **CI/CD**: GitHub Actions runs tests on every push/PR, then (only on
  `main`, only after tests pass) builds and pushes a Docker image to
  GitHub Container Registry (GHCR).

---

## Run it locally (no Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
uvicorn app.main:app --app-dir backend --reload
```

Open **http://localhost:8000**. First request will be slower while
PyTorch initializes; after that it's fast.

## Run it with Docker

```bash
docker compose up --build
```

Open **http://localhost:8000**. This is the exact same container that
CI will build and push — if it works here, it'll work in CI.

## Run the tests

```bash
cd backend
pytest tests -v
```

Tests mock the model (see `tests/test_api.py`) so they run in under a
second and don't need model weights downloaded — they test your *API
contract* (status codes, validation, response shape), not the model's
accuracy.

---

## Setting up CI/CD yourself

1. Push this project to a new GitHub repo.
2. That's it — `.github/workflows/ci-cd.yml` runs automatically. No
   secrets to configure: it authenticates to GHCR using the automatic
   `GITHUB_TOKEN`.
3. Watch it run under the repo's **Actions** tab.
4. After a push to `main` passes tests, check **Packages** on your repo
   for the built image (`ghcr.io/<you>/<repo>:latest`).

### What each job does

| Job | Trigger | Purpose |
|---|---|---|
| `test` | every push & PR | Installs deps, runs `pytest`. This is your safety net — it fails loudly before anything bad reaches `main`. |
| `build-and-push` | push to `main`, only if `test` passed | Builds the Docker image and pushes it to GHCR, tagged `latest` and with the short commit SHA. |

This is the core CI/CD idea: **CI (Continuous Integration)** verifies
every change automatically; **CD (Continuous Delivery)** turns a verified
change into a deployable artifact automatically. Nothing gets published
without passing tests first.

---

## Where to go next (suggested learning path)

1. **Swap the model.** Try `resnet18` or `efficientnet_b0` from
   `torchvision.models` — same API, different accuracy/speed trade-off.
2. **Fine-tune instead of using it as-is.** Freeze MobileNet's early
   layers and retrain the last layer on your own small image dataset
   (e.g., 3 classes of your choosing). This is the natural next step
   from "using a pretrained model" to "training."
3. **Add a real deploy step.** Extend the CD job to deploy the pushed
   image somewhere with a free tier — Render, Railway, or Fly.io all
   support "deploy this container image" directly.
4. **Add basic observability.** Log each prediction's top label and
   latency; this is what separates a demo from something you could
   reasonably operate.
5. **Harden it.** Rate-limit `/predict`, cap upload size, restrict CORS
   to your real frontend origin instead of `*`.

## Project structure

```
image-classifier-app/
├── backend/
│   ├── app/
│   │   ├── main.py        FastAPI routes
│   │   ├── model.py       Model loading + inference
│   │   └── schemas.py     Request/response models
│   ├── tests/
│   │   └── test_api.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci-cd.yml
```
