import click
import boto3
import requests
import time

cloudformation = boto3.client('cloudformation')
ec2 = boto3.client('ec2')
elb = boto3.client('elb')


def instances_with_image(image_id):
    response = ec2.describe_instances(
        Filters=[
            {
                'Name': 'image-id',
                'Values': [image_id]
            },
            {
                'Name': 'instance-state-name',
                'Values': ['pending', 'running']
            }
        ]
    )
    instance_ids = []
    for reservation in (response["Reservations"]):
        for instance in reservation["Instances"]:
            instance_ids.append(instance["InstanceId"])

    return instance_ids


def destroy_instances(stack_name, image_id):
    instance_ids = instances_with_image(image_id)
    if len(instance_ids):
        vpc = describe_stack(stack_name)
        app_lb = get_output(vpc['Outputs'], "AppLoadBalancer")
        deregister_instances(app_lb, instance_ids)
        ec2.terminate_instances(
            InstanceIds=instance_ids
        )


def create_instances(stack_name, image_id):
    vpc = describe_stack(stack_name)
    subnet_ids = [
        get_output(vpc['Outputs'], "PrivateSubnetAZ1"),
        get_output(vpc['Outputs'], "PrivateSubnetAZ2"),
        get_output(vpc['Outputs'], "PrivateSubnetAZ3")
    ]
    app_sg = get_output(vpc['Outputs'], "AppSecurityGroup")
    app_lb = get_output(vpc['Outputs'], "AppLoadBalancer")

    for subnet_id in subnet_ids:
        click.echo("Creating instance in subnet " + subnet_id + " with image id " + image_id + " and security group " + app_sg)
        response = ec2.run_instances(
            InstanceType="t2.micro",
            KeyName="tradebot",
            BlockDeviceMappings=[
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {
                    'DeleteOnTermination': True,
                    'VolumeSize': 8,
                    'VolumeType': 'standard'
                }
            }],
            ImageId=image_id,
            SubnetId=subnet_id,
            SecurityGroupIds=[app_sg],
            MinCount=1,
            MaxCount=1)


def get_external_ip():
    return requests.get("https://ipinfo.io/ip").content.replace('\n', '') + "/32"


def describe_stack(stack_name):
    responses = cloudformation.describe_stacks(
        StackName=stack_name
    )
    return responses['Stacks'][0]


def get_output(outputs, key):
    for output in outputs:
        if output['OutputKey'] == key:
            return output['OutputValue']
    return False


def register_instances(app_lb, instance_ids):
    formatted_ids = []
    for id in instance_ids:
        formatted_ids.append({'InstanceId': id})
    elb.register_instances_with_load_balancer(
        LoadBalancerName=app_lb,
        Instances=formatted_ids
    )


def deregister_instances(app_lb, instance_ids):
    formatted_ids = []
    for id in instance_ids:
        formatted_ids.append({'InstanceId': id})
    elb.deregister_instances_from_load_balancer(
        LoadBalancerName=app_lb,
        Instances=formatted_ids
    )
