#!/usr/bin/env bash

echo "=========================================================="
echo " [CHAOS TEST] Triggering High CPU Load on sre-app"
echo " Timestamp: $(date -u '+%Y-%m-%d %H:%M:%SZ')"
echo "=========================================================="

# Find an active pod name
POD_NAME=$(kubectl get pods -n production -l app.kubernetes.io/name=microservice -o jsonpath='{.items[0].metadata.name}')
echo "Targeting pod: $POD_NAME"

echo "Spawning 20 concurrent intensive CPU worker tasks..."
for i in {1..20}; do
  kubectl exec -n production "$POD_NAME" -- curl -s "http://localhost:8000/stress/cpu?duration=90" > /dev/null 2>&1 &
done

echo "Workers running in background for 90 seconds."
echo "Monitoring CPU consumption... (Press Ctrl+C anytime to stop)"
while true; do
  kubectl top pods -n production 2>/dev/null || echo "Waiting for metrics..."
  sleep 5
done
