
# Edit the tags of an AWS client
def edit_tags(client, ins_id, v):
# ins_id : string
# v: string
    response = client.create_tags(
        Resources=[ins_id],
        Tags=[
            {
                'Key': 'Name',
                'Value': v
            },
        ]
    )
    return response

# Get info about the instances in an AWS client
def get_info(client):
    response = client.describe_instances()

    m = len(response['Reservations'])

    lst = []

    for i in range(m):
        n = len(response['Reservations'][i]['Instances'])
        for j in range(n):
            dic = {}
            if 'PublicIpAddress' in response['Reservations'][i]['Instances'][j]:

                dic['Id'] = response['Reservations'][i]['Instances'][j]['InstanceId']
                dic['IpAddress'] = response['Reservations'][i]['Instances'][j]['PublicIpAddress']
                dic['status'] = response['Reservations'][i]['Instances'][j]['State']['Name']
                dic['tags'] = response['Reservations'][i]['Instances'][j]['Tags']
                lst.append(dic)
    return lst
