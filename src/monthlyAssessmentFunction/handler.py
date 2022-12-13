import json
import boto3
import os
from datetime import date
import csv

PERMISSION_TABLE = os.environ['PERMISSION_TABLE_NAME']
USER_TABLE = os.environ['USER_TABLE_NAME']
SNS_ARN = os.environ['TOPIC_ARN']
BUCKET_NAME = os.environ['BUCKET_NAME']

ddb = boto3.resource('dynamodb')
iam = boto3.client('iam')
sns = boto3.client('sns')
s3 = boto3.client('s3')

def handler(event, context):
    # Log the event argument for debugging and for use in local development.
    print(json.dumps(event))
    payload = event['Payload']
    INSTANCE_ARN = payload['instanceArn']
    today = date.today()
    curr_date = today.strftime("%m%d%y")
    S3_UPLOAD_KEY = curr_date + 'result.csv'
    
    iam_permissions_table = ddb.Table(PERMISSION_TABLE)
    user_list_table = ddb.Table(USER_TABLE)
    
    user_list_response = user_list_table.scan(
        TableName=USER_TABLE
        )

    with open('/tmp/' + curr_date + 'result.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['User', 'GroupIds', 'Permission Sets', 'Inline Policy', 'AWS Managed Policy', 'Customer Managed Policy'])
        
        # For logging purpose only
        a=1
        for user in user_list_response.get('Items'):
            userId = user['userId']
            userName = user['userName']
            # For logging purpose only
            a=a+1
            g=1
            for group in user['groupMemberships']:
                groupId = group['GroupId']
                # For logging purpose only
                g=g+1
                # For logging purpose only
                print('user: ' + str(a-1) + ' with name: ' + userName + ', ' + 'group No: ' + str(g-1) + ' with group ID: ' + groupId + '\n')
                permission_response = iam_permissions_table.query(
                    TableName=PERMISSION_TABLE,
                    KeyConditionExpression="id = :id",
                    FilterExpression= "contains(groupId, :gid)",
                    ExpressionAttributeValues={
                        ':id': INSTANCE_ARN,
                        ':gid': groupId
                    }
                    )
                # print(permission_response)
                if permission_response.get('Count') == 0:
                    writer.writerow([userName, groupId, '', '', '', ''])
                else:
                    for permission in permission_response.get('Items'):
                        # print(permission)
                        writer.writerow([userName, groupId, permission['permissionSetArn'], permission['inlinePolicies'], permission['managedPolicies'], permission['customerPolicies']])

    s3.upload_file('/tmp/' + S3_UPLOAD_KEY, BUCKET_NAME, S3_UPLOAD_KEY)
    
    # For logging purpose only
    # print("before printing table\n")
    # with open('/tmp/' + S3_UPLOAD_KEY, 'r+') as f:
    #     reader = csv.reader(f)
    #     for row in reader:
    #         print(row)
    
    sns_message = "Analysis of users list with granted permission policies have been completed. \n Find out more from the report stored in the S3 bucket " + BUCKET_NAME + ", with the object key name: " + S3_UPLOAD_KEY
    sns.publish(
        TopicArn = SNS_ARN,
        Message = sns_message,
        Subject='SSO IAM Analyzer Report'
        )
        
    return {}