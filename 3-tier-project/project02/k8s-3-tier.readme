🚀 3-Tier React + Spring Boot + PostgreSQL on Kubernetes
Final architecture
                         INTERNET
                            │
                            ▼
                    Public IP / EIP
                    98.80.123.55
                            │
                            ▼
                  ┌──────────────────┐
                  │  NGINX Ingress   │
                  │  ingress-nginx   │
                  └────────┬─────────┘
                           │
                 ┌─────────┴─────────┐
                 │                   │
                /                  /app1
                 │                   │
                 ▼                   ▼
        ┌────────────────┐   ┌────────────────┐
        │ frontend-svc   │   │ backend-svc    │
        │ ClusterIP:8082 │   │ ClusterIP:8080 │
        └───────┬────────┘   └───────┬────────┘
                │                    │
                ▼                    ▼
         ┌─────────────┐      ┌──────────────┐
         │ React × 2   │      │ Spring Boot×2│
         └─────────────┘      └───────┬──────┘
                                      │
                                      ▼
                              ┌────────────────┐
                              │ postgres-svc   │
                              │ ClusterIP:5432 │
                              └───────┬────────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │ PostgreSQL   │
                              │ postgres-0   │
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │ PVC 10Gi     │
                              │ gp3 / EBS    │
                              └──────────────┘
1. Kubernetes cluster

You already had a kubeadm cluster:

k8s-master       Ready
k8s-worker01     NotReady

Because you decided to run everything on the master, we used:

nodeSelector:
  kubernetes.io/hostname: k8s-master

for the application workloads.

Your master:

k8s-master
172.31.30.35
Kubernetes v1.33.13
containerd
2. Create namespace

Everything was deployed into:

three-tier

Create it with:

kubectl create namespace three-tier

Verify:

kubectl get ns
3. PostgreSQL Secret

Create:

01-postgres-secret.yaml

Example:

apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: three-tier
type: Opaque
stringData:
  username: ankit
  password: ankit

Apply:

kubectl apply -f 01-postgres-secret.yaml

Check:

kubectl get secret -n three-tier
4. PostgreSQL StatefulSet

We used a StatefulSet because PostgreSQL is a stateful application.

Example:

apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: three-tier
spec:
  serviceName: postgres-service
  replicas: 1

  selector:
    matchLabels:
      app: postgres

  template:
    metadata:
      labels:
        app: postgres

    spec:
      nodeSelector:
        kubernetes.io/hostname: k8s-master

      containers:
        - name: postgres
          image: postgres:16

          ports:
            - containerPort: 5432

          env:
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: username

            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password

            - name: POSTGRES_DB
              value: appdb

          volumeMounts:
            - name: postgres-storage
              mountPath: /var/lib/postgresql/data

  volumeClaimTemplates:
    - metadata:
        name: postgres-storage

      spec:
        accessModes:
          - ReadWriteOnce

        storageClassName: gp3

        resources:
          requests:
            storage: 10Gi

Apply:

kubectl apply -f 02-postgres.yaml
5. PostgreSQL lost+found problem

Initially PostgreSQL failed with:

directory "/var/lib/postgresql/data" exists but is not empty
It contains a lost+found directory

This happens because the EBS filesystem contains lost+found.

The solution is to mount a subdirectory rather than the filesystem root.

For PostgreSQL 16, we used the appropriate data directory configuration/mount approach so PostgreSQL could initialize successfully.

Eventually:

postgres-0   1/1   Running

and the logs showed:

database system is ready to accept connections
6. PostgreSQL Service

Create:

apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: three-tier
spec:
  type: ClusterIP

  selector:
    app: postgres

  ports:
    - port: 5432
      targetPort: 5432

Apply:

kubectl apply -f 03-postgres-service.yaml

The backend connects using:

postgres-service:5432

Never use the PostgreSQL Pod IP, because Pod IPs can change.

7. Verify PostgreSQL
kubectl get pods -n three-tier

Expected:

postgres-0   1/1   Running

PVC:

kubectl get pvc -n three-tier

Expected:

postgres-storage-postgres-0   Bound   10Gi   RWO   gp3

Service:

kubectl get svc -n three-tier

Expected:

postgres-service   ClusterIP   ...   5432/TCP
8. Spring Boot backend Deployment

Your backend image:

ankitrajput/springboot_app_with_db:6.0.0

Deployment:

apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: three-tier
spec:
  replicas: 2

  selector:
    matchLabels:
      app: backend

  template:
    metadata:
      labels:
        app: backend

    spec:
      nodeSelector:
        kubernetes.io/hostname: k8s-master

      containers:
        - name: backend
          image: ankitrajput/springboot_app_with_db:6.0.0

          ports:
            - containerPort: 8080

          env:
            - name: POSTGRES_URL
              value: postgres-service

            - name: POSTGRES_PORT
              value: "5432"

            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: username

            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password

Apply:

kubectl apply -f 05-backend-deployment.yaml
9. Backend Service
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: three-tier
spec:
  type: ClusterIP

  selector:
    app: backend

  ports:
    - port: 8080
      targetPort: 8080

Apply:

kubectl apply -f 06-backend-service.yaml
10. Backend verification

We verified Spring Boot directly with:

kubectl port-forward -n three-tier svc/backend-service 8080:8080

Then:

curl http://127.0.0.1:8080/actuator/health

Result:

{
  "status": "UP",
  "groups": [
    "liveness",
    "readiness"
  ]
}

We also verified:

curl http://127.0.0.1:8080/

Result:

hello friends

And:

curl http://127.0.0.1:8080/topics

returned HTTP 200.

So:

Spring Boot → PostgreSQL

is working.

11. React frontend Deployment

Your React image:

ankitrajput/frontend-app-react:2.0.0

Deployment:

apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: three-tier
spec:
  replicas: 2

  selector:
    matchLabels:
      app: frontend

  template:
    metadata:
      labels:
        app: frontend

    spec:
      nodeSelector:
        kubernetes.io/hostname: k8s-master

      containers:
        - name: frontend
          image: ankitrajput/frontend-app-react:2.0.0

          ports:
            - containerPort: 8082

Apply:

kubectl apply -f 07-frontend-deployment.yaml
12. Frontend Service
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: three-tier
spec:
  type: ClusterIP

  selector:
    app: frontend

  ports:
    - port: 8082
      targetPort: 8082

Apply:

kubectl apply -f 08-frontend-service.yaml
13. Verify frontend
kubectl get pods -n three-tier

We reached:

frontend-...   1/1   Running
frontend-...   1/1   Running

And:

kubectl get endpoints -n three-tier

showed:

frontend-service → 2 endpoints
backend-service  → 2 endpoints
postgres-service → 1 endpoint

That means Kubernetes Services are correctly selecting Pods.

14. NGINX Ingress Controller

You already had NGINX installed:

ingress-nginx-controller

Service:

Type:       LoadBalancer
External IP: 54.173.178.225

Later you tested through:

98.80.123.55

So your public endpoint is:

http://98.80.123.55

IngressClass:

nginx

Verify anytime with:

kubectl get svc -n ingress-nginx
kubectl get ingressclass
kubectl get pods -n ingress-nginx
15. Final Ingress configuration

The important lesson from our testing is: keep the frontend rule simple.

Use:

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: three-tier-ingress
  namespace: three-tier

spec:
  ingressClassName: nginx

  rules:
    - http:
        paths:

          - path: /app1
            pathType: Prefix
            backend:
              service:
                name: backend-service
                port:
                  number: 8080

          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 8082

Apply:

kubectl apply -f 09-ingress.yaml
16. Final URL

Frontend:

http://98.80.123.55/

This routes to:

NGINX
   ↓
frontend-service:8082
   ↓
React

Backend:

http://98.80.123.55/app1

routes to:

NGINX
   ↓
backend-service:8080
   ↓
Spring Boot
Important

Your Spring Boot application actually exposes:

/
 /topics
 /actuator/health
