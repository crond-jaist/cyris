
# Create a new AWS image
def create_img(client, ins_id, name, des='New image created from the previous_instance(BaseVM)'):

    response = client.create_image(
        Description=des,
        InstanceId=ins_id,
        Name=name,
        #NoReboot=True|False
    )
    img_id = response['ImageId']
    return img_id


# Get AWS image description
def describe_image(client, img_id):
    response = client.describe_images(
        ImageIds=[
            img_id,
        ]
    )
    state = response['Images'][0]['State']
    return state
