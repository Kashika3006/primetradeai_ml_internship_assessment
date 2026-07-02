# Minimal MLOps-style batch job 

This repository contains an automated MLOps pipeline designed to ingest financial time-series data, dynamically resolve file-formatting anomalies, execute deterministic matrix computations over a rolling mathematical window, and output standardized telemetry metrics and execution logs.

---

## Features
* **Robust Data Cleaning**: Automatically handles hidden byte-order marks (BOM), structural text-parsing bugs, and leading indices stuck to timestamp strings.
* **Deterministic Signal Generation**: Computes rolling moving averages to evaluate relative closing price momentum.
* **Standardized MLOps Artifacts**: Structured JSON telemetry output for downstream CI/CD performance tracking.
* **Containerized Parity**: Fully Dockerized execution layer ensuring consistent builds across local and cloud environments.

---

## Prerequisites

Ensure you have Python 3.10+ installed on your host system:

```bash
python --version
```

## Local Run Instructions
* **1. Set Up Environment & Install Dependencies**: It is highly recommended to use a virtual environment. Install all structural data-science and configuration parsing requirements via pip:
```bash
pip install -r requirements.txt
```
* **2. Execute the Pipeline**: The run.py script utilizes standard command-line flags to manage pipeline ingestion and exports. Run the script using your local paths:
```bash
python run.py --input data.csv --config config.yaml --output metrics.json --log run.log
```
* **3. Verification of Local Artifacts**: Upon a successful execution cycle, the pipeline yields two key tracking files:
* run.log: Comprehensive chronological execution logs detailing the validation lifecycle.
* metrics.json: High-precision data profiling including row summaries, seed values, and performance latency.

## Docker Build & Run Commands

To verify performance consistency and run the pipeline inside an isolated container, utilize the configured project Dockerfile.

* **1. Build the Docker Image**: Build the container from the project root directory:
```bash
docker build -t mlops-signal-pipeline:latest .
```
* **2. Run the Containerized Task**: Execute the containerized pipeline while mapping your local workspace via volume mounting. This ensures the output artifacts (metrics.json and run.log) are generated directly back onto your computer:
```bash
docker run --rm \
  -v "$(pwd)":/app \
  mlops-signal-pipeline:latest \
  --input data.csv --config config.yaml --output metrics.json --log run.log
```

## Example Expected Output (metrics.json)
When executed successfully against a valid configuration profile, the pipeline outputs high-precision metrics directly to your targeted destination:
```bash
{
  "version": "v1",
  "rows_processed": 10000,
  "metrics": "signal_rate",
  "value": 0.4991,
  "latency_ms": 68,
  "seed": 42,
  "status": "success"
}
```
