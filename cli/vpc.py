import click
import boto3
import json
from common import *

@click.group()
@click.pass_context
def vpc(ctx):
    pass

@vpc.command()
@click.option('--stack-name',
    default="jeremyhahnvpc",
    help="The cloudformation stack name for the VPC")
@click.option('--image-id', default="ami-009d6802948d06e52")
@click.option('--destroy', is_flag=True)
@click.option('--create-nodes', is_flag=True)
@click.option('--destroy-nodes', is_flag=True)
@click.pass_context
def vpc(ctx, stack_name, image_id, destroy, create_nodes, destroy_nodes):

    if destroy:
        destroy_vpc(stack_name, image_id)
        print("VPC successfully destroyed")
        exit(0)
    elif create_nodes:
        create_instances(stack_name, image_id)
        stack = describe_stack(stack_name)
        app_lb = get_output(stack['Outputs'], "AppLoadBalancer")
        register_instances(app_lb, instances_with_image(image_id))
        exit(0)
    elif destroy_nodes:
        destroy_instances(stack_name, image_id)
        exit(0)

    click.echo('Creating VPC...')

    params = []
    with open('templates/vpc.parameters', 'r') as f:
        params = json.load(f)

    template_body = {}
    with open('templates/vpc.json', 'r') as f:
        template_body = json.load(f)

    for param in params:
        if param['ParameterKey'] == 'RemoteAdminNetwork':
            param['ParameterValue'] = get_external_ip()
        if ctx.obj['DEBUG']:
            print param

    cloudformation.create_stack(
        StackName=stack_name,
        TemplateBody=json.dumps(template_body),
        Capabilities=[
            'CAPABILITY_IAM'
        ],
        Parameters=params
    )

    stack = wait_for(stack_name)
    if not stack:
        click.echo('VPC creation failed')
        return False

    click.echo('VPC successfully created.')

    if ctx.obj['DEBUG']:
        print stack

    create_instances(stack_name, image_id)

    app_lb = get_output(stack['Outputs'], "AppLoadBalancer")
    register_instances(app_lb, instances_with_image(image_id))


def destroy_vpc(stack_name, image_id):
    destroy_instances(stack_name, image_id)
    cloudformation.delete_stack(
        StackName=stack_name
    )


def wait_for(stack_name):
    stack = describe_stack(stack_name)
    status = stack['StackStatus']
    if status == "CREATE_IN_PROGRESS":
        click.echo('Waiting for VPC creation to complete...')
        time.sleep(2)
        return wait_for(stack_name)
    elif status == "CREATE_COMPLETE":
        return stack
    else:
        click.echo('Failed to create stack: ' + status)
        return False
