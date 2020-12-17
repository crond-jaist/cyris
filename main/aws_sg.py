
# Create an AWS security group
def create_security_group(client,gName):
# input: gName: string
# output:
    groupId = client.create_security_group(
        Description='SG for SSH-access',
        GroupName=gName
    )
    return groupId

'''
# example
import boto3
client = boto3.client('ec2', region_name='us-east-1')
gName = 'cr01-sg'
s = create_security_group(client, gName)
print(s)
'''

# Authorize the security group for an AWS client ingress
def edit_ingress(client, gName):
    response = client.authorize_security_group_ingress(
        CidrIp='0.0.0.0/0',
        FromPort=22,
        GroupName=gName,
        IpProtocol='tcp',
        ToPort=22
        )
    return response

'''
# example:
import boto3
client = boto3.client('ec2', region_name='us-east-1')
gName = 'cr01-sg'
s = edit_ingress(client, gName)
print(s)
'''

# Describe the security groups for an AWS client
def describe_security_groups(client, gNames):
    response = client.describe_security_groups(
         GroupNames=gNames
    )
    # GroupID = []
    #  GroupID.append(response['SecurityGroups'][0]['GroupId'])
    return response

'''
# example:
import boto3
gNames = ['cr01-sg']
client = boto3.client('ec2', region_name='us-east-1')
r = describe_security_groups(client, gNames)
print(r)
'''
