# Security Architecture & Secrets Handling Strategy

## 1. Zero Secrets in Source Control
In adherence to SRE and DevSecOps security standards, no plaintext secrets, database credentials, or API keys are stored in this Git repository.
* Mechanism: 
  * The Helm chart charts/microservice/templates/secret.yaml dynamically pulls from .Values.secrets.dbPassword.
  * During automated deployments, GitHub Actions injects the secret dynamically at runtime using --set secrets.dbPassword="${{ secrets.DB_PASSWORD }}".
  * The actual value is encrypted at rest inside GitHub Repository Secrets and never exposed in workflow logs.

## 2. Least Privilege Container Security
* Non-Root Execution: The Dockerfile uses USER 10001 (appuser). Even if an application vulnerability allows arbitrary code execution, the attacker cannot modify root-owned filesystem binaries or perform kernel escalation.
* Minimal Base Image: Built on python:3.11-slim, stripping build-time compilers and extraneous binaries to minimize the CVE attack surface.

## 3. Kubernetes Network & Resource Isolation
* Resource Limits (cgroups): Enforced CPU (limits.cpu: 250m) and memory (limits.memory: 256Mi) limits ensure that a compromised or misbehaving container cannot cause a Denial of Service (DoS) to the host node.
* Namespace Isolation: Workloads are isolated into production (application) and monitoring (Prometheus/Grafana/Loki) namespaces.
