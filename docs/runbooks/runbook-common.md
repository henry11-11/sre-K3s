# SRE Operational Runbook: Production Remediation Procedures

This playbook outlines standard operating procedures for responding to common production incidents on the sre-app microservice.

---

## Playbook 1: Immediate Pod Restart
Trigger: Pod memory leak, transient deadlocks, or stale background threads.

Commands:
# Gracefully restart all pods in production
kubectl rollout restart deployment sre-app -n production

# Monitor rollout progress
kubectl rollout status deployment sre-app -n production

---

## Playbook 2: Emergency Release Rollback
Trigger: A bad release was deployed via CI/CD causing immediate service failure.

Commands:
# 1. View deployment revision history
helm history sre-app -n production

# 2. Roll back immediately to the previous revision (0 = previous revision)
helm rollback sre-app 0 -n production

# 3. Verify pods restored to running state
kubectl get pods -n production

---

## Playbook 3: Emergency Horizontal Scaling (Traffic/Load Spikes)
Trigger: Alert HighCPUUsage firing or incoming request surge.

Commands:
# Scale up replicas from 2 to 5 immediately
kubectl scale deployment sre-app --replicas=5 -n production

# Confirm all 5 pods are Ready
kubectl get pods -n production -w

---

## Playbook 4: Debugging Crashing Pods & Fetching Previous Logs
Trigger: Pods in CrashLoopBackOff or Error.

Commands:
# View previous crash logs (before container died)
kubectl logs -n production -l app.kubernetes.io/name=microservice --previous --tail=50

# Inspect Kubelet events and health checks
kubectl describe pod -n production -l app.kubernetes.io/name=microservice | tail -n 25
