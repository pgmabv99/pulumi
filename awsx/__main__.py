"""An AWS Python Pulumi program"""
import pulumi
import pulumi_awsx as awsx
import pulumi_eks as eks
import pulumi_kubernetes as k8s


from pulumi_aws import s3
from pulumi_aws import ec2
from pulumi_aws import eks as eks_classic
from pulumi_aws import iam



class aws_classic_test:
    def __init__(self):
        print('test2 class constructor')

    def instance_create(self):
        # Define a security group to allow SSH access
        security_group = ec2.SecurityGroup('web-secgrp',
        description='Enable SSH access',
        ingress=[
            {
                'protocol': 'tcp',
                'from_port': 22,
                'to_port': 22,
                'cidr_blocks': ['0.0.0.0/0'],
            }
        ])

        # Get the latest Amazon Linux 2 AMI
        ami = ec2.get_ami(
            most_recent=True,
            owners=["amazon"],
            filters=[{"name": "name", "values": ["amzn2-ami-hvm-*-x86_64-gp2"]}]
        )

        # Create a small EC2 instance
        instance = ec2.Instance('web-server-www',
            instance_type='t2.micro',
            vpc_security_group_ids=[security_group.id],  # reference the security group here
            ami=ami.id,
            tags={
                'Name': 'web-server-www',
            })

        # Export the public IP of the instance
        pulumi.export('instance_public_ip established', instance.public_ip)

        # Print the instance ID
        instance.id.apply(lambda id: pulumi.log.info(f'official Log of Instance ID: {id}'))

    def bucket_create(self):

        # Create an AWS resource (S3 Bucket)
        bucket = s3.Bucket('pulumi-test-2')

        # Export the name of the bucket
        pulumi.export('bucket_id established ', bucket.id)
        bucket.id.apply(lambda id: pulumi.log.info(f'official Log of bucket.id: {id}'))

    def cluster_create(self):

        # Set the desired configurations
        cluster_name = "my-eks-cluster"
        nodegroup_name = "my-nodegroup"
        # region = "us-west-2"
        instance_type = "t3.medium"
        desired_size = 1
        min_size = 1
        max_size = 3
        # Create an IAM Role for the EKS service
        eks_service_role = iam.Role("eksServiceRole",
            assume_role_policy="""{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "eks.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    },
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "ec2.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    },
                    {
                    "Effect": "Allow",
                    "Action": [
                        "eks:ListFargateProfiles",
                        "eks:DescribeNodegroup",
                        "eks:ListNodegroups",
                        "eks:ListUpdates",
                        "eks:AccessKubernetesApi",
                        "eks:ListAddons",
                        "eks:DescribeCluster",
                        "eks:DescribeAddonVersions",
                        "eks:ListClusters",
                        "eks:ListIdentityProviderConfigs",
                        "iam:ListRoles"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": "ssm:GetParameter",
                    "Resource": "arn:aws:ssm:*:074196741531:parameter/*"
                }

                ]
            }"""
        )

        # Attach the necessary policies to the EKS service role
        eks_service_role_policy_attachment = iam.RolePolicyAttachment("eksServiceRolePolicyAttachment",
            policy_arn="arn:aws:iam::aws:policy/AmazonEKSServicePolicy",
            role=eks_service_role.name
        )

        # Fetch the default VPC
        default_vpc = ec2.get_vpc(default=True)
        print("====default_vpc.id: ", default_vpc.id)

        # Fetch the subnets associated with the default VPC
        default_subnets = ec2.get_subnets(filters=[{
            "name": "vpc-id",
            "values": [default_vpc.id]
        }])
        print("====default_subnets.ids: ", default_subnets.ids)

        # Create an EKS cluster using the default VPC and its subnets
        eks_cluster = eks_classic.Cluster(cluster_name,
            vpc_config=eks_classic.ClusterVpcConfigArgs(
                    subnet_ids=default_subnets.ids,  # Include subnet_ids here
            ),
            role_arn=eks_service_role.arn,  # Specify node role if needed
            )
        print("====eks_cluster: ", eks_cluster)

        # Create a Node Group
        node_group = eks_classic.NodeGroup(nodegroup_name,
            cluster_name=eks_cluster.name,
            node_group_name=nodegroup_name,
            instance_types=[instance_type],
            scaling_config=eks_classic.NodeGroupScalingConfigArgs(
                                                        desired_size=desired_size,
                                                        min_size=min_size,
                                                        max_size=max_size,
                                                        ),
            subnet_ids=default_subnets.ids,
            node_role_arn=eks_service_role.arn,  # Specify node role if needed
            # node_root_volume_size=20,
        )




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

# classic
# t=aws_classic_test()
# t.instance_create()
# t.bucket_create()
# t.cluster_create()