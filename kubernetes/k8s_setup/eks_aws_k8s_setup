EKS Cluster Setup — Step by Step
1. AWS prerequisites

You need:

AWS account
IAM user/role with permissions to create EKS, VPC, EC2, IAM resources
AWS CLI
kubectl
eksctl — optional, but makes EKS creation much easier

Check:

aws --version
kubectl version --client
eksctl version

Configure AWS:

aws configure

Enter:

AWS Access Key ID
AWS Secret Access Key
Default region: us-east-1
Default output format: json

Verify:

aws sts get-caller-identity
2. Create VPC

For a production-style EKS cluster, create:

VPC
├── Public Subnet AZ-1
├── Public Subnet AZ-2
├── Private Subnet AZ-1
└── Private Subnet AZ-2

Typical architecture:

                    Internet
                       |
                 Internet Gateway
                       |
              +--------+--------+
              |       VPC       |
              |                 |
        Public Subnet       Public Subnet
          AZ-1                  AZ-2
             |                    |
           NAT GW               NAT GW
             |                    |
        Private Subnet       Private Subnet
          AZ-1                  AZ-2
             |                    |
          EKS Node             EKS Node

For learning/testing, you can also use an existing VPC with suitable subnets.

3. Create EKS cluster

You have two common options.

Option A — AWS Console

Go to:

AWS Console → EKS → Clusters → Create cluster

Choose:

Cluster name:
Devops-EKS-cluster01

Kubernetes version:
1.34

For the cluster IAM role, create/select an EKS cluster role with:

AmazonEKSClusterPolicy

Then select your VPC and at least two subnets.

Create the cluster.

4. Create worker nodes

After the control plane is ready:

EKS
 |
 +-- Control Plane
 |
 +-- Node Group
       |
       +-- EC2 Node
       +-- EC2 Node

Go to:

EKS → Clusters → Devops-EKS-cluster01 → Compute → Add node group

For example:

Node group name:
devops-nodegroup

Instance type:
t3.medium

Desired:
2

Minimum:
1

Maximum:
3

The node IAM role normally needs:

AmazonEKSWorkerNodePolicy
AmazonEC2ContainerRegistryPullOnly
AmazonEKS_CNI_Policy

Create the node group.

5. Connect kubectl to EKS

Once the cluster and nodes are ready:

aws eks update-kubeconfig \
  --region us-east-1 \
  --name Devops-EKS-cluster01

Check:

kubectl get nodes

You should see something similar to:

NAME                             STATUS   ROLES    AGE
ip-172-31-10-101.ec2.internal    Ready    <none>   5m
ip-172-31-20-102.ec2.internal    Ready    <none>   5m

Check cluster:

kubectl cluster-info
6. Deploy nginx

Create a deployment:

kubectl create deployment nginx --image=nginx

Check:

kubectl get deployment
kubectl get pods

Expose it:

kubectl expose deployment nginx \
  --type=LoadBalancer \
  --port=80

Check:

kubectl get svc nginx

You may initially see:

NAME    TYPE           CLUSTER-IP      EXTERNAL-IP
nginx   LoadBalancer   10.100.x.x      <pending>

After AWS provisions the load balancer:

NAME    TYPE           CLUSTER-IP      EXTERNAL-IP
nginx   LoadBalancer   10.100.x.x      xxx.elb.amazonaws.com

Then:

curl http://xxx.elb.amazonaws.com

or open the DNS name in your browser.

7. Understand the EKS architecture

At this point your setup is:

                    AWS
                     |
                EKS Cluster
                     |
          +----------+----------+
          |                     |
    EKS Control Plane      Managed Node Group
          |                     |
          |                +----+----+
          |                |         |
          |              EC2       EC2
          |                |         |
          +----------------+---------+
                           |
                       Kubernetes
                           |
                  +--------+--------+
                  |                 |
               nginx Pod        nginx Pod
                  |
               Service
                  |
             Load Balancer
                  |
               Internet

The important point is that EKS manages the Kubernetes control plane, while your managed node group provides the worker capacity.

8. Install AWS Load Balancer Controller

If you want Kubernetes Ingress resources to create an AWS Application Load Balancer (ALB), install the AWS Load Balancer Controller.

This is different from simply using:

type: LoadBalancer

The architecture becomes:

Internet
   |
   v
AWS ALB
   |
   v
Ingress
   |
   v
Kubernetes Service
   |
   v
Pods

You'll need:

IAM permissions
OIDC/IRSA configuration
AWS Load Balancer Controller
IngressClass

Check whether it exists:

kubectl get deployment -n kube-system

Look for:

aws-load-balancer-controller
