import jupyterhub
import boto3
import sys
import socket
import errno
from tornado import gen, ioloop
from tornado.concurrent import return_future
from tornado.log import app_log
import os

from jupyterhub.spawner import Spawner

class EC2Spawner(Spawner):
    client = boto3.client('ec2')
    ec2 = boto3.resource('ec2')
    ec2_instance_id = None
    ec2_instance_ip = None
    ec2_instance_port = int(os.getenv('AWS_NOTEBOOK_SERVER_PORT'))

    
    print("Loaded EC2Spawner Class")
    """
    A JupyterHub spawner using Boto3 to create EC2 instances on demand.
    """

    @return_future
    def buildInstance(self,  instanceDef, callback):
        """
            Build instance according to instanceDefinition object

            instanceDef= {
                'AWS_AMI_ID': os.getenv("AWS_AMI_ID"),
                'AWS_KEYNAME': os.getenv("AWS_KEYNAME"),
                'AWS_SUBNET': os.getenv("AWS_SUBNET"),
                "AWS_INSTANCE_NAME': 'Jupyter',
                'AWS_IAM_ARN': os.getenv('AWS_IAM_ARN'),
                'DryRun':True
            }

            returns the id, ip address and full description of the instance once available as a dictionary.
        """
        # Create tag specifications which we use to pass variables to the instance
        tags = self.user_env(instanceDef)
        import EC2Spawner as ec2spawnerModule
        dirString = os.path.dirname(ec2spawnerModule.__file__) + '/data/bootstrap.sh'
        with open(dirString, 'r') as myfile:
            UserData = myfile.read()
        
        instance = self.ec2.create_instances(
            ImageId=instanceDef['AWS_AMI_ID'],
            KeyName=instanceDef['AWS_KEYNAME'], 
            InstanceType='t2.medium',
            MinCount=1, MaxCount=1,
            DryRun=instanceDef['DryRun'],
            SubnetId=instanceDef['AWS_SUBNET'], 
            SecurityGroupIds=[instanceDef['AWS_SECURITY_GROUP']],
            TagSpecifications=tags,
            IamInstanceProfile={'Arn': instanceDef['AWS_IAM_ARN']},
            UserData=UserData
        )

        # InstanceType='t1.micro'|'t2.nano'|'t2.micro'|'t2.small'|'t2.medium'|'t2.large'|'t2.xlarge'|'t2.2xlarge'|'t3.nano'|'t3.micro'|'t3.small'|'t3.medium'|'t3.large'|'t3.xlarge'|'t3.2xlarge'|'m1.small'|'m1.medium'|'m1.large'|'m1.xlarge'|'m3.medium'|'m3.large'|'m3.xlarge'|'m3.2xlarge'|'m4.large'|'m4.xlarge'|'m4.2xlarge'|'m4.4xlarge'|'m4.10xlarge'|'m4.16xlarge'|'m2.xlarge'|'m2.2xlarge'|'m2.4xlarge'|'cr1.8xlarge'|'r3.large'|'r3.xlarge'|'r3.2xlarge'|'r3.4xlarge'|'r3.8xlarge'|'r4.large'|'r4.xlarge'|'r4.2xlarge'|'r4.4xlarge'|'r4.8xlarge'|'r4.16xlarge'|'r5.large'|'r5.xlarge'|'r5.2xlarge'|'r5.4xlarge'|'r5.8xlarge'|'r5.12xlarge'|'r5.16xlarge'|'r5.24xlarge'|'r5.metal'|'r5a.large'|'r5a.xlarge'|'r5a.2xlarge'|'r5a.4xlarge'|'r5a.12xlarge'|'r5a.24xlarge'|'r5d.large'|'r5d.xlarge'|'r5d.2xlarge'|'r5d.4xlarge'|'r5d.8xlarge'|'r5d.12xlarge'|'r5d.16xlarge'|'r5d.24xlarge'|'r5d.metal'|'x1.16xlarge'|'x1.32xlarge'|'x1e.xlarge'|'x1e.2xlarge'|'x1e.4xlarge'|'x1e.8xlarge'|'x1e.16xlarge'|'x1e.32xlarge'|'i2.xlarge'|'i2.2xlarge'|'i2.4xlarge'|'i2.8xlarge'|'i3.large'|'i3.xlarge'|'i3.2xlarge'|'i3.4xlarge'|'i3.8xlarge'|'i3.16xlarge'|'i3.metal'|'hi1.4xlarge'|'hs1.8xlarge'|'c1.medium'|'c1.xlarge'|'c3.large'|'c3.xlarge'|'c3.2xlarge'|'c3.4xlarge'|'c3.8xlarge'|'c4.large'|'c4.xlarge'|'c4.2xlarge'|'c4.4xlarge'|'c4.8xlarge'|'c5.large'|'c5.xlarge'|'c5.2xlarge'|'c5.4xlarge'|'c5.9xlarge'|'c5.18xlarge'|'c5d.large'|'c5d.xlarge'|'c5d.2xlarge'|'c5d.4xlarge'|'c5d.9xlarge'|'c5d.18xlarge'|'cc1.4xlarge'|'cc2.8xlarge'|'g2.2xlarge'|'g2.8xlarge'|'g3.4xlarge'|'g3.8xlarge'|'g3.16xlarge'|'g3s.xlarge'|'cg1.4xlarge'|'p2.xlarge'|'p2.8xlarge'|'p2.16xlarge'|'p3.2xlarge'|'p3.8xlarge'|'p3.16xlarge'|'d2.xlarge'|'d2.2xlarge'|'d2.4xlarge'|'d2.8xlarge'|'f1.2xlarge'|'f1.4xlarge'|'f1.16xlarge'|'m5.large'|'m5.xlarge'|'m5.2xlarge'|'m5.4xlarge'|'m5.12xlarge'|'m5.24xlarge'|'m5a.large'|'m5a.xlarge'|'m5a.2xlarge'|'m5a.4xlarge'|'m5a.12xlarge'|'m5a.24xlarge'|'m5d.large'|'m5d.xlarge'|'m5d.2xlarge'|'m5d.4xlarge'|'m5d.12xlarge'|'m5d.24xlarge'|'h1.2xlarge'|'h1.4xlarge'|'h1.8xlarge'|'h1.16xlarge'|'z1d.large'|'z1d.xlarge'|'z1d.2xlarge'|'z1d.3xlarge'|'z1d.6xlarge'|'z1d.12xlarge'|'u-6tb1.metal'|'u-9tb1.metal'|'u-12tb1.metal'
        
        print(instance[0].id)
        waiter = self.client.get_waiter('instance_running')
        
        print('Waiting...')
        waiter.wait(InstanceIds=[instance[0].id])
        description = self.client.describe_instances(InstanceIds=[instance[0].id])
        instanceIP = description['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']

        self.ec2_instance_ip = instanceIP
        self.ec2_instance_id = instance[0].id
        callback(instanceIP)
    
    
    def user_env(self, instanceDef):
        env = self.get_env()
        env['USER'] = self.user.name
        env['HOME'] = '/home'
        env['SHELL'] = '/bin/bash'
        env['Name'] = instanceDef['AWS_INSTANCE_NAME']
        env['JUPYTERHUB_API_URL'] = os.getenv('AWS_HUB_URL') + '/hub/api'
        
        print(env)

        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': []
        }]

        for key in env:
            TagSpecifications[0]['Tags'].append(
                { 'Key': key, 'Value': env[key] }
            )
        
        return TagSpecifications

    @gen.coroutine
    def start_ec2_instance(self):
        instanceDef= {
            'AWS_AMI_ID': os.getenv("AWS_AMI_ID"),
            'AWS_KEYNAME': os.getenv("AWS_KEYNAME"),
            'AWS_SECURITY_GROUP': os.getenv('AWS_SECURITY_GROUP'),
            'AWS_SUBNET': os.getenv("AWS_SUBNET"),
            'DryRun':False,
            'AWS_INSTANCE_NAME': 'Jupyter',
            'AWS_IAM_ARN': os.getenv('AWS_IAM_ARN')
        }
        
        print('building instance')
        yield self.buildInstance(instanceDef)
        return self.ec2_instance_ip

    @gen.coroutine
    def start(self):
        notebook_server_ip = yield self.start_ec2_instance() # that would be a function that uses boto3 to start an instance, pass it the dict from get_env(), and return its IP
        
        cmd = []
        cmd.extend(self.cmd)

        print(cmd)

        print('Server: ', self.server)

        cmd.extend(self.get_args())



        print('Type of Port', type(int(self.ec2_instance_port)))
        return (self.ec2_instance_ip, int(self.ec2_instance_port))
    
    @gen.coroutine
    def stop_ec2_instance(self, instanceID):
        self.ec2.instances.filter(InstanceIds=[instanceID]).terminate()

    @gen.coroutine
    def stop(self):
        try:
            stop_ec2_instance(self.ec2_instance_id) # function that uses boto3 to stop an instance based on instance_id
        except Exception as e:
            print("Error in terminating instance") # easy to save the instance id when you start the instance
            print(str(e)) # this will print the error on our JupyterHub process' output

    @gen.coroutine
    def poll(self, timeout=250):
        """wait for any server to show up at ip:port"""
        loop = ioloop.IOLoop.current()
        tic = loop.time()
        while loop.time() - tic < timeout:
            try:
                socket.create_connection((self.ec2_instance_ip, self.ec2_instance_port))
            except socket.error as e:
                if e.errno != errno.ECONNREFUSED:
                    app_log.error("Unexpected error waiting for ",
                        self.ec2_instance_ip, self.ec2_instance_port,"-", e
                    )
                yield gen.Task(loop.add_timeout, loop.time() + 1)
            else:
                return
        raise TimeoutError("Server at {self.ec2_instance_ip}:{self.ec2_instance_port} didn't respond in {timeout} seconds".format(
            **locals()
        ))

    def get_state(self):
        """get the current state"""
        """To save the state, so that we can persist it over restarts or similar."""
        """In our case it would include for example the instance ID of the EC2 instance we’ve spawned for our single-user server.:"""
        state = super().get_state()
        if self.ec2_instance_id:
            state['ec2_instance_id'] = self.ec2_instance_id
        return state

    def load_state(self, state):
        """
        Load state from storage required to reinstate this user's server
        This runs after __init__, so we can override it with saved unit name
        if needed. This is useful primarily when you change the unit name template
        between restarts.
        JupyterHub before 0.7 also assumed your notebook was dead if it
        saved no state, so this helps with that too!
        """
        if 'ec2_instance_id' in state:
            self.ec2_instance_id = state['ec2_instance_id']