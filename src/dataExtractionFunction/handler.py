import json
import boto3
import botocore
import os

AWS_REGION = os.environ['AWS_DEFAULT_REGION']
PERMISSION_TABLE = os.environ['PERMISSION_TABLE_NAME']
USER_TABLE = os.environ['USER_TABLE_NAME']

ddb = boto3.resource('dynamodb')
iam = boto3.client('iam')

def handler(event, context):
    # Log the event argument for debugging and for use in local development.
    print(json.dumps(event))
    IDENTITY_STORE_ID = event['identityStoreId']
    INSTANCE_ARN = event['instanceArn']
    SSO_DEPLOYED_REGION = event['ssoDeployedRegion']
    
    sso = boto3.client('sso-admin', region_name=SSO_DEPLOYED_REGION)
    identitystore = boto3.client('identitystore', region_name=SSO_DEPLOYED_REGION)

    iam_permissions_table = ddb.Table(PERMISSION_TABLE)
    user_list_table = ddb.Table(USER_TABLE)

    permission_sets_response = sso.list_permission_sets(
        InstanceArn=INSTANCE_ARN
    )
    print(permission_sets_response)
    
    # loop through permission set to get list of group ID (to get sso group and users), policies, default versions (for json details)
    for item in permission_sets_response.get('PermissionSets'):
        # get list of accounts associated with permission set
        assoc_acc_response = sso.list_accounts_for_provisioned_permission_set(
            InstanceArn=INSTANCE_ARN,
            PermissionSetArn=item
            )
        
        describe_permission_set_response = sso.describe_permission_set(
            InstanceArn=INSTANCE_ARN,
            PermissionSetArn=item
            )

        # Define array to store Principal ID, Account ID and Principal Type
<<<<<<< HEAD:src/dataExtractionFunction/handler.py
<<<<<<< HEAD:src/dataExtractionFunction/handler.py
        principal_id_list=[]
        account_list=[]
        principal_type_list=[]
=======
        principalId_list=[]
        account_list=[]
        principalType_list=[]
>>>>>>> d782689 (Extract more data (principal type, group name, accountid, permission set name) and modifying logic to cover all edge cases in report generation):src/updateDbFunction/handler.py
=======
        principal_id_list=[]
        account_list=[]
        principal_type_list=[]
>>>>>>> 930df63 (fix variable naming convention):src/updateDbFunction/handler.py
        
        for account in assoc_acc_response.get('AccountIds'):
            # get the principal ID to link with the AWS IAM Identity Center group to get members
            account_assignments_response = sso.list_account_assignments(
                InstanceArn=INSTANCE_ARN,
                AccountId=account,
                PermissionSetArn=item
                )

            for group in account_assignments_response['AccountAssignments']:
                # build json
<<<<<<< HEAD:src/dataExtractionFunction/handler.py
<<<<<<< HEAD:src/dataExtractionFunction/handler.py
                principal_id_list.append(group['PrincipalId'])
                account_list.append(group['AccountId'])
                principal_type_list.append(group['PrincipalType'])
=======
                principalId_list.append(group['PrincipalId'])
                account_list.append(group['AccountId'])
                principalType_list.append(group['PrincipalType'])
>>>>>>> d782689 (Extract more data (principal type, group name, accountid, permission set name) and modifying logic to cover all edge cases in report generation):src/updateDbFunction/handler.py
=======
                principal_id_list.append(group['PrincipalId'])
                account_list.append(group['AccountId'])
                principal_type_list.append(group['PrincipalType'])
>>>>>>> 930df63 (fix variable naming convention):src/updateDbFunction/handler.py
                
        # get the list of managed policies attached in each of the permission set
        managed_policies_response = sso.list_managed_policies_in_permission_set(
            InstanceArn=INSTANCE_ARN,
            PermissionSetArn=item
            )
                
        managed_policies = []
        # loop through each policy arn to get version ID in order to list out json
        for i in managed_policies_response['AttachedManagedPolicies']:
            policy_details = iam.get_policy(
                PolicyArn=i['Arn']
                )
            defaultVersionId = policy_details['Policy']['DefaultVersionId']
            policy_json = iam.get_policy_version(
                PolicyArn=i['Arn'],
                VersionId=defaultVersionId
                )
            managed_policies.append({'policryArn': i['Arn'], 'policy_type': 'aws_managed', 'policyJson': json.dumps(policy_json['PolicyVersion']['Document'], default=str)})
        
        # get the inline policy attached in each of the permission set
        inline_policies_response = sso.get_inline_policy_for_permission_set(
            InstanceArn=INSTANCE_ARN,
            PermissionSetArn=item
            )

        # get the list of customer managed policy references attached in each of the permission set
        customer_policies_response = sso.list_customer_managed_policy_references_in_permission_set(
            InstanceArn=INSTANCE_ARN,
            PermissionSetArn=item
            )
        # print(customer_policies_response)

        # get the permission boundary attached in each of the permission set
        try: 
            permissions_boundary_response = sso.get_permissions_boundary_for_permission_set(
                InstanceArn=INSTANCE_ARN,
                PermissionSetArn=item
                )
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'ResourceNotFoundException':
                print('No Permission Boundary attached')
                permissions_boundary_response = {'PermissionsBoundary':''}
            else:
                raise error

        # store all in ddb table
        iam_permissions_table.put_item(
            TableName=PERMISSION_TABLE,
            Item={
                'id': INSTANCE_ARN,
                'permissionSetArn': item,
                'permissionSetName': describe_permission_set_response['PermissionSet']['Name'],
<<<<<<< HEAD:src/dataExtractionFunction/handler.py
<<<<<<< HEAD:src/dataExtractionFunction/handler.py
                'principalId': principal_id_list,
                'accountId': account_list,
                'principalType': principal_type_list,
=======
                'principalId': principalId_list,
                'accountId': account_list,
                'principalType': principalType_list,
>>>>>>> d782689 (Extract more data (principal type, group name, accountid, permission set name) and modifying logic to cover all edge cases in report generation):src/updateDbFunction/handler.py
=======
                'principalId': principal_id_list,
                'accountId': account_list,
                'principalType': principal_type_list,
>>>>>>> 930df63 (fix variable naming convention):src/updateDbFunction/handler.py
                'managedPolicies': managed_policies,
                'inlinePolicies': inline_policies_response['InlinePolicy'],
                'customerPolicies': customer_policies_response['CustomerManagedPolicyReferences'],
                'permissionsBoundary': permissions_boundary_response['PermissionsBoundary']
            })

    user_list_response = identitystore.list_users(
        IdentityStoreId=IDENTITY_STORE_ID
    )
    
    # loop through user lists to get the membership details (user Id, group ID in GroupMemberships details, user names etc)
    for user in user_list_response.get('Users'):
        # get member group (groupId) details
        user_group_membership_response = identitystore.list_group_memberships_for_member(
            IdentityStoreId=IDENTITY_STORE_ID,
            MemberId={
                'UserId': user['UserId']
            }
        )
<<<<<<< HEAD:src/dataExtractionFunction/handler.py
<<<<<<< HEAD:src/dataExtractionFunction/handler.py
        group_name_list=[]
=======
        groupName_list=[]
>>>>>>> d782689 (Extract more data (principal type, group name, accountid, permission set name) and modifying logic to cover all edge cases in report generation):src/updateDbFunction/handler.py
=======
        group_name_list=[]
>>>>>>> 930df63 (fix variable naming convention):src/updateDbFunction/handler.py
        for group in user_group_membership_response['GroupMemberships']:
            group_description_response = identitystore.describe_group(
                IdentityStoreId=IDENTITY_STORE_ID,
                GroupId=group['GroupId']
                )
<<<<<<< HEAD:src/dataExtractionFunction/handler.py
<<<<<<< HEAD:src/dataExtractionFunction/handler.py
            group_name_list.append(group_description_response['DisplayName'])
=======
            groupName_list.append(group_description_response['DisplayName'])
>>>>>>> d782689 (Extract more data (principal type, group name, accountid, permission set name) and modifying logic to cover all edge cases in report generation):src/updateDbFunction/handler.py
=======
            group_name_list.append(group_description_response['DisplayName'])
>>>>>>> 930df63 (fix variable naming convention):src/updateDbFunction/handler.py
        
        # store all in ddb table
        user_list_table.put_item(
            TableName=USER_TABLE,
            Item={
                'userId': user['UserId'],
                'userName': user['UserName'],
                'groupMemberships': user_group_membership_response['GroupMemberships'],
<<<<<<< HEAD:src/dataExtractionFunction/handler.py
<<<<<<< HEAD:src/dataExtractionFunction/handler.py
                'groupName': group_name_list
=======
                'groupName': groupName_list
>>>>>>> d782689 (Extract more data (principal type, group name, accountid, permission set name) and modifying logic to cover all edge cases in report generation):src/updateDbFunction/handler.py
=======
                'groupName': group_name_list
>>>>>>> 930df63 (fix variable naming convention):src/updateDbFunction/handler.py
            })
    
    return event