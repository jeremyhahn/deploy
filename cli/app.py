import click
import time
from common import *

@click.command()
@click.option('--stack-name',
    default="jeremyhahnvpc",
    help="The cloudformation stack name for the VPC")
@click.argument('target')
@click.argument('upgrade')
@click.pass_context
def app(ctx, stack_name, target, upgrade):
    print("Updating instances with " + target + " to " + upgrade)
    stack = describe_stack(stack_name)
    app_lb = get_output(stack['Outputs'], "AppLoadBalancer")

    create_instances(stack_name, upgrade)
    register_instances(app_lb, instances_with_image(upgrade))
    wait_for_instances(ctx, upgrade, app_lb)

    target_ids = instances_with_image(target)
    if len(target_ids):
        deregister_instances(app_lb, target_ids)
        destroy_instances(stack_name, target)


def wait_for_instances(ctx, image_id, app_lb):
    instance_ids = instances_with_image(image_id)
    num_instances = len(instance_ids)
    if num_instances < 3:
        click.echo(num_instances + " instances deployed, waiting for 3")
        wait_for_instances(ctx, image_id, app_lb)

    formatted_ids = []
    for id in instance_ids:
        formatted_ids.append({'InstanceId': id})

    response = elb.describe_instance_health(
        LoadBalancerName=app_lb,
        Instances=formatted_ids
    )

    for instance in response['InstanceStates']:
        if instance['State'] != 'InService':
            print "Waiting for instance " + instance['InstanceId'] + " to become healthy."
            if ctx.obj['DEBUG']:
                print instance
            time.sleep(2)
            wait_for_instances(ctx, image_id, app_lb)
