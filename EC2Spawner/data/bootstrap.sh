#!/bin/bash
yum update -y
sudo yum install python36 python36-devel python36-pip python36-setuptools python36-virtualenv -y
sudo pip-3.6 install --upgrade pip
sudo python3 -m pip install jupyterhub jupyter

# How to get instance tags
REGION=`curl -s http://169.254.169.254/latest/dynamic/instance-identity/document|grep region|awk -F\" '{print $4}'`
INSTANCE_ID=$(/usr/bin/curl --silent http://169.254.169.254/latest/meta-data/instance-id)

# Write these out to a profile file which is loaded with each session
echo 'export REGION='$REGION > ~/startup.sh
echo 'export INSTANCE_ID='$INSTANCE_ID >> ~/startup.sh


export_statement=$(aws ec2 describe-tags --region "$REGION" \
    --filters "Name=resource-id,Values=$INSTANCE_ID" \
    --query 'Tags[?!contains(Key, `:`)].[Key,Value]' \
    --output text | \
    sed -E 's/^([^\s\t]+)[\s\t]+([^\n]+)$/export \1="\2"/g >> ~/startup.sh'
)

eval $export_statement

chmod +x ~/startup.sh
sudo cp ~/startup.sh /etc/init.d/startup.sh

echo 'TESTING LOGGING' > ~/TESTLOG.log

echo '''
import argparse
import socket

def main():
    args = parse_arguments()
    if args.ip:
        print("{} {}".format(port(), ip()))
    else:
        print(port())

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", "-i",
            help="Include IP address in output",
            action="store_true")
    return parser.parse_args()

def port():
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port

def ip(address=("8.8.8.8", 80)):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(address)
    ip = s.getsockname()[0]
    s.close()
    return ip

if __name__ == "__main__":
    main()
''' > /home/ec2-user/get-port.py

echo "done everything"

/usr/local/bin/jupyterhub-singleuser --ip=0.0.0.0 --allow-root &> /home/ec2-user/jupyter
export DONE