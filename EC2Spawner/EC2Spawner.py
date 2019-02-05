import asyncio, asyncssh
import os
from textwrap import dedent
import warnings
import random
import boto3
import time

from tornado import gen, ioloop
from tornado.concurrent import return_future
from tornado.log import app_log

from dotenv import load_dotenv

from traitlets import Bool, Unicode, Integer, List, observe

from jupyterhub.spawner import Spawner
load_dotenv()

class EC2Spawner(Spawner):

    # Fix the subnet issue with known hosts redirect?

    # http://traitlets.readthedocs.io/en/stable/migration.html#separation-of-metadata-and-keyword-arguments-in-traittype-contructors
    # config is an unrecognized keyword

    client = boto3.client('ec2')
    ec2 = boto3.resource('ec2')
    ec2_instance_id = None

    remote_hosts = List(trait=Unicode(),
            help="Possible remote hosts from which to choose remote_host.",
            config=True)

    # Removed 'config=True' tag.
    # Any user configureation of remote_host is redundant.
    # The spawner now chooses the value of remote_host.
    remote_host = Unicode("remote_host",
            help="SSH remote host to spawn sessions on")

    remote_port = Unicode("22",
            help="SSH remote port number",
            config=True)

    ssh_command = Unicode("/usr/bin/ssh",
            help="Actual SSH command",
            config=True)

    path = Unicode("/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin",
            help="Default PATH (should include jupyter and python)",
            config=True)

    # The get_port.py script is in scripts/get_port.py
    # FIXME See if we avoid having to deploy a script on remote side?
    # For instance, we could just install sshspawner on the remote side
    # as a package and have it put get_port.py in the right place.
    # If we were fancy it could be configurable so it could be restricted
    # to specific ports.
    remote_port_command = Unicode("/usr/bin/python /usr/local/bin/get_port.py",
            help="Command to return unused port on remote host",
            config=True)

    # FIXME Fix help, what happens when not set?
    hub_api_url = Unicode(os.getenv("HERE"),
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

    async def buildInstance(self,  instanceDef, env):
        """
            Build instance according to instanceDefinition object
            returns the id, ip address and full description of the instance once available as a dictionary.
        """
        # Create tag specifications which we use to pass variables to the instance
        tags = self.env_to_tags(env)
        
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
        
        self.log.debug("AWS Instance ID: {}".format(instance[0].id))
        waiter = self.client.get_waiter('instance_running')
        
        self.log.debug('Waiting...')
        waiter.wait(InstanceIds=[instance[0].id])
        description = self.client.describe_instances(InstanceIds=[instance[0].id])
        instanceIP = description['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']

        self.ec2_instance_ip = instanceIP
        self.log.debug("AWS Instance IP: {}".format(self.ec2_instance_ip))
        self.ec2_instance_id = instance[0].id
        return instanceIP
    
    async def start_ec2_instance(self, env):
        """Builds an ec2 instance on request"""
        instanceDef= {
            'AWS_AMI_ID': os.getenv("AWS_AMI_ID"),
            'AWS_KEYNAME': os.getenv("AWS_KEYNAME"),
            'AWS_SECURITY_GROUP': os.getenv('AWS_SECURITY_GROUP'),
            'AWS_SUBNET': os.getenv("AWS_SUBNET"),
            'DryRun':False,
            'AWS_INSTANCE_NAME': 'Jupyter',
            'AWS_IAM_ARN': os.getenv('AWS_IAM_ARN')
        }
        
        self.log.debug('building instance')
        ip = await self.buildInstance(instanceDef, env)
        return ip
    
    
    # TODO When we add host pool, we need to keep host/ip too, not just PID.
    def load_state(self, state):
        """Restore state about ssh-spawned server after a hub restart.
        The ssh-spawned processes only need the process id."""
        super().load_state(state)
        if "pid" in state:
            self.pid = state["pid"]

    # TODO When we add host pool, we need to keep host/ip too, not just PID.
    def get_state(self):
        """Save state needed to restore this spawner instance after hub restore.
        The ssh-spawned processes only need the process id."""
        state = super().get_state()
        if self.pid:
            state["pid"] = self.pid
        return state

    # TODO When we add host pool, we need to clear host/ip too, not just PID.
    def clear_state(self):
        """Clear stored state about this spawner (pid)"""
        super().clear_state()
        self.pid = 0

    # FIXME this looks like it's done differently now, there is get_env which
    # actually calls this.
    def user_env(self):
        """Augment env of spawned process with user-specific env variables."""

        # FIXME I think the JPY_ variables have been deprecated in JupyterHub
        # since 0.7.2, we should replace them.  Can we figure this out?

        env = super(EC2Spawner, self).get_env()
        env.update(dict(
            JUPYTERHUB_PREFIX=self.hub.server.base_url,
            Name='Jupyter',
            PATH=self.path
        ))

        if self.notebook_dir:
            env['NOTEBOOK_DIR'] = self.notebook_dir

        hub_api_url = self.hub.api_url
        if self.hub_api_url != '':
            hub_api_url = self.hub_api_url

        env['JPY_HUB_API_URL'] = hub_api_url
        env['JUPYTERHUB_API_URL'] = hub_api_url

        self.log.debug("Env built: {}".format(env))
        return env

    async def start(self):
        """Start single-user server on remote host."""
        envs = self.user_env()
        self.remote_host = await self.start_ec2_instance(envs)
        
        # commenting this out till I can figure out how to do aws networking within a subnet
        # port = await self.remote_random_port()
        port=int(os.getenv('REMOTE_PORT'))
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

        remote_cmd = '/usr/local/bin/'+remote_cmd

        self.log.debug("Command issued to remote serve: {}".format(remote_cmd))
        self.pid = await self.exec_notebook(remote_cmd)

        self.log.debug("Starting User: {}, PID: {}".format(self.user.name, self.pid))

        if self.pid < 0:
            return None
        # DEPRECATION: Spawner.start should return a url or (ip, port) tuple in JupyterHub >= 0.9
        return (self.remote_host, int(port))

    async def poll(self):
        """Poll ssh-spawned process to see if it is still running.
        If it is still running return None. If it is not running return exit
        code of the process if we have access to it, or 0 otherwise."""

        if not self.pid:
                # no pid, not running
            self.clear_state()
            return 0

        # send signal 0 to check if PID exists
        alive = await self.remote_signal(0)
        self.log.debug("Polling returned {}".format(alive))

        if not alive:
            self.clear_state()
            return 0
        else:
            return None
    
    async def stop_ec2_instance(self, instanceID):
        await self.ec2.instances.filter(InstanceIds=[instanceID]).terminate()

    async def stop(self, now=False):
        """Stop single-user server process for the current user."""
        alive = await self.remote_signal(15)

        try:
            self.stop_ec2_instance(self.ec2_instance_id) # function that uses boto3 to stop an instance based on instance_id
        except Exception as e:
            self.log.error("Error in terminating instance") # easy to save the instance id when you start the instance
            self.log.error(str(e)) # this will print the error on our JupyterHub process' output

        self.clear_state()

    def get_remote_user(self, username):
        """Map JupyterHub username to remote username. We don't need this right now"""
        return 'ec2-user'

    @observe('remote_host')
    def _log_remote_host(self, change):
        self.log.debug("Remote host was set to %s." % self.remote_host)

    # FIXME add docstring
    async def exec_notebook(self, command, timeout=750):
        """TBD"""

        env = self.user_env()
        
        bash_script_str = "#!/bin/bash\n"

        for item in env.items():
            # item is a (key, value) tuple
            # command = ('export %s=%s;' % item) + command
            bash_script_str += 'export %s=%s\n' % item
        bash_script_str += 'unset XDG_RUNTIME_DIR\n'

        bash_script_str += 'eval echo ${USER} >> user.log\n'
        bash_script_str += 'eval ls -l /usr/local/bin/ >> dir.log\n'

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
        
        self.log.debug('Running exec_notebook')
        
        tryCount = 0
        while(tryCount <= 3):
            try:
                self.log.debug('Attempting to make connection to remote host:' + tryCount)
                username = self.get_remote_user(self.user.name)
                self.log.debug(username, self.remote_host)
                k = asyncssh.read_private_key(self.ssh_keyfile)
                
                ## TODO tidy this logic up to retry or check it's up.
                self.log.debug("Sleeping...")
                time.sleep(10)
                self.log.debug("Done, attempting to connect...")
                async with asyncssh.connect(self.remote_host,username=username,client_keys=[k],known_hosts=None) as conn:
                    result = await conn.run("bash -s", stdin=run_script)
                    stdout = result.stdout
                    stderr = result.stderr
                    retcode = result.exit_status
                #stdout, stderr, retcode = await self.run_connection_wrapper(run_script, username, k)
            except (OSError, asyncssh.Error) as exc:
                sys.exit('SSH connection failed: ' + str(exc))
                tryCount +=1
                if(tryCount == 3):
                    raise Exception('Connection failed (OSError): '+ str(exc))
                else:
                    self.log.error('Connection failed, waiting 20 seconds...')
                    time.sleep(20)
            except:
                tryCount +=1
                if(tryCount == 3):
                    raise Exception('Connection failed (except).')
                else:
                    self.log.error('Connection failed, waiting 20 seconds...')
                    time.sleep(20)
        
             
        
        self.log.debug("exec_notebook status={}".format(retcode))
        if stdout != b'':
            pid = int(stdout)
        else:
            return -1
        return pid 

    async def remote_signal(self, sig):
        """Signal on the remote host."""

        username = self.get_remote_user(self.user.name)
        k = asyncssh.read_private_key(self.ssh_keyfile.format(username=self.user.name))

        command = "kill -s %s %d < /dev/null"  % (sig, self.pid)

        async with asyncssh.connect(self.remote_host,username=username,client_keys=[k],known_hosts=None) as conn:
            result = await conn.run(command)
            stdout = result.stdout
            stderr = result.stderr
            retcode = result.exit_status
        self.log.debug("command: {} returned {} --- {} --- {}".format(command, stdout, stderr, retcode))
        return (retcode == 0)