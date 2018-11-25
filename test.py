import os
import EC2Spawner.EC2Spawner as EC2Spawner
ec2spawner = EC2Spawner

from dotenv import load_dotenv
load_dotenv()

instanceDef= {
    'AWS_AMI_ID': os.getenv("AWS_AMI_ID"),
    'AWS_KEYNAME': os.getenv("AWS_KEYNAME"),
    'AWS_SECURITY_GROUP': os.getenv('AWS_SECURITY_GROUP'),
    'AWS_SUBNET': os.getenv("AWS_SUBNET"),
    'DryRun':False,
    'AWS_INSTANCE_NAME': 'Jupyter',
    'AWS_IAM_ARN': os.getenv('AWS_IAM_ARN')
}

#print(ec2spawner.buildInstance(instanceDef))
#print(ec2spawner.user_env('', {}, instanceDef))