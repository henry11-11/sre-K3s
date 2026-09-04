# Production SRE Microservice Platform with Kubernetes, GitOps CI/CD & Full-Stack Observability

Deploying a containerized microservice onto a lightweight Kubernetes (k3s) cluster with automated GitHub Actions CI/CD, end-to-end observability (Prometheus, Grafana, Loki, Promtail), automated failure simulations, and incident response artifacts.

---

## 1. System Architecture Diagram

<img width="771" height="331" alt="image" src="https://github.com/user-attachments/assets/c16be3ce-a81e-461c-a909-61f48d96f37e" />

---

## 2. Environment Specifications
- Host OS: Ubuntu 22.04 LTS
- Hardware Resources: 6 vCPUs, 6 GB RAM, 40 GB Storage
- Kubernetes Runtime: k3s (v1.30+k3s1) with containerd runtime
- Ingress Controller: Traefik (Built-in k3s ingress)
- Deployment Engine: Helm v3.14+
- CI/CD Platform: GitHub Actions (Self-Hosted Runner)
- Observability Stack: Prometheus (kube-prometheus-stack), Grafana, Loki, Promtail

---

## 3. Setup

### Step 1: Base System Initialization
sudo apt update && sudo apt install -y curl wget git jq docker.io
sudo usermod -aG docker $USER
newgrp docker

### Step 2: Install k3s & Setup Permissions
curl -sfL https://get.k3s.io | sh -
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown ~/.kube/config
chmod 600 ~/.kube/config
export KUBECONFIG= ~/.kube/config
echo "export KUBECONFIG= ~/.kube/config" >> ~/.bashrc

### Step 3: Install Helm 3
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

### Step 4: Deploy Observability Stack (Prometheus, Grafana, Loki)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Deploy Prometheus and Grafana with tuned resources
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f observability/prometheus-values.yaml

# Deploy Loki and Promtail
helm install loki grafana/loki-stack \
  --namespace monitoring \
  -f observability/loki-values.yaml

# Apply Alerting Rules and Service Monitor
kubectl apply -f observability/prometheus-rules.yaml
kubectl apply -f observability/pod-monitor.yaml

### Step 5: Deploy Application via Helm
helm install sre-app ./charts/microservice \
  --namespace production --create-namespace \
  --set secrets.dbPassword="DynamicProductionPassword2026!"

### Step 6: Verify Cluster Health
kubectl get nodes -o wide
kubectl get pods -A

---

## 4. Viewing Instructions & Observability Access

### 1. Access Application via Ingress
The Ingress routes incoming traffic with host header matching "app.local":
- Test API endpoint:
  curl -H "Host: app.local" http://localhost/api/v1/data
- Test Health check:
  curl -H "Host: app.local" http://localhost/healthz
- Direct Prometheus metrics scrape:
  curl -H "Host: app.local" http://localhost/metrics

### 2. Access Grafana Dashboards & Logs

<img width="1851" height="992" alt="Screenshot From 2026-09-04 16-58-09" src="https://github.com/user-attachments/assets/a5dc3c57-7738-4b9a-927d-7277ae6157d4" />

Start port-forwarding Grafana:
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80 --address 0.0.0.0

- URL: http://localhost:3000 (or http://<VM_IP>:3000)
- Username: admin
- Password: AdminPassword123!
- Service Health Dashboard:
  Go to Dashboards -> "SRE Microservice - Service Health"
  Displays real-time Request Rate (RPS) and 95th Percentile Latency (P95).
- Cluster Monitoring Dashboard:
  Go to Dashboards -> "Kubernetes / Compute Resources / Cluster"
  Displays Node CPU utilization, RAM usage, and container saturation.
- Centralized Log Explorer (Loki):
  Go to Explore -> Select Data Source "Loki"
  Query application logs: {namespace="production"}
  Query error logs only: {namespace="production"} |= "error"

### 3. Access Prometheus Web UI & Alert Status

<img width="1851" height="992" alt="Screenshot From 2026-09-04 16-57-08" src="https://github.com/user-attachments/assets/c831fe21-bd8c-4f91-9f8b-e46836725a53" />

Start port-forwarding Prometheus:
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090 --address 0.0.0.0

- URL: http://localhost:9090/alerts
- Active Defined Alert Rules:
  - PodCrashLoopBackOff: Triggers when pod restart count increases > 1 within 5 minutes.
  - HighCPUUsage: Triggers when pod CPU core utilization exceeds 150m for more than 1 minute.
  - PodNotReady: Triggers when a pod remains in a non-Running phase for over 2 minutes.

---

## 5. Failure Simulations & Resilience Verification

### Scenario 1: Pod CrashLoopBackOff (Configuration Corruption)
Simulates a misconfigured deployment rollout where invalid environment parameters cause application startup failure.

- Execution Script:
  ./tests/simulate-crashloop.sh
- Failure Mechanics:
  Patches the ConfigMap with APP_ENV="CORRUPT_CONFIG" and restarts the deployment. The container logic detects the invalid string and triggers SystemExit(1).
- Detection Evidence:
  1. Prometheus alert "PodCrashLoopBackOff" turns FIRING within 1-2 minutes.
  2. Loki logs capture: "FATAL ERROR: Invalid configuration parameter detected in APP_ENV!".
  3. Pod enters CrashLoopBackOff status.
- Mitigation / Runbook Recovery:
  kubectl patch configmap sre-app-config -n production --type merge -p '{"data":{"APP_ENV":"production"}}'
  kubectl rollout restart deployment sre-app -n production

### Scenario 2: High CPU Exhaustion & Throttling
Simulates compute-intensive tasks pinning CPU usage to evaluate alerting and autoscaling readiness.

- Execution Script:
  ./tests/simulate-cpu-stress.sh
- Failure Mechanics:
  Dispatches 20 concurrent background threads to /stress/cpu?duration=90, pushing pod CPU utilization to its 250m cgroup limit.
- Detection Evidence:
  1. Prometheus alert "HighCPUUsage" turns FIRING after 1 minute of sustained load (> 150m).
  2. Grafana Service Health dashboard displays latency and CPU spikes.
- Mitigation / Runbook Recovery (Horizontal Pod Scaling):
  kubectl scale deployment sre-app --replicas=4 -n production

---

## 6. Automated CI/CD Pipeline (GitHub Actions)

Located at .github/workflows/ci-cd.yaml:
- Trigger: Push event to branch "main".
- Infrastructure: Self-hosted runner executing on the Linux VM.
- Pipeline Workflow:
  1. Source code checkout.
  2. Container authentication to GitHub Container Registry (ghcr.io).
  3. Multi-stage Docker build tagging immutable commit SHA and :latest.
  4. Static analysis and linting of Helm templates (helm lint).
  5. Helm upgrade and deployment into namespace "production" with dynamically injected secrets.
  6. Health verification using kubectl rollout status with a 120s timeout.

---

## 7. Security & Secrets Management
- Zero Plaintext Secrets in Repository: Database credentials and private keys are never stored in Git. Values are injected dynamically via GitHub Actions Secrets.
- Non-Root Container Execution: The Dockerfile enforces USER 10001 (appuser) to prevent container escape and privilege escalation.
- Resource Bounds (cgroups): Explicit CPU/Memory requests and limits prevent noisy-neighbor interference and Host Out-Of-Memory conditions.
- Network Namespace Isolation: Workloads are partitioned into separate "production" and "monitoring" namespaces.

---

## 8. Teardown Instructions

To completely remove deployed releases and cluster resources:

# 1. Uninstall Application
helm uninstall sre-app -n production
kubectl delete namespace production

# 2. Uninstall Observability Stack
helm uninstall loki -n monitoring
helm uninstall prometheus -n monitoring
kubectl delete namespace monitoring

# 3. Complete k3s Uninstall (Optional - Cleans entire VM)
/usr/local/bin/k3s-uninstall.sh

---

## 9. Assumptions
- Single-node architecture is utilized for the PoC; HA multi-node setups would run independent control planes.
- Traefik serves as the unified ingress point on standard HTTP port 80.
- Grafana, Prometheus, and Loki run in-cluster with local volume retention suitable for ephemeral evaluation workloads.
- The CI/CD pipeline leverages a self-hosted runner to allow private local cluster deployments without exposing external public ingress ports.
