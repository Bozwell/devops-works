#-*- coding: utf-8 -*-
import boto3
import telegram
import operator
from datetime import datetime
import time
import json

''' 
    description : spot instance interruption발생시 최근 백업을 이용해서 인스턴스를 생성한다.
    date : 2018.12.05
    author : mordorkang@gmail.com
'''
# 아래의 TELEGRAM_TOKEN은 본인의 값을로 대체한다.
telegram_token = 'TELEGRAM_TOKEN'
bot = telegram.Bot(token=telegram_token)

ec2_client = boto3.client('ec2', region_name='ap-northeast-2')



'''
    instance_id로 instance_name을 가져온다.
'''
def get_instance_info(instance_id):
    desc_ins_res = ec2_client.describe_instances(
        InstanceIds=[
            instance_id
        ],
    )
    instance_name = ""
    for tag in desc_ins_res['Reservations'][0]['Instances'][0]['Tags']:
        if tag['Key'] == 'Name':
            instance_name =  tag['Value']



'''
    instance_name에 해당하는 최근 백업 AMI di를 가져온다.
'''
def get_recent_ami(instance_name):
    amis = {}
    desc_img_res = ec2_client.describe_images(
        # 아래의 AWS_OWNER_ID 본인의 ID로 대체한다.
        Owners=['AWS_OWNER_ID'],
        Filters=[
            {"Name": "description", "Values": ["spot_instance_backup"]},
        ]
    )

    for img in desc_img_res['Images']:
        if img['Name'].find(instance_name) != -1:
            amis[img['ImageId']] = img['CreationDate'][:10].replace('-', '')

    return max(amis.iteritems(), key=operator.itemgetter(1))[0]

# spot interruption을 체크한다.
response = ec2_client.describe_spot_instance_requests(
    Filters=[
        {
            'Name': 'state',
            'Values': [
                'open',
            ]
        },
    ],
)

if len(response['SpotInstanceRequests']) > 0:

    today = datetime.today()

    # spot instance 생성중에 발생한 이벤트인지 검사한다.
    for ins in response['SpotInstanceRequests']:
        delta = today - datetime.strptime(ins['CreateTime'][:19],"%Y-%m-%d %H:%M:%S")

        # 스팟인스턴스 생성시간(CreateTime)이 현재시간의 차이(delta)가 300초 초과이면 발생한 이벤트가 spot interruption이라고 판단한다.
        if delta.seconds > 300:
            #텔레그램으로 알람
            bot.sendMessage(chat_id='CHAT_ID', text='Spot Instance Interruption Occur!')


            # 백업본이 있는지 알아본다.
            # instance_id로 name을 가져오고 name으로 최근백업 AMI id를 가져온다.
            instance_name = get_instance_info(ins['InstanceId'])
            ami_id = get_recent_ami(instance_name)


            #최신백업본이 존재하는경우 spot request를 취소하고 새로운 스팟인스턴스를 만든다.
            if ami_id != None:
                #기존 인스턴스에 할당된 elaticIp정보를 가져온다.
                desc_ip_res = ec2_client.describe_addresses(
                    Filters=[
                        {
                            'Name': 'instance-id',
                            'Values': [
                                ins['InstanceId'],
                            ]
                        },
                    ],
                )

                public_ip = desc_ip_res['Addresses'][0]['PublicIp']
                allocation_id =  desc_ip_res['Addresses'][0]['AssociationId']

                #기존인스턴스의 태그정보를 가져온다.
                desc_ins_res = ec2_client.describe_instances(
                    InstanceIds=[
                        ins['InstanceId']
                    ],
                )
                tags = desc_ins_res['Reservations'][0]['Instances'][0]['Tags']
                print json.dumps(tags, indent=4, sort_keys=True, default=str)


                # 스팟 리퀘스트를 취소한다.
                cancel_res = ec2_client.cancel_spot_instance_requests(
                    SpotInstanceRequestIds=[
                        ins['SpotInstanceRequestId']
                                            ]
                )


                # 스팟인스턴스 가격을 가져온다.
                sph_res = ec2_client.describe_spot_price_history(
                    Filters=[
                        {
                            'Name': 'product-description',
                            'Values': [
                                ins['ProductDescription'],
                            ]
                        },
                    ],
                    AvailabilityZone=ins['LaunchedAvailabilityZone'],
                    InstanceTypes=[
                        ins['LaunchSpecification']['InstanceType']
                    ],

                )

                spot_price = sph_res['SpotPriceHistory'][0]['SpotPrice']

                # spot 인스턴스를 생성한다.
                spot_create_res = ec2_client.request_spot_instances(

                    InstanceCount=1,
                    LaunchSpecification={
                        'SecurityGroupIds': [sg.get('GroupId') for sg in ins['LaunchSpecification']['SecurityGroups']],
                        'ImageId': ami_id,
                        'InstanceType': ins['LaunchSpecification']['InstanceType'],
                        'KeyName': ins['LaunchSpecification']['KeyName'],
                        'SubnetId': ins['LaunchSpecification']['SubnetId'],
                    },
                    SpotPrice=spot_price,
                    Type='persistent',
                    InstanceInterruptionBehavior='stop'
                )

                spot_req_id = spot_create_res['SpotInstanceRequests'][0]['SpotInstanceRequestId']
                print "spot_req_id : {}".format(spot_req_id)

                time.sleep(30)

                desc_spot_res = ec2_client.describe_spot_instance_requests(SpotInstanceRequestIds=[spot_req_id])

                instance_id = desc_spot_res['SpotInstanceRequests'][0]['InstanceId']
                print "instance_id : {}".format(instance_id)



                #기존 인스턴스 가지고 있던 IP를 할당한다.
                response = ec2_client.associate_address(
                    AllocationId=allocation_id,
                    InstanceId=instance_id,
                )

                ec2_client.create_tags(
                    Resources=[instance_id],
                    Tags=[tags]
                )

                # 인스턴스가 생성되었음을 알린다.
                bot.sendMessage(chat_id='CHAT_ID', text='Spot instance renew : {}'.format(spot_create_res['SpotInstanceRequests'][0]['InstanceId']))




