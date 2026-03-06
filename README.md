# InferQueue: A Cloud-Native ML Inference Job Execution Platform
### An Instruction Manual for Building a Production-Grade Model Serving and Job Orchestration System

---

## What You Are Building

A system that accepts ML inference jobs via a REST API, queues them, distributes them to worker containers that run model inference, and exposes the entire system's health through a live Grafana dashboard with alerting. The "jobs" are inference requests — you POST an input (an image, a time series, or a text prompt), the system queues the job, a worker picks it up, runs it through a model, stores the result, and you can poll for status and retrieve the output.

This is architecturally equivalent to what production ML serving platforms like Triton Inference Server, BentoML, and Qiskit Runtime do. You are building the classical foundation from scratch.

---

## System Architecture Overview

```
Client (curl / simple UI)
        |
        v
[ FastAPI REST Service ]   <-- job submission, status, result retrieval
        |
        v
[ Redis Message Queue ]    <-- jobs sit here waiting for a worker
        |
        v
[ Worker Containers ]      <-- pull jobs, load model, run inference, write results
        |
        v
[ PostgreSQL ]             <-- persistent job records, inputs, outputs, latency logs
        |
        v
[ Prometheus ]             <-- scrapes metrics from FastAPI and workers
        |
        v
[ Grafana ]                <-- dashboards, alerting
```

All components run as containers. Kubernetes orchestrates them. GitHub Actions handles CI/CD.

---

## What Model You Will Serve

Use your existing **Vision Transformer (ViT) cat classification model** from your resume. You already built it, you already know how it works, and it produces real outputs you can reason about. This is not a tutorial toy — it is a model you trained on real data with a real inference pipeline.

Later stretch goals include swapping in different models (your LSTM time series model, or a HuggingFace model pulled from the hub) without changing the surrounding infrastructure — which demonstrates the real power of this architecture.

---

## Prerequisites

Before you start, you need the following installed locally:

- **Docker Desktop** — https://docs.docker.com/get-docker/
- **minikube** (local Kubernetes cluster) — https://minikube.sigs.k8s.io/docs/start/
- **kubectl** (Kubernetes CLI) — https://kubernetes.io/docs/tasks/tools/
- **Helm** (Kubernetes package manager) — https://helm.sh/docs/intro/install/
- **Python 3.11+** — https://www.python.org/downloads/
- **Git + GitHub account** — https://github.com

Recommended: install in the order listed above. Verify each one works before moving on.

---

## Phase 1 — Understand the Pieces Individually

Do not write any project code yet. Spend time with each technology in isolation first. This phase is reading and running small throwaway examples.

### 1.1 Docker

If you are not already comfortable with Docker beyond basic usage, work through this first:

- **Official getting started guide:** https://docs.docker.com/get-started/
- **Key concepts to understand before moving on:**
  - What a Dockerfile is and how image layers work
  - The difference between an image and a container
  - How container networking works (ports, bridge networks)
  - Docker volumes and why they matter for persistent data (e.g. storing model weights)
  - `docker-compose` for running multi-container apps locally

> **Checkpoint:** Write a Dockerfile for a Python app that loads a PyTorch model from disk and runs a single inference call on a dummy input. Build it, run it, confirm it works. This proves your model can live inside a container before anything else.

---

### 1.2 Redis as a Message Queue

Redis is an in-memory data store. You will use it specifically as a job queue via a Python library called **RQ (Redis Queue)**.

- **Redis overview:** https://redis.io/docs/get-started/
- **RQ documentation:** https://python-rq.org/docs/
- **Key concepts to understand:**
  - What a queue is and why it decouples job submission from job execution
  - How RQ enqueues a job and how a worker picks it up
  - Job states: queued → started → finished / failed
  - How to inspect the queue (RQ Dashboard: https://github.com/Parallels/rq-dashboard)

> **Checkpoint:** Run Redis in a Docker container locally. Write a small Python script that enqueues a function (e.g. a dummy function that sleeps 2 seconds and returns a string) and a separate worker script that executes it. Confirm the result comes back correctly.

---

### 1.3 FastAPI

FastAPI is the REST layer — it receives inference job submissions and serves status and results back to the client.

- **FastAPI official tutorial (do the whole thing):** https://fastapi.tiangolo.com/tutorial/
- **Key concepts to understand:**
  - Path operations (GET, POST)
  - Pydantic models for request and response validation
  - Handling file uploads (you will need this for image inputs)
  - Background tasks
  - OpenAPI auto-generated docs at `/docs` — useful for manual testing

> **Checkpoint:** Build a FastAPI app with three endpoints: POST /job (accepts a JSON body or file upload), GET /job/{id}/status, GET /job/{id}/result. Return hardcoded dummy data for now. You will wire real logic in later.

---

### 1.4 PostgreSQL

PostgreSQL stores persistent job records — status, input metadata, model outputs, timestamps, and inference latency.

- **PostgreSQL official docs:** https://www.postgresql.org/docs/current/tutorial.html
- **SQLAlchemy ORM (Python):** https://docs.sqlalchemy.org/en/20/orm/quickstart.html
- **Key concepts to understand:**
  - Schema design for a jobs table (id, status, model_name, input_ref, result, latency_ms, created_at, updated_at)
  - Connecting from Python using SQLAlchemy
  - Running PostgreSQL in Docker

> **Checkpoint:** Run PostgreSQL in Docker. Connect from Python using SQLAlchemy. Create a jobs table and write functions to insert a job record and update it with a result.

---

### 1.5 Kubernetes Fundamentals

This is the most conceptually heavy piece. Do not rush it.

- **Official interactive tutorial (do all sections):** https://kubernetes.io/docs/tutorials/kubernetes-basics/
- **Recommended book — "Kubernetes Up and Running" (O'Reilly):** https://www.oreilly.com/library/view/kubernetes-up-and/9781491935668/
- **Key concepts to understand:**
  - Pods, Deployments, Services, ConfigMaps, Secrets
  - How Kubernetes schedules Pods onto nodes
  - How Services expose Pods internally and externally
  - What a ReplicaSet is and how it relates to Deployments
  - Namespaces
  - `kubectl` commands you will use constantly:
    - `kubectl apply -f`
    - `kubectl get pods / services / deployments`
    - `kubectl describe pod <name>`
    - `kubectl logs <pod>`
    - `kubectl exec -it <pod> -- bash`

> **Checkpoint:** Start a minikube cluster. Deploy the official nginx image as a Kubernetes Deployment with 2 replicas. Expose it via a Service. Hit it from your browser using `minikube service`. Delete one pod manually and watch Kubernetes recreate it automatically.

---

### 1.6 Helm

Helm is a package manager for Kubernetes. Instead of writing raw YAML manifests for every third-party component, Helm lets you install pre-packaged applications called charts with a single command. You will use it to install Redis, PostgreSQL, Prometheus, and Grafana into your cluster.

- **Helm official docs:** https://helm.sh/docs/intro/using_helm/
- **Artifact Hub (browse available charts):** https://artifacthub.io/
- **Key concepts to understand:**
  - What a chart is and what a release is
  - `helm install`, `helm upgrade`, `helm uninstall`
  - How to override default values with a `values.yaml` file

> **Checkpoint:** Add the Bitnami chart repository (`helm repo add bitnami https://charts.bitnami.com/bitnami`). Install Redis into your minikube cluster using `helm install my-redis bitnami/redis`. Confirm the pods are running with `kubectl get pods`.

---

### 1.7 Prometheus and Grafana

Prometheus scrapes metrics from your services on a schedule and stores them as time series. Grafana queries Prometheus and renders dashboards.

- **Prometheus getting started:** https://prometheus.io/docs/prometheus/latest/getting_started/
- **Grafana getting started:** https://grafana.com/docs/grafana/latest/getting-started/build-first-dashboard/
- **prometheus-client (Python library):** https://github.com/prometheus/client_python
- **Key concepts to understand:**
  - Metric types: counter, gauge, histogram, summary
  - How Prometheus scrapes — it pulls from `/metrics` endpoints on your services
  - How to expose custom metrics from a Python app
  - How to add Prometheus as a data source in Grafana
  - How to build a dashboard panel and set up an alert rule

> **Checkpoint:** Install the `kube-prometheus-stack` Helm chart (includes Prometheus and Grafana). Port-forward Grafana to localhost. Log in and confirm you can see the default Kubernetes cluster dashboards before adding any of your own.

---

## Phase 2 — Build the System

Build InferQueue in the following order. Each step should be fully working before you move to the next.

---

### Step 1 — The Inference Worker Module (No infrastructure yet)

Package your ViT model inference logic as a clean, self-contained Python function. It should accept a file path or raw bytes as input and return a structured dictionary as output. No FastAPI, no Redis, no database — just the model logic in isolation.

Input it should accept:
```python
def run_inference(image_bytes: bytes, model_name: str = "vit-cat") -> dict:
    ...
```

Output it should return:
```json
{
  "model": "vit-cat",
  "predicted_class": "tabby",
  "confidence": 0.94,
  "top_k": [
    {"class": "tabby", "score": 0.94},
    {"class": "siamese", "score": 0.04},
    {"class": "maine_coon", "score": 0.02}
  ],
  "inference_time_ms": 38.2
}
```

Write unit tests using `pytest`. Include a test that loads the real model weights and runs on a real image. This module is what every worker container will import and call.

**Model weight storage:** store your `.pth` file in a dedicated directory. Later you will mount this into the worker container via a Kubernetes volume. Do not bake the weights into the Docker image — they are too large and change independently of code.

---

### Step 2 — FastAPI Service + PostgreSQL (Local, no containers yet)

Wire your three endpoints to a real PostgreSQL database running locally via Docker Compose.

- `POST /job` — accepts a multipart file upload (the image) plus optional parameters (model name, top-k count). Writes a job record to the database with status `queued`. Returns a job ID.
- `GET /job/{id}/status` — returns current status of the job.
- `GET /job/{id}/result` — returns the full inference result once complete.

Add Prometheus metrics to the FastAPI app using `prometheus-client`:
- A counter for total jobs submitted
- A gauge for current queue depth
- A histogram for API request latency

Expose metrics at `/metrics`.

---

### Step 3 — Add Redis Queue and Worker

Add RQ to the FastAPI service. When a job is submitted, enqueue it to Redis in addition to writing the database record. Write the RQ worker that:

1. Pulls a job from the Redis queue
2. Retrieves the image bytes from wherever you stored them (local disk, or a simple object store)
3. Calls your `run_inference()` function
4. Writes the result back to PostgreSQL with status `finished` or `failed`
5. Records inference latency

Add a Prometheus gauge to the worker that tracks how many inferences it has completed and its average latency.

Run the full stack locally with Docker Compose: FastAPI + Worker + Redis + PostgreSQL + Prometheus + Grafana.

Test end to end: POST an image, poll status, retrieve result.

---

### Step 4 — Containerize Everything

Write Dockerfiles for your FastAPI service and your worker. Pay attention to:

- Your model weights should **not** be copied into the image. Use a Docker volume mount to provide them at runtime.
- PyTorch images are large. Use `python:3.11-slim` as your base and install only what you need, or use the official `pytorch/pytorch` base image.
- Pin your dependency versions in `requirements.txt`.

Push images to Docker Hub or GitHub Container Registry.

Write a `docker-compose.yml` that runs the full stack and mounts your model weights directory into the worker container.

---

### Step 5 — Deploy to Kubernetes (minikube)

Write Kubernetes manifests for:
- FastAPI Deployment + Service
- Worker Deployment (start with 1 replica)
- ConfigMap for non-secret configuration (model name, top-k default, etc.)
- Secrets for database credentials
- PersistentVolume + PersistentVolumeClaim for model weights storage

Use Helm to install Redis, PostgreSQL, Prometheus, and Grafana into the cluster.

Deploy your manifests with `kubectl apply -f`.

Verify the full flow works end to end inside the cluster before moving on.

**Reference:**
- Kubernetes Persistent Volumes: https://kubernetes.io/docs/concepts/storage/persistent-volumes/
- Kubernetes Secrets: https://kubernetes.io/docs/concepts/configuration/secret/

---

### Step 6 — Grafana Dashboards and Alerting

Build a Grafana dashboard with the following panels:

- Inference jobs submitted per minute
- Current queue depth
- Job success vs failure rate
- Average inference latency (p50, p95, p99)
- Worker container count
- GPU/CPU utilization per worker (if applicable)

Set up at least one alert: if queue depth exceeds a threshold for more than 2 minutes (workers falling behind), fire an alert. Route it to email or a Slack webhook.

**Grafana alerting docs:** https://grafana.com/docs/grafana/latest/alerting/

---

### Step 7 — CI/CD with GitHub Actions

Write a GitHub Actions workflow that:

1. On every push to `main`: runs your `pytest` test suite including the real model inference test
2. On a passing test: builds and pushes updated Docker images to your container registry
3. Optionally: applies updated Kubernetes manifests to the cluster

**References:**
- GitHub Actions docs: https://docs.github.com/en/actions
- Docker build-push action: https://github.com/docker/build-push-action

---

### Step 8 — Multi-Model Support (Stretch Goal)

Extend the system to support multiple models. The job submission endpoint accepts a `model_name` parameter. The worker loads the appropriate model based on that parameter.

Add your LSTM time series model as a second option. The input schema changes (it now accepts a JSON array of floats instead of an image), but the surrounding infrastructure — the queue, the database, the dashboards — does not change at all. This demonstrates the real value of the architecture.

To do this cleanly, define a model registry: a Python dictionary or config file that maps model names to their loader functions and expected input schemas.

---

### Step 9 — Worker Autoscaling (Stretch Goal)

Configure Kubernetes to automatically scale worker replicas up when queue depth is high and down when it is low.

- **Kubernetes Horizontal Pod Autoscaler:** https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- **KEDA (scales directly based on Redis queue depth):** https://keda.sh/docs/2.13/scalers/redis-list/

KEDA is the more production-realistic option here — it watches the Redis queue directly and scales workers in response to actual job backlog, which is exactly how production ML serving infrastructure manages load.

---

## Reference Links (Consolidated)

| Topic | Resource |
|---|---|
| Docker | https://docs.docker.com/get-started/ |
| PyTorch Docker images | https://hub.docker.com/r/pytorch/pytorch |
| Redis | https://redis.io/docs/get-started/ |
| RQ (Redis Queue) | https://python-rq.org/docs/ |
| FastAPI | https://fastapi.tiangolo.com/tutorial/ |
| FastAPI file uploads | https://fastapi.tiangolo.com/tutorial/request-files/ |
| SQLAlchemy | https://docs.sqlalchemy.org/en/20/orm/quickstart.html |
| Kubernetes basics | https://kubernetes.io/docs/tutorials/kubernetes-basics/ |
| Kubernetes Persistent Volumes | https://kubernetes.io/docs/concepts/storage/persistent-volumes/ |
| minikube | https://minikube.sigs.k8s.io/docs/start/ |
| kubectl reference | https://kubernetes.io/docs/reference/kubectl/ |
| Helm | https://helm.sh/docs/intro/using_helm/ |
| Artifact Hub | https://artifacthub.io/ |
| kube-prometheus-stack | https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack |
| Prometheus Python client | https://github.com/prometheus/client_python |
| Grafana docs | https://grafana.com/docs/grafana/latest/ |
| Grafana alerting | https://grafana.com/docs/grafana/latest/alerting/ |
| GitHub Actions | https://docs.github.com/en/actions |
| KEDA autoscaler | https://keda.sh/docs/ |
| HuggingFace model hub | https://huggingface.co/models |

---

## Suggested Repository Structure

```
inferqueue/
├── api/
│   ├── main.py            # FastAPI app
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic request/response models
│   ├── queue.py           # Redis/RQ integration
│   └── Dockerfile
├── worker/
│   ├── worker.py          # RQ worker entrypoint
│   ├── inference.py       # Model loading and inference logic
│   ├── model_registry.py  # Maps model names to loaders
│   ├── tests/
│   │   ├── test_inference.py
│   │   └── test_worker.py
│   └── Dockerfile
├── models/                # Model weights live here (not committed to git)
│   └── vit-cat.pth
├── k8s/
│   ├── api-deployment.yaml
│   ├── api-service.yaml
│   ├── worker-deployment.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   └── model-pvc.yaml
├── .github/
│   └── workflows/
│       └── ci.yml
├── docker-compose.yml
└── README.md
```

---

## What This Demonstrates to an Interviewer

When you describe this project, the narrative is:

> "I built a distributed ML inference platform that accepts image classification jobs via REST API, queues them with Redis, executes them across containerized PyTorch workers, persists results in PostgreSQL, and exposes system health through Grafana dashboards with alerting — all orchestrated with Kubernetes and deployed via a CI/CD pipeline. The architecture is directly analogous to production model serving infrastructure."

Every bullet point the quantum backend manager gave you is directly demonstrated. And because you used your own trained ViT model as the payload, it is not a tutorial — it is a real system built on top of real prior work.
