#!/usr/bin/python

import boto3
import time
import sys

# Can be used to assign a default AWS account ID if the program
# is only used by one user
AWS_ACCOUNT_ID = '123456789012'

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
    ins_ids = {}
    gNames = []
    ins_names = {}
    for x in response['Reservations']:
        ins_ids.update({x['Instances'][0]['Tags'][0]['Value']: x['Instances'][0]['InstanceId']})
        ins_names.update({x['Instances'][0]['Tags'][0]['Value']: x['Instances'][0]['ImageId']})
        gName = x['Instances'][0]['SecurityGroups'][0]['GroupName']
        if gName not in gNames:
            gNames.append(gName)
    return ins_ids,gNames,ins_names

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
def del_img(client,OwnerId,Image_ID):
    response = client.describe_images(
        Owners=[OwnerId]
    )
    for x in response['Images']:
        for i in Image_ID:
            if i == str(x['ImageId']):
                client.deregister_image(
                    ImageId=x['ImageId']
                )

# Main function of the program
def main(argv):

    # Initialize the AWS account ID with a default value
    aws_account_id = AWS_ACCOUNT_ID
    image_names = []
    image_id = []
    security_name = []
    ins_list = []

    # Get the AWS account ID from the first command-line argument (if provided)
    if len(argv) >= 1:
        aws_account_id = argv[0]
        for input_name in argv[1:]:
            image_names.append('cr' + input_name)
            security_name.append('cr' + input_name + '-sg' )

    print('* Clean up the AWS cyber range...')
    client = boto3.client('ec2', region_name='us-east-1')
    ins_ids, gNames, ins_names = describe(client)
    # Build list of related AMI ids
    for i in ins_names.items():
        for j in image_names:
            if j in i[0]:
                image_id.append(i[1])

    print('* Terminate instances...')
    for ins in ins_ids.items():
        for i in image_names:
            if i in ins[0]:
                ins_list.append(ins[1])
    #print(ins_list)
    terminate_ins(client, ins_list)

    print('* Delete security groups...')
    for gName in gNames:
        if gName in security_name:
            #print(gName)
            delete_SG(client, gName)

    print('* Deregister AMIs...')
    #print(image_id)
    del_img(client, aws_account_id, image_id)
    print('* AWS clean up completed.')

if __name__ == '__main__':
    main(sys.argv[1:])
