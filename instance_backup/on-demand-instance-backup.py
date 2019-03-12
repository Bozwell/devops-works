#!/usr/bin/python3
import boto3
from datetime import datetime
import time

regions = ['ap-northeast-1', 'ap-northeast-2','ap-southeast-1','us-west-1']
for region in regions:
    ec2_client = boto3.client('ec2', region_name=region)

    # describe instances
    desc_ins_res = ec2_client.describe_instances(
        Filters = [
            {
                "Name":"tag:is_bkup",
                "Values":["true"]
            },
            {
                "Name": "tag:is_spot",
                "Values": ["false"]
            },
        ]
    )

    for instances_obj in desc_ins_res['Reservations']:
        # print instances_obj
        for instance in instances_obj['Instances']:

            instance_name = ""

            for tag in instance['Tags']:
                if tag['Key'] == 'Name':
                    instance_name = tag['Value']
                    # break

            instance_id = instance['InstanceId']

            print(instance_name, instance_id)

            now = datetime.today().strftime("%Y%m%d%H%M%S")

            try:
                # create ami
                res = ec2_client.create_image(
                    InstanceId=instance_id,
                    Name=now + "-" + instance_name,
                    Description='scheduled backup',
                    NoReboot=True
                )
            except Exception as e:
                print(e)

            # print(res)

            time.sleep(1)



    # deleting old ami
    desc_img_res =  ec2_client.describe_images(
        # 아래의 AWS_OWNER_ID 본인의 ID로 대체한다.
        Owners=['AWS_OWNER_ID'],

        Filters = [
            {"Name":"description", "Values":["scheduled backup",]}
        ]
    )
    today = datetime.today()

    for image in desc_img_res['Images']:
        delta = today - datetime.strptime(image['Name'][0:14],"%Y%m%d%H%M%S")
        if delta.days > 7:

            ec2_client.deregister_image(
                ImageId = image['ImageId']
            )

            for blk in image['BlockDeviceMappings']:
                if 'Ebs' in blk:
                    ec2_client.delete_snapshot(
                        SnapshotId=blk['Ebs']['SnapshotId'])

            time.sleep(1)