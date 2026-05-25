# Kubernetes Deployment — Quick Reference

## Prerequisites

- Docker images built and pushed to a registry
- `kubectl` configured with target cluster
- Helm 3+ installed (or use `kubectl apply -k` directly)
- Ingress controller installed (e.g., `ingress-nginx`)
- cert-manager for TLS (or pre-provisioned secret)

## Build & Push Images

```bash
# Backend
docker build -t your-registry/voise-backend:latest -f backend/Dockerfile ./backend
docker push your-registry/voise-backend:latest

# Frontend
docker build -t your-registry/voise-frontend:latest -f frontend/Dockerfile ./frontend
docker push your-registry/voise-frontend:latest
```

Update `k8s/backend/deployment.yaml` and `k8s/frontend/deployment.yaml` image fields.

## Deploy with Kustomize

```bash
# Preview
kubectl kustomize k8s/ --output -

# Apply
kubectl apply -k k8s/

# Check status
kubectl -n voise get pods
kubectl -n voise get svc
kubectl -n voise get ingress
```

## Deploy with Helm

```bash
# Set secrets
export SECRET_KEY="$(openssl rand -hex 32)"
export POSTGRES_PASSWORD="$(openssl rand -hex 16)"
export REDIS_PASSWORD="$(openssl rand -hex 16)"

# Install
helm upgrade --install voise ./helm/voise \
  --namespace voise \
  --create-namespace \
  --set secrets.secretKey="$SECRET_KEY" \
  --set secrets.postgresPassword="$POSTGRES_PASSWORD" \
  --set secrets.redisPassword="$REDIS_PASSWORD" \
  --set secrets.groqApiKey="gsk_..." \
  --set secrets.ultravoxApiKey="..." \
  --set backend.image=your-registry/voise-backend \
  --set frontend.image=your-registry/voise-frontend

# Override per environment
helm upgrade --install voise ./helm/voise -f values-prod.yaml
```

## TLS Setup

```bash
# With cert-manager
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: voise-tls
  namespace: voise
spec:
  secretName: voise-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - voise.ai
    - api.voise.ai
EOF
```

## Monitoring Access

After deploy, port-forward for local access:

```bash
kubectl -n voise port-forward svc/voise-grafana 3005:3000   # Grafana
kubectl -n voise port-forward svc/voise-prometheus 9090:9090 # Prometheus
```

Grafana: `admin` / `voise2026`

## Scaling

- Backend HPA: 2–10 pods, CPU 70% / memory 80%
- Frontend HPA: 2–8 pods, CPU 70%
- Adjust in `k8s/backend/hpa.yaml` or `helm/voise/values.yaml`
- Postgres/Redis are single-node (add HA replicas for production)

## Cleanup

```bash
kubectl delete -k k8s/
# or
helm uninstall voise --namespace voise
kubectl delete namespace voise
```
