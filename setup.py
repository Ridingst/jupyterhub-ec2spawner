from setuptools import setup

setup(
    name='jupyterhub-ec2spawner',
    version='0.6',
    description='Simple EC2 spawner for JupyterHub',
    url='https://github.com/Ridingst/jupyterhub-ec2spawner',
    author='Thomas Ridings',
    author_email='mail@thomasridings.com',
    license='3 Clause BSD',
    packages=['EC2Spawner'],
    install_requires=[
      'setuptools',
      'jupyterhub',
      'boto3',
      'tornado'
  ],
)