import os
import time
from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="SRE Evaluation Service")

# 1. Prometheus Telemetry
REQUESTS_TOTAL = Counter(
    "http_requests_total", 
    "Total incoming HTTP requests", 
    ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", 
    "HTTP request latency in seconds", 
    ["endpoint"]
)

# 2. Chaos / Failure trigger (for CrashLoopBackOff validation)
CONFIG_MODE = os.getenv("APP_ENV", "production")
if CONFIG_MODE == "CORRUPT_CONFIG":
    print("FATAL ERROR: Invalid configuration parameter detected in APP_ENV!", flush=True)
    raise SystemExit(1)

# 3. Health check for Kubernetes Probes
@app.get("/healthz")
def health_check():
    return {"status": "healthy", "env": CONFIG_MODE}

# 4. Metrics scraper endpoint for Prometheus
@app.get("/metrics")
def get_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# 5. Core service endpoint
@app.get("/api/v1/data")
def get_data():
    start_time = time.time()
    REQUESTS_TOTAL.labels(method="GET", endpoint="/api/v1/data", status="200").inc()
    
    response_data = {
        "status": "success",
        "message": "SRE Microservice is operational",
        "timestamp": time.time()
    }
    
    REQUEST_DURATION.labels(endpoint="/api/v1/data").observe(time.time() - start_time)
    return response_data

# 6. Stress test endpoint to test CPU alarms
@app.get("/stress/cpu")
def stress_cpu(duration: int = 15):
    end_time = time.time() + duration
    while time.time() < end_time:
        _ = [x ** 2 for x in range(25000)]
    return {"status": f"Stressed CPU for {duration} seconds"}
