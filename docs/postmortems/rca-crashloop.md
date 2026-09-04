# Incident Postmortem: INC-001 - Production CrashLoopBackOff

## 1. Incident Overview
| Metric | Value |
| :--- | :--- |
| **Incident ID** | INC-20260904-001 |
| **Severity** | P1 - Critical Outage |
| **Impacted Service** | `sre-app` (FastAPI Microservice) |
| **Impacted Namespace** | `production` |
| **Mean Time to Detect (MTTD)** | 1 minute 45 seconds |
| **Mean Time to Recover (MTTR)** | 2 minutes 30 seconds |
| **Incident Commander** | On-Call SRE |
| **Resolution Status** | Resolved |

---

## 2. Impact Summary
During a rolling update, a corrupted environment variable (`APP_ENV=CORRUPT_CONFIG`) was deployed into the `production` ConfigMap. The new pods failed startup validation, causing them to terminate with exit code 1. The service degraded as 100% of the replacement pods entered a `CrashLoopBackOff` state.

---

## 3. Incident Timeline (UTC)
* **T0 (10:00:00)**: Faulty configuration change applied to `sre-app-config` via deployment update.
* **T1 (+00:25)**: Rolling update launched new pod replicas; containers failed startup check and exited immediately.
* **T2 (+01:10)**: Kubelet put containers into exponential backoff (`CrashLoopBackOff`).
* **T3 (+01:45)**: Prometheus alert **`PodCrashLoopBackOff`** transitioned from `PENDING` to **`FIRING`**.
* **T4 (+02:15)**: On-call engineer consulted Loki logs and observed fatal trace: `FATAL ERROR: Invalid configuration parameter detected in APP_ENV!`.
* **T5 (+03:30)**: On-call engineer executed runbook remediation: reverted ConfigMap `APP_ENV` to `production` and triggered rollout restart.
* **T6 (+04:15)**: New pods passed liveness/readiness probes (Status: `2/2 Running`).
* **T7 (+05:00)**: Prometheus alert automatically resolved to green. Incident closed.

---

## 4. 5-Whys Root Cause Analysis
1. **Why did the service fail?**
   * The application pods were trapped in a continuous `CrashLoopBackOff` cycle.
2. **Why were the pods crashing?**
   * The Python process encountered an unhandled fatal condition (`raise SystemExit(1)`) during boot.
3. **Why did the startup process fail?**
   * The environment variable `APP_ENV` contained the invalid value `CORRUPT_CONFIG`.
4. **Why did an invalid configuration value reach production?**
   * The ConfigMap was updated directly without configuration schema validation or syntax checking.
5. **Why was there no automated configuration validation?**
   * The Helm chart lacked a strict `values.schema.json` constraint enforcing allowable enum values (`production`, `staging`, `development`).

---

## 5. Corrective & Preventative Action Items
| Action Item | Type | Owner | Target Date |
| :--- | :--- | :--- | :--- |
| Implement `values.schema.json` in the Helm chart to reject unapproved environments | Preventative | SRE Team | 2026-09-10 |
| Add a pre-deployment dry-run and integration smoke test step to the CI/CD pipeline | Automated Guardrail | DevOps | 2026-09-08 |
| Add automated Slack/PagerDuty webhook alerts for any pod restart increase > 1 in production | Observability | SRE Team | Complete |
