from setuptools import setup

setup(
    name='jupyterhub-ec2spawner',
    version='0.22',
    description='Simple EC2 spawner for JupyterHub',
    url='https://github.com/Ridingst/jupyterhub-ec2spawner',
    author='Thomas Ridings',
    author_email='mail@thomasridings.com',
    include_package_data=True,
    packages=['EC2Spawner'],
    package_dir={'EC2Spawner': 'EC2Spawner'},
    package_data={'EC2Spawner': ['data/*.sh']},
    license='3 Clause BSD',
    install_requires=[
      'setuptools',
      'jupyterhub',
      'boto3',
      'tornado'
  ],
)