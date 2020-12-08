
import boto3
import time
import sys

# Can be used to assign a default AWS owner id value if the program
# is only used by one user
OWNER_ID = '012345678900'

# Describe relevant properties of AWS instances in a client
# Return 2 lists containing instance ids and security group names
def describe(client):
    response = client.describe_instances(
        Filters=[
        {
            'Name': 'instance-state-name',
            'Values': [
                'running', 'stopped'
            ]
        },
    ],
    )
    ins_ids = []
    gNames = []
    for x in response['Reservations']:
        ins_ids.append(x['Instances'][0]['InstanceId'])
        gName = x['Instances'][0]['SecurityGroups'][0]['GroupName']
        if gName not in gNames:
            gNames.append(gName)
    return ins_ids,gNames

# Terminate the AWS instances identified in the 'ins_ids' list
def terminate_ins(client,ins_ids):
    response = client.terminate_instances(
        InstanceIds=ins_ids
    )
    for i in range(10):
        status = describe_instance_status(client,ins_ids)
        status = list(set(status))
        if len(status) == 1:
            if status[0] == 'terminated':
                print('Instances terminated!')
                break
        time.sleep(10)

# Delete the security group for an AWS client
def delete_SG(client,gName):
    response = client.delete_security_group(
        GroupName=gName
    )

# Describe the status of the AWS instances in the 'ins_ids' list
def describe_instance_status(client,ins_ids):
    response = client.describe_instance_status(
        InstanceIds=ins_ids,
        IncludeAllInstances=True
    )
    status = []

    for idx, value in enumerate(response['InstanceStatuses']):
        status.append(value['InstanceState']['Name'])
    return status

'''
def get_img_id(client,img_name)
    response = client.describe_images(
        Filters=[
        {
            'Name': 'name',
            'Values': [img_name]
        }
        ]
    )
    return response['Images'][0]['ImageId']
'''

# Delete all AWS images associated to an owner id 
def del_img(client,OwnerId):
    response = client.describe_images(
        Owners=[OwnerId]
    )
    for x in response['Images']:
        client.deregister_image(
            ImageId=x['ImageId']
        )

# Main function of the program
def main(argv):

    # Initialize with default value
    owner_id = OWNER_ID

    # Get owner id from the first command-line argument (if provided)
    if len(argv) >= 1:
        owner_id = argv[0]

    print('* Clean up the AWS cyber range...')
    client = boto3.client('ec2', region_name='us-east-1')
    ins_ids, gNames = describe(client)

    print('* Terminate instances...')
    terminate_ins(client, ins_ids)

    print('* Delete security groups...')
    for gName in gNames:
        delete_SG(client, gName)

    print('* Deregister AMIs...')
    del_img(client, owner_id)
    print('* AWS clean up completed.')

if __name__ == '__main__':
    main(sys.argv[1:])
