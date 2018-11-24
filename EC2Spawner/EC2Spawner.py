import jupyterhub
import boto3

from jupyterhub.spawner import LocalProcessSpawner


class EC2Spawner(LocalProcessSpawner):
    """
    A JupyterHub spawner using Boto3 to create EC2 instances on demand.
    """

    def user_env(self, env):
        env['USER'] = self.user.name
        env['HOME'] = self.home_path
        env['SHELL'] = '/bin/bash'
        return env

    @gen.coroutine
    def start(self):
        notebook_server_ip = yield self.start_ec2_instance() # that would be a function that uses boto3 to start an instance, pass it the dict from get_env(), and return its IP
        return (notebook_server_ip, NOTEBOOK_SERVER_PORT)


    @gen.coroutine
    def stop():
        try:
            stop_ec2_instance(self.ec2_instance_id) # function that uses boto3 to stop an instance based on instance_id
        except Exception as e:
            print("Error in terminating instance " + self.ec2_instance_id) # easy to save the instance id when you start the instance
            print(str(e)) # this will print the error on our JupyterHub process' output

    @gen.coroutine
    def poll():
        try:
            # Return None if ok else 0
            return None
        except:
            return 0


    def get_state(self):
        """get the current state"""
        """To save the state, so that we can persist it over restarts or similar."""
        """In our case it would include for example the instance ID of the EC2 instance we’ve spawned for our single-user server.:"""
        state = super().get_state()
        if self.ec2_instance_id:
            state['ec2_instance_id'] = self.ec2_instance_id
        return state

    def load_state():
        """To load the state from above (i.e. read the value of state['ec2_instance_id'] that get_state() previously wrote)."""
        