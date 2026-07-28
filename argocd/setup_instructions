1. Create the Argo CD namespace
kubectl create namespace argocd

2. Install Argo CD
Use the current official stable manifest:

kubectl apply -n argocd \
  --server-side \
  --force-conflicts \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

The --server-side --force-conflicts flags are recommended by current Argo CD documentation because some CRDs are too large for the normal client-side apply mechanism.

3. Check the pods
kubectl get pods -n argocd

You should eventually see components such as:

argocd-application-controller       Running
argocd-applicationset-controller    Running
argocd-dex-server                   Running
argocd-notifications-controller     Running
argocd-redis                         Running
argocd-repo-server                  Running
argocd-server                       Running

Check services:

kubectl get svc -n argocd

You'll see:

NAME                    TYPE        CLUSTER-IP       PORT(S)
argocd-server            ClusterIP   ...              80/TCP,443/TCP
argocd-repo-server       ClusterIP   ...              8081/TCP
...
4. Get the initial admin password

Argo CD creates an initial admin password in a Kubernetes Secret.

Run:

kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
echo

Save that password temporarily.

Username:
admin


5. Login to Argo CD UI
Since you previously used a public IP and don't want to depend on a DNS name, an easier way to test Argo CD is to expose its service using NodePort.

kubectl patch svc argocd-server -n argocd \
  -p '{"spec":{"type":"NodePort"}}'

Check:

kubectl get svc argocd-server -n argocd

You'll get something like:

argocd-server   NodePort   10.x.x.x   <none>   80:30xxx/TCP,443:30yyy/TCP

Open browser: http://<publicip>:<nodeport>




-------------------------------------------------

Now setup the repo and test from argocd
Let's do a first GitHub → Argo CD → Kubernetes deployment using your existing nginx application.

The flow will be:

GitHub repository
      ↓
    Argo CD
      ↓
Kubernetes cluster
      ↓
 nginx Deployment
      ↓
 nginx Service
1. Put your Kubernetes YAML in GitHub

For example, create a GitHub repository called:

k8s-nginx

Structure:

k8s-nginx/
└── nginx.yaml

Your nginx.yaml can contain your existing Deployment and Service:

apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx:latest
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  type: NodePort
  selector:
    app: nginx
  ports:
    - name: http
      port: 8443
      targetPort: 80

Commit and push it.

2. Get your GitHub repository URL

For example:

https://github.com/YOUR_USERNAME/k8s-nginx.git

If the repository is public, Argo CD can access it directly.

If it is private, you'll need to add GitHub credentials to Argo CD.

3. Connect GitHub to Argo CD

Since you want to do this from Argo CD, you can use the Argo CD UI.

Open your Argo CD UI.

If you're using port-forward:

kubectl port-forward svc/argocd-server -n argocd 8080:443

Then open:

https://localhost:8080

Login with:

Username: admin
Password: <your initial password>
4. Add your GitHub repository

In the Argo CD UI:

Settings
   ↓
Repositories
   ↓
Connect Repo

Select the repository connection method.

For a public GitHub repository, use:

Connection Method: VIA HTTPS

Repository URL:

https://github.com/YOUR_USERNAME/k8s-nginx.git

You don't need a username/password for a public repository.

Click:

Connect

You should see:

Successful
5. Create your first Application

Go to:

Applications
   ↓
NEW APP

Fill it like this.

General

Application Name:

nginx-app

Project:

default

Sync Policy:

For your first deployment, select:

Manual

I'd recommend manual initially so you can understand what Argo CD is doing.

6. Source

Under Source:

Repository URL:

https://github.com/YOUR_USERNAME/k8s-nginx.git

Revision:

HEAD

Path:

.

Because your YAML is at the root:

k8s-nginx/
└── nginx.yaml

If you instead have:

k8s-nginx/
└── kubernetes/
    └── nginx.yaml

then Path should be:

kubernetes
7. Destination

For your current cluster, use:

Cluster URL:

https://kubernetes.default.svc

Namespace:

default

So your application configuration is essentially:

Application:
    nginx-app

Source:
    GitHub
    https://github.com/YOUR_USERNAME/k8s-nginx.git
    HEAD
    .

Destination:
    https://kubernetes.default.svc
    default

Click:

CREATE
8. Sync the application

After creating the Application, Argo CD will show:

nginx-app

SYNC STATUS: OutOfSync
HEALTH STATUS: Missing

That's expected.

Click:

SYNC

Then:

SYNCHRONIZE

Argo CD reads:

GitHub
   ↓
nginx.yaml

and creates:

Deployment/nginx-deployment
Service/nginx-service

inside Kubernetes.

9. Check from Kubernetes

On your master:

kubectl get deployment

You should see:

NAME               READY   UP-TO-DATE   AVAILABLE
nginx-deployment   2/2     2            2

Check pods:

kubectl get pods -l app=nginx -o wide

Check service:

kubectl get svc nginx-service
10. Check from Argo CD

In the Argo CD UI, your application should become:

SYNC STATUS: Synced
HEALTH STATUS: Healthy

You can also run:

argocd app list

Something like:

NAME         CLUSTER                         NAMESPACE   STATUS    HEALTH
nginx-app    https://kubernetes.default.svc  default     Synced    Healthy
