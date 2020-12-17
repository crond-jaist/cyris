
# Create AWS instances
def create_instances(client, gNames, basevm_id, numOfIns,basevm_os_type):
    # AMI IDs for various instance types:
    # - Amazon Linux 2 AMI (HVM), SSD Volume Type - ami-0323c3dd2da7fb37d
    # - Amazon Linux AMI 2018.03.0 (HVM), SSD Volume Type - ami-01d025118d8e760db
    # - Red Hat Enterprise Linux 8 (HVM), SSD Volume Type - ami-098f16afa9edf40be
    # - Ubuntu Server 16.04 LTS (HVM), SSD Volume Type - ami-039a49e70ea773ffc
    # - Ubuntu Server 18.04 LTS (HVM), SSD Volume Type - ami-085925f297f89fce1
    # - Ubuntu Server 20.04 LTS (HVM), SSD Volume Type - ami-068663a3c619dd892
    # - Microsoft Windows Server 2019 Base - ami-04a0ee204b44cc91a
    dic = {'amazon_linux':'ami-01d025118d8e760db',
        'amazon_linux2':'ami-0323c3dd2da7fb37d',
        'red_hat':'ami-098f16afa9edf40be',
        'ubuntu_16':'ami-039a49e70ea773ffc',
        'ubuntu_18':'ami-085925f297f89fce1',
        'ubuntu_20':'ami-068663a3c619dd892',
        'windows':'ami-04a0ee204b44cc91a'}
    if basevm_os_type not in dic.keys():
        print('error ami')
        quit(-1)
    else:
        img_id = dic[basevm_os_type]
    # gNames: list, eg: ['aa','bb']
    # tags: list[dict], eg: [{}]
    # numOfIns: int
    response = client.run_instances(
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/xvda',
                'VirtualName': 'Desktop',
                'Ebs': {
                    'DeleteOnTermination': True,
                    'VolumeSize': 8,
                    'VolumeType': 'gp2'
                },
            },
        ],
        ImageId=img_id,
        InstanceType='t2.micro',
        KeyName='TESTKEY',
        MaxCount= numOfIns,
        MinCount=1,
        Monitoring={
            'Enabled':True
        },
        SecurityGroups=gNames,
        TagSpecifications=[
                        {
                            'ResourceType': 'instance',
                            'Tags': [
                                {
                                    'Key': 'Name',
                                    'Value': basevm_id
                                }
                            ]
                        }
                        ]
    )
    n = len(response['Instances'])

    if n == numOfIns:
        print('* INFO: cyris_aws: %s instance(s) created.'%(n))
    elif n < numOfIns:
        print('* ERROR: cyris_aws: Limit was exceeded => only %s instance(s) created.'%(n))
    else:
        print('* ERROR: cyris_aws: Instance creation failed.')

    ins_ids = []
    for x in response['Instances']:
        ins_ids.append(x['InstanceId'])
    return ins_ids

# Check status of AWS instances
def describe_instance_status(client, ins_ids):
    response = client.describe_instance_status(
        InstanceIds=ins_ids,
        IncludeAllInstances=True
    )

    status = response['InstanceStatuses'][0]['InstanceState']['Name']
    return status

# Get public IP addresses of AWS instances 
def publicIp_get(client,ins_ids):
    response = client.describe_instances(InstanceIds=ins_ids)

    return response['Reservations'][0]['Instances'][0]['PublicIpAddress']

# Stop AWS instances
# - input: ins_ids: list, the id of the instances to be stoped
# - output: status: dictionary, the id and the status
def stop_instances(client,ins_ids):
    response = client.stop_instances(
        InstanceIds=ins_ids
    )

    return None

# Clone AWS instances
def clone_instances(client, gNames, key_name, cloned_name, numOfIns, img_id):

    response = client.run_instances(
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/xvda',
                'VirtualName': 'Desktop',
                'Ebs': {
                    'DeleteOnTermination': True,
                    'VolumeSize': 8,
                    'VolumeType': 'gp2'
                },
            },
        ],
        ImageId=img_id,
        InstanceType='t2.micro',
        KeyName=key_name,
        MaxCount= numOfIns,
        MinCount=1,
        Monitoring={
            'Enabled':True
        },
        SecurityGroups=gNames,
        TagSpecifications= [
                    {
                        'ResourceType': 'instance',
                        'Tags':[{
                            'Key': 'Name',
                            'Value': cloned_name
                        }]
                    }
                ]
    )
    n = len(response['Instances'])
    ins_ids = []
    for i in range(n):
        ins_id = response['Instances'][i]['InstanceId']
        ins_ids.append(ins_id)
    return ins_ids

'''
import boto3 
import time

def main():
    client = boto3.client('ec2', region_name='us-east-1')

    gNames = ['cr01-sg']
    tags = [
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': 'test3'
                    }
                ]
            }
            ]

    numOfIns = 1
    ins_ids = create_instances(client, gNames, tags, numOfIns)

    # check the state whether is running
    print('Check the status:')
    for i in range(10):
        res = describe_instance_status(client,ins_ids)
        print(res)
        if res[ins_ids[0]] == 'running': break
        time.sleep(10)

    # stop the instance
    print('Stop the instance:')
    res = stop_instances(client,ins_ids)
    print(res)

main()
'''
