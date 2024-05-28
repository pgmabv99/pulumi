"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import s3
from pulumi_aws import ec2



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

t=test2()
# t.instance_create()
# t.bucket_create()