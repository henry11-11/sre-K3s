# Incident Postmortem: INC-002 - High CPU Exhaustion & Capacity Throttling

## 1. Incident Overview
| Metric | Value |
| :--- | :--- |
| **Incident ID** | INC-20260904-002 |
| **Severity** | P2 - Service Degradation |
| **Impacted Service** | `sre-app` (FastAPI Microservice) |
| **Impacted Namespace** | `production` |
| **Mean Time to Detect (MTTD)** | 1 minute 10 seconds |
| **Mean Time to Recover (MTTR)** | 1 minute 45 seconds |
| **Incident Commander** | On-Call SRE |
| **Resolution Status** | Resolved |

---

## 2. Impact Summary
An intensive compute job spawned 20 concurrent intensive mathematical tasks on `sre-app`. Pod CPU usage spiked from a baseline of ~5m up to the 250m cgroup limit, inducing CPU throttling. Latency degraded on `/api/v1/data` before horizontal pod scaling was invoked.

---

## 3. Incident Timeline (UTC)
* **T0 (10:30:00)**: Concurrent compute-heavy requests reached `/stress/cpu`.
* **T1 (+00:30)**: Pod CPU consumption peaked above 200m (exceeding the 150m alert threshold).
* **T2 (+01:10)**: Prometheus alert **`HighCPUUsage`** fired (`rate(container_cpu_usage_seconds_total) > 0.15 for 1m`).
* **T3 (+01:30)**: On-call engineer consulted Grafana Service Health dashboard; confirmed RPS spike and high latency percentiles.
* **T4 (+02:00)**: Remediation runbook invoked: scaled deployment from 2 to 4 replicas (`kubectl scale deployment sre-app --replicas=4`).
* **T5 (+02:30)**: Two new pod replicas came online, redistributing CPU load.
* **T6 (+03:15)**: CPU dropped back to baseline across all pods. Alert resolved.

---

## 4. 5-Whys Root Cause Analysis
1. **Why did the application experience high latency?**
   * The CPU cores allocated to the container reached their limit, causing the Linux CFS scheduler to throttle CPU cycles.
2. **Why did CPU usage spike?**
   * Concurrent compute-intensive calculations consumed all available container cycles.
3. **Why did high computation overload a single pod?**
   * Heavy tasks were executed synchronously on the web-serving thread pool instead of an asynchronous background worker queue.
4. **Why didn't the cluster absorb the traffic automatically?**
   * A Horizontal Pod Autoscaler (HPA) was not configured on the `sre-app` deployment.
5. **Why was HPA not configured?**
   * Autoscaling was not part of the initial static capacity deployment model.

---

## 5. Corrective & Preventative Action Items
| Action Item | Type | Owner | Target Date |
| :--- | :--- | :--- | :--- |
| Deploy a Kubernetes `HorizontalPodAutoscaler` (HPA) targeting 70% CPU utilization | Automated Mitigation | SRE Team | 2026-09-10 |
| Offload heavy processing tasks to asynchronous Celery/Redis worker queues | Architecture | Dev Team | 2026-09-18 |
| Fine-tune container CPU requests and limits based on observed production p99 usage | Capacity Planning | SRE Team | Complete |
