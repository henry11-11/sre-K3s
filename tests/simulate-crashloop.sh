#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " [CHAOS TEST] Injecting Corrupt Configuration to sre-app"
echo " Timestamp: $(date -u '+%Y-%m-%d %H:%M:%SZ')"
echo "=========================================================="

# 1. Corrupt the ConfigMap
kubectl patch configmap sre-app-config -n production \
  --type merge -p '{"data":{"APP_ENV":"CORRUPT_CONFIG"}}'

# 2. Trigger rolling restart to force new pods to pick up corrupt config
kubectl rollout restart deployment sre-app -n production

echo ""
echo "Corrupt config injected! Watching pod statuses..."
kubectl get pods -n production -w
