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

echo "done everything"

/usr/local/bin/jupyterhub-singleuser --ip=0.0.0.0 --allow-root &> /home/ec2-user/jupyter
export DONE