# AWS SSO Permission Policies Analyzer

This solution 

AWS Services used
- Application Composer - to generate baseline template and resources
- Amazon EventBridge
- AWS Step Functions
- AWS Lambda
- Amazon DynamoDB
- Amazon S3

## To deploy
- Clone a copy of your

## Default Specifications
### Amazon EventBridge Schedule
- Cron schedule is at 1st day of each month 0800 UTC +8. Update your preferred schedule and timezone accordingly
#### To update / configure
- Go to Console > Amazon EventBridge > Schedules > Select generated schedule resources (name with 'YOUR_STACK_NAME--monthlySchedule-XXXXXXXXX') > Click `Edit` > Under `Schedule pattern` segment, update your preferred scheduling.

### Analyzed SSO account
#### To update / configure
- Update the account details and SSO instance you would like to.
- Go to Console > Amazon EventBridge > Schedules > Scroll down and Click `Next` > Under `StartExecution` segment in 'Input' box, use the following format to update the pattern. The format and keyword has to be followed to allow Lambda function to execute successfully. (Or update in Lambda function to retrieve your own event pattern)
```
{
  "identityStoreId": "d-xxxxxxxxxx",
  "instanceArn": "arn:aws:sso:::instance/ssoins-xxxxxxxxxx",
  "accountId": [
    "xxxxxxxxxx",
    "xxxxxxxxxx",
    "xxxxxxxxxx",
    "xxxxxxxxxx",
    "xxxxxxxxxx"
  ],
  "ssoDeployedRegion": "YOUR_SSO_DEPLOYED_REGION" (example: us-east-1)
}
```