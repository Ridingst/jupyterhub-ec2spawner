import asyncio, asyncssh
import os
from dotenv import load_dotenv
load_dotenv()

remote_host =os.getenv('DEV_UTILS_remote_host')
username=os.getenv('DEV_UTILS_username')
k=asyncssh.read_private_key(os.getenv('DEV_UTILS_private_key'))

async def run_connection(host, username, k):
    print('Running')
    async with asyncssh.connect(host,username=username,client_keys=[k],known_hosts=None) as conn:
        result = await conn.run("eval echo ${USER}")
        stdout = result.stdout
        stderr = result.stderr
        retcode = result.exit_status
        return (stdout, stderr, retcode)

try:
    stdout, stderr, retcode = asyncio.get_event_loop().run_until_complete(run_connection(remote_host, username, k))
    print(stdout)
except (OSError, asyncssh.Error) as exc:
    sys.exit('SSH connection failed: ' + str(exc))