# Configuration file for jupyterhub.

#------------------------------------------------------------------------------
# Application(SingletonConfigurable) configuration
#------------------------------------------------------------------------------

## This is an application.

## The date format used by logging formatters for %(asctime)s
#c.Application.log_datefmt = '%Y-%m-%d %H:%M:%S'

## The Logging format template
#c.Application.log_format = '[%(name)s]%(highlevel)s %(message)s'

## Set the log level by value or name.
#c.Application.log_level = 30

#------------------------------------------------------------------------------
# JupyterHub(Application) configuration
#------------------------------------------------------------------------------

## An Application for starting a Multi-User Jupyter Notebook server.

## Maximum number of concurrent servers that can be active at a time.
#
#  Setting this can limit the total resources your users can consume.
#
#  An active server is any server that's not fully stopped. It is considered
#  active from the time it has been requested until the time that it has
#  completely stopped.
#
#  If this many user servers are active, users will not be able to launch new
#  servers until a server is shutdown. Spawn requests will be rejected with a 429
#  error asking them to try again.
#
#  If set to 0, no limit is enforced.
import os
from dotenv import load_dotenv
import json

load_dotenv()

c.JupyterHub.active_server_limit = 4

from oauthenticator.github import GitHubOAuthenticator
c.JupyterHub.authenticator_class = GitHubOAuthenticator

c.GitHubOAuthenticator.oauth_callback_url = os.getenv('OAUTH_CALLBACK_URL')
c.GitHubOAuthenticator.client_id = os.getenv('OAUTH_CLIENT_ID')
c.GitHubOAuthenticator.client_secret = os.getenv('OAUTH_CLIENT_SECRET')
c.Authenticator.whitelist = set(os.getenv('AUTH_WHITELIST'))
c.Authenticator.admin_users = set(os.getenv('AUTH_ADMIN'))


## Duration (in seconds) to determine the number of active users.
c.JupyterHub.active_user_window = 1800

## Grant admin users permission to access single-user servers.
#
#  Users should be properly informed if this is enabled.
c.JupyterHub.admin_access = True

## Allow named single-user servers per user
c.JupyterHub.allow_named_servers = False

## Whether to shutdown single-user servers when the Hub shuts down.
#
#  Disable if you want to be able to teardown the Hub while leaving the single-
#  user servers running.
#
#  If both this and cleanup_proxy are False, sending SIGINT to the Hub will only
#  shutdown the Hub, leaving everything else running.
#
#  The Hub should be able to resume from database state.
#c.JupyterHub.cleanup_servers = True

## Maximum number of concurrent users that can be spawning at a time.
#
#  Spawning lots of servers at the same time can cause performance problems for
#  the Hub or the underlying spawning system. Set this limit to prevent bursts of
#  logins from attempting to spawn too many servers at the same time.
#
#  This does not limit the number of total running servers. See
#  active_server_limit for that.
#
#  If more than this many users attempt to spawn at a time, their requests will
#  be rejected with a 429 error asking them to try again. Users will have to wait
#  for some of the spawning services to finish starting before they can start
#  their own.
#
#  If set to 0, no limit is enforced.
c.JupyterHub.concurrent_spawn_limit = 3

## The config file to load
c.JupyterHub.config_file = '~/jupyterhub_config.py'

# shutdown the server after no activity for an hour
c.NotebookApp.shutdown_no_activity_timeout = 60 * 60
# shutdown kernels after no activity for 20 minutes
c.MappingKernelManager.cull_idle_timeout = 60 * 60
# check for idle kernels every two minutes
c.MappingKernelManager.cull_interval = 2 * 60

"""
JupyterHub config for server startup form

c.JupyterHub.spawner_class = 'wrapspawner.ProfilesSpawner'
c.Spawner.http_timeout = 120
c.ProfilesSpawner.profiles = [
        ("T2 Medium", 'local', 'jupyterhub.spawner.LocalProcessSoawner', {'ip':'0.0.0.0'})
]

"""