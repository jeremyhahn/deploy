# deploy

AWS ELB zero-downtime deployment script that includes support for creating and cleaning up dependent VPC infrastructure, ELB and EC2 instances.


## Dependencies

1. [Make](https://www.gnu.org/software/make/)
2. [Python](https://www.python.org/)
3. [Packer](https://www.packer.io/downloads.html)
4. [Test App](https://github.com/jeremyhahn/go-testapp) (managed dependency)

## Makefile

A Makefile is used to streamline various automation tasks.

#### Install

Run the make script in the root of the project:

    make install

Alternatively, you may install via PIP directly:

    pip install -e .

#### AMI Images

Packer is used to create 2 images that contain two different [Test App](https://github.com/jeremyhahn/go-testapp) binaries. The first is the binary that is pre-compiled in the repository and a second version that's been modified for the purposes of simulating a version 2 release. The only difference between the 2 binaries is the welcome message displayed to the user.

    make images

** Be sure to note the AMI IDs of these 2 images **

## Usage

deploy --help

#### Subcommands

##### vpc

This deployment scenerio needs a VPC with 3 availability zones, an ELB and 3 EC2 instances to meet the criteria of the exercise. This subcommand takes care of everything needed to bootstrap an environment.

A stack name and AMI ID are used to drive the automation. A default stack name of `jeremyhahnvpc` will be used if not provided. The default AMI ID is a vanilla AWS AMI from the market place.

> Be sure to use the AMI ID of the "v1" / first packer build here

    # Create the VPC, ELB and EC2 instances (default stack name)
    deploy --debug vpc

    # Create the VPC, ELB and EC2 instances (optional custom stack name)
    deploy --debug vpc --stack-name myvpc

    # Create the VPC, ELB and EC2 instances (using custom AMI ID)
    deploy --debug vpc --stack-name myvpc --image-id {{FIRST_PACKER_BUILD_IMAGE_ID}}

    # Deregister the EC2 instances from the ELB and destroy them
    deploy --debug vpc --destroy-nodes

    # Create the EC2 instances and register them with the ELB
    deploy --debug vpc --destroy-nodes

    # Deregister the EC2 instances from the ELB, destroy them, the ELB and VPC
    deploy --debug vpc --destroy

When this command has completed, you should see a resulting cloudformation stack along with the VPC, ELB, and EC2 instances. The ELB should be showing 3 of 3 instances in service. If so, copy and paste the DNS name of the ELB into a browser and you should be greeted with "Welcome to the test app!". Now we're ready for some zero-downtime deployment fun.

##### app

This subcommand performs the zero downtime application deployment.

    # Create a new fleet using {{SECOND_PACKER_BUILD_IMAGE_ID}} and
    # then decommission nodes using {{FIRST_PACKER_BUILD_IMAGE_ID}}
    deploy app {{FIRST_PACKER_BUILD_IMAGE_ID}} {{SECOND_PACKER_BUILD_IMAGE_ID}}

If something goes wrong during the deployment, use the `deploy vpc --image-id {{SECOND_PACKER_BUILD_IMAGE_ID}} --destroy-nodes` to terminate all instances using the new AMI ID.
