"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import s3
from pulumi_aws import ec2
from pulumi_aws import eks
from pulumi_aws import iam



class test2:
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
        eks_cluster = eks.Cluster(cluster_name,
            vpc_config=eks.ClusterVpcConfigArgs(
                    subnet_ids=default_subnets.ids,  # Include subnet_ids here
            ),
            # role_arn=eks_service_role.arn,  # Specify node role if needed
            )
        print("====eks_cluster: ", eks_cluster)

        # Create a Node Group
        node_group = eks.NodeGroup(nodegroup_name,
            cluster_name=eks_cluster.name,
            node_group_name=nodegroup_name,
            instance_types=[instance_type],
            scaling_config=eks.NodeGroupScalingConfigArgs(
                                                        desired_size=desired_size,
                                                        min_size=min_size,
                                                        max_size=max_size,
                                                        ),
            subnet_ids=default_subnets.ids,
            # node_role_arn=eks_service_role.arn,  # Specify node role if needed
            # node_root_volume_size=20,
        )

        # Get the kubeconfig for the cluster
        # kubeconfig = eks.get_cluster(cluster_name=eks_cluster.name).kubeconfig
        # kubeconfig = eks.get_kubeconfig(cluster_name=cluster_name)
        # kubeconfig = eks_cluster.kubeconfig
        # kubeconfig = pulumi.Output.all(eks_cluster.endpoint, eks_cluster.certificate_authority).apply(
        #                                 lambda args: eks.create_kubeconfig(args[0], args[1])
        #                             )

        # # Export the kubeconfig for the cluster
        # pulumi.export("kubeconfig", kubeconfig)


        # Export the cluster name
        pulumi.export("cluster_name", eks_cluster.name)


t=test2()
# t.instance_create()
# t.bucket_create()
t.cluster_create()