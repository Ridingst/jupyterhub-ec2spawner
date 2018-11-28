import jupyterhub
import asyncio, asyncssh
import boto3
import sys
import socket
import errno
from textwrap import dedent

from tornado import gen, ioloop
from tornado.concurrent import return_future
from tornado.log import app_log

from traitlets import Bool, Unicode, Integer, List, observe
import os


from jupyterhub.spawner import Spawner

class EC2Spawner(Spawner):
    """
    A JupyterHub spawner using Boto3 to create EC2 instances on demand.
    """
    print("Loaded EC2Spawner Class")
    client = boto3.client('ec2')
    ec2 = boto3.resource('ec2')
    ec2_instance_id = None
    ec2_instance_ip = None
    ec2_instance_port = int(os.getenv('AWS_NOTEBOOK_SERVER_PORT'))

    env = None

    remote_port = Unicode("22",
            help="SSH remote port number",
            config=True)

    ssh_command = Unicode("/usr/bin/ssh",
            help="Actual SSH command",
            config=True)

    path = Unicode("/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin",
            help="Default PATH (should include jupyter and python)",
            config=True)

    remote_port_command = Unicode("/usr/bin/python /usr/local/bin/get_port.py",
            help="Command to return unused port on remote host",
            config=True)

    hub_api_url = Unicode("",
            help=dedent("""If set, Spawner will configure the containers to use
            the specified URL to connect the hub api. This is useful when the
            hub_api is bound to listen on all ports or is running inside of a
            container."""),
            config=True)

    ssh_keyfile = Unicode(os.getenv("PEM_FILE_LOCATION"),
            help=dedent("""Key file used to authenticate hub with remote host.
            `~` will be expanded to the user's home directory and `{username}`
            will be expanded to the user's username"""),
            config=True)

    pid = Integer(0,
            help=dedent("""Process ID of single-user server process spawned for
            current user."""))
    
    def get_remote_user(self, username):
        """Map JupyterHub username to remote username."""
        return 'ec2-user'
    
    async def remote_random_port(self):
        """Select unoccupied port on the remote host and return it. 
        
        If this fails for some reason return `None`."""

        username = self.get_remote_user(self.user.name)
        k = asyncssh.read_private_key(self.ssh_keyfile.format(username=self.user.name))

    def setup_ssh_tunnel(port, user, server):
        """Setup a local SSH port forwarding"""
        #tunnel.openssh_tunnel(port, port, "%s@%s" % (user, server))
        call(["ssh", "-N", "-f", "%s@%s" % (user, server),
            "-L {port}:localhost:{port}".format(port=port)])



    @return_future
    def buildInstance(self,  instanceDef, env, callback):
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
        tags = self.env_to_tags(self.user_env())

        import EC2Spawner as ec2spawnerModule
        bootstrapPath = os.path.dirname(ec2spawnerModule.__file__) + '/data/bootstrap.sh'

        with open(bootstrapPath, 'r') as myfile:
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
        print(self.ec2_instance_ip)
        self.ec2_instance_id = instance[0].id
        callback(instanceIP)
    
    
    def env_to_tags(self, env):
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': []
        }]

        for key in env:
            TagSpecifications[0]['Tags'].append(
                { 'Key': key, 'Value': env[key] }
            )
        
        return TagSpecifications
    
    def user_env(self):
        env = self.get_env()
        env.update(dict(
            USER=self.user.name,
            HOME='/home',
            SHELL='/bin/bash',
            Name='Jupyter',
            JUPYTERHUB_API_URL=os.getenv('AWS_HUB_URL') + '/hub/api'
        ))

        if self.notebook_dir:
            env['NOTEBOOK_DIR'] = self.notebook_dir

        return env

    @gen.coroutine
    def start_ec2_instance(self, env):
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
        yield self.buildInstance(instanceDef, env)
        return self.ec2_instance_ip

    @gen.coroutine
    def start(self):
        envs = self.user_env()
        notebook_server_ip = yield self.start_ec2_instance(envs) # that would be a function that uses boto3 to start an instance, pass it the dict from get_env(), and return its IP
        port = yield self.remote_random_port()
        
        if port is None or port == 0:
            return False

        cmd = []
        cmd.extend(self.cmd)
        cmd.extend(self.get_args())

        if self.hub_api_url != "":
            old = "--hub-api-url={}".format(self.hub.api_url)
            new = "--hub-api-url={}".format(self.hub_api_url)
            for index, value in enumerate(cmd):
                if value == old:
                    cmd[index] = new
        for index, value in enumerate(cmd):
            if value[0:6] == '--port':
                cmd[index] = '--port=%d' % (port)

        remote_cmd = ' '.join(cmd)

        self.pid = yield self.exec_notebook(remote_cmd)

        self.log.debug("Starting User: {}, PID: {}".format(self.user.name, self.pid))

        if self.pid < 0:
            return None
        # DEPRECATION: Spawner.start should return a url or (ip, port) tuple in JupyterHub >= 0.9
        return (self.notebook_server_ip, port)
    
    @gen.coroutine
    def stop_ec2_instance(self, instanceID):
        self.ec2.instances.filter(InstanceIds=[instanceID]).terminate()

    @gen.coroutine
    def stop(self):
        try:
            self.stop_ec2_instance(self.ec2_instance_id) # function that uses boto3 to stop an instance based on instance_id
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
        print('Getting state')
        if self.ec2_instance_id:
            state['ec2_instance_id'] = self.ec2_instance_id
            state["pid"] = self.pid
            state['ec2_instance_ip'] = self.ec2_instance_ip
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
        print('Loading State')
        if 'ec2_instance_id' in state:
            self.ec2_instance_id = state['ec2_instance_id']
            self.pid = state["pid"]
            self.ec2_instance_ip = state['ec2_instance_ip']

    def clear_state(self):
        """Clear stored state about this spawner (pid)"""
        super().clear_state()
        self.pid = 0
        self.ec2_instance_id
        self.ec2_instance_ip

    async def exec_notebook(self, command):
        """TBD"""

        env = self.user_env()
        username = self.get_remote_user(self.user.name)
        k = asyncssh.read_private_key(self.ssh_keyfile.format(username=self.user.name))
        bash_script_str = "#!/bin/bash\n"

        for item in env.items():
            # item is a (key, value) tuple
            # command = ('export %s=%s;' % item) + command
            bash_script_str += 'export %s=%s\n' % item
        bash_script_str += 'unset XDG_RUNTIME_DIR\n'

        bash_script_str += '%s < /dev/null >> jupyter.log 2>&1 & pid=$!\n' % command
        bash_script_str += 'echo $pid\n'

        run_script = "/tmp/{}_run.sh".format(self.user.name)
        with open(run_script, "w") as f:
            f.write(bash_script_str)
        if not os.path.isfile(run_script):
            raise Exception("The file " + run_script + "was not created.")
        else:
            with open(run_script, "r") as f:
                self.log.debug(run_script + " was written as:\n" + f.read())

        async with asyncssh.connect(self.remote_host,username=username,client_keys=[k],known_hosts=None) as conn:
            result = await conn.run("bash -s", stdin=run_script)
            stdout = result.stdout
            stderr = result.stderr
            retcode = result.exit_status

        self.log.debug("exec_notebook status={}".format(retcode))
        if stdout != b'':
            pid = int(stdout)
        else:
            return -1

        return pid