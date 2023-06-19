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

def query_ddb_to_populate_report(userName, PrincipalId, groupName, PrincipalType, iam_permissions_table, INSTANCE_ARN, writer):
    permission_response = iam_permissions_table.query(
        TableName=PERMISSION_TABLE,
        KeyConditionExpression="id = :id",
        FilterExpression= "contains(principalId, :pid)",
        ExpressionAttributeValues={
            ':id': INSTANCE_ARN,
            ':pid': PrincipalId
        }
        )

    print('Dynamodb query result for user:' + userName + ', group name:'+ groupName)
    print(permission_response)

    if permission_response.get('Count') == 0:
        writer.writerow([userName, PrincipalId, PrincipalType, groupName, 'not_assigned'])
    else:
        for permission in permission_response.get('Items'):
            print('Permissions for user:' + userName + ', group name:'+ groupName)
            print(permission)
            # Excel has a 32700 character limit
            if len(str(permission['inlinePolicies'])) > 32700:
                permission['inlinePolicies'] = 'Exceed character limit for excel, refer to AWS Console for full policy details'
            if len(str(permission['customerPolicies'])) > 32700:
                permission['customerPolicies'] = 'Exceed character limit for excel, refer to AWS Console for policy details'
            if len(str(permission['managedPolicies'])) > 32700:
                permission['managedPolicies'] = 'Exceed character limit for excel, refer to AWS Console for policy details'
                
            # Loop through all assignments of a permission set for individual users and groups
            for no_of_assignments, accountid in enumerate(permission['accountId']):
                if PrincipalType == 'USER' and permission['principalType'][no_of_assignments] == 'USER':
                    writer.writerow([userName, PrincipalId, permission['principalType'][no_of_assignments], groupName, permission['accountId'][no_of_assignments], permission['permissionSetArn'], permission['permissionSetName'], permission['inlinePolicies'], permission['customerPolicies'], permission['managedPolicies']])
                if PrincipalType == 'GROUP'and permission['principalType'][no_of_assignments] == 'GROUP':
                    writer.writerow([userName, PrincipalId, permission['principalType'][no_of_assignments], groupName, permission['accountId'][no_of_assignments], permission['permissionSetArn'], permission['permissionSetName'], permission['inlinePolicies'], permission['customerPolicies'], permission['managedPolicies']])
                    
                    
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
        writer.writerow(['User', 'PrincipalId', 'PrincipalType', 'GroupName', 'AccountIdAssignment', 'PermissionSetARN', 'PermissionSetName', 'Inline Policy', 'Customer Managed Policy','AWS Managed Policy'])
        
        for user in user_list_response.get('Items'):
            print('extracting user data')
            print(user)
            userId = user['userId']
            userName = user['userName']
            groupName = ''
       
            # Check individual user assignment first
            query_ddb_to_populate_report(userName, userId, groupName, 'USER', iam_permissions_table, INSTANCE_ARN, writer)

            # Check if user is in a group and group assignment 
            if user['groupMemberships']:
                for idx, group in enumerate(user['groupMemberships']):
                    groupId = group['GroupId']
                    groupName = user['groupName'][idx]
                    print('groupname is: ' + groupName)
                    query_ddb_to_populate_report(userName, groupId, groupName, 'GROUP', iam_permissions_table, INSTANCE_ARN, writer)
   
    s3.upload_file('/tmp/' + S3_UPLOAD_KEY, BUCKET_NAME, S3_UPLOAD_KEY)
    
    sns_message = "Analysis of users list with granted permission policies have been completed. \n Find out more from the report stored in the S3 bucket " + BUCKET_NAME + ", with the object key name: " + S3_UPLOAD_KEY
    sns.publish(
        TopicArn = SNS_ARN,
        Message = sns_message,
        Subject='AWS IAM Identity Center Policies Analyzer Report'
        )
        
    return {}