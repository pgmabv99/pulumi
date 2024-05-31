import pulumi
import pulumi_awsx as awsx
import pulumi_eks as eks
import pulumi_kubernetes as k8s




class awsx_test:
    def __init__(self):

        # Get some values from the Pulumi configuration (or use defaults)
        config = pulumi.Config()
        self.min_cluster_size = config.get_int("minClusterSize", 3)
        self.max_cluster_size = config.get_int("maxClusterSize", 6)
        self.desired_cluster_size = config.get_int("desiredClusterSize", 3)
        self.eks_node_instance_type = config.get("eksNodeInstanceType", "t3.medium")
        self.vpc_network_cidr = config.get("vpcNetworkCidr", "10.0.0.0/16")
        pass

    def cluster_create(self):

        self.eks_vpc = awsx.ec2.Vpc("eks-vpc",
            enable_dns_hostnames=True,
            cidr_block=self.vpc_network_cidr)

        # Create the EKS cluster
        self.eks_cluster = eks.Cluster("eks-cluster",
            # Put the cluster in the new VPC created earlier
            vpc_id=self.eks_vpc.vpc_id,
            # Public subnets will be used for load balancers
            public_subnet_ids=self.eks_vpc.public_subnet_ids,
            # Private subnets will be used for cluster nodes
            private_subnet_ids=self.eks_vpc.private_subnet_ids,
            # Change configuration values to change any of the following settings
            instance_type=self.eks_node_instance_type,
            desired_capacity=self.desired_cluster_size,
            min_size=self.min_cluster_size,
            max_size=self.max_cluster_size,
            # Do not give worker nodes a public IP address
            node_associate_public_ip_address=False,
            # Change these values for a private cluster (VPN access required)
            endpoint_private_access=False,
            endpoint_public_access=True
            )

        # Export values to use elsewhere
        pulumi.export("kubeconfig", self.eks_cluster.kubeconfig)
        pulumi.export("vpcId", self.eks_vpc.vpc_id)
    def deploy_web_server(self):
        # Create a Kubernetes provider using the kubeconfig from the EKS cluster
        k8s_provider = k8s.Provider("k8s-provider", kubeconfig=self.eks_cluster.kubeconfig)

        # Define a deployment for a sample web server (nginx)
        app_labels = {"app": "nginx"}
        deployment = k8s.apps.v1.Deployment("nginx-deployment",
            spec=k8s.apps.v1.DeploymentSpecArgs(
                selector=k8s.meta.v1.LabelSelectorArgs(
                    match_labels=app_labels,
                ),
                replicas=1,
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels=app_labels,
                    ),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[k8s.core.v1.ContainerArgs(
                            name="nginx",
                            image="nginx:1.14.2",
                            ports=[k8s.core.v1.ContainerPortArgs(
                                container_port=80,
                            )],
                        )],
                    ),
                ),
            ),
            opts=pulumi.ResourceOptions(provider=k8s_provider)
        )

        # Define a service to expose the nginx deployment
        service = k8s.core.v1.Service("nginx-service",
            spec=k8s.core.v1.ServiceSpecArgs(
                selector=app_labels,
                ports=[k8s.core.v1.ServicePortArgs(
                    port=80,
                    target_port=80,
                )],
                type="LoadBalancer",
            ),
            opts=pulumi.ResourceOptions(provider=k8s_provider)
        )

        pulumi.export("nginx_service_ip", service.status.load_balancer.ingress[0].ip)



# import debugpy
# debugpy.listen(("localhost", 5678))
# print("Waiting for debugger attach...")
# debugpy.wait_for_client()  # Only include this line if you want the script to pause until the debugger is attached.
# print("Debugger attached.")


#high level API
t=awsx_test()
t.cluster_create()
t.deploy_web_server()
