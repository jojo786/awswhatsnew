# awswhatsnew

![Pipeline workflow](https://github.com/jojo786/awswhatsnew/actions/workflows/pipeline.yaml/badge.svg)


Publish AWS News, filtered for the Africa (Cape Town) region, to Slack (and Twitter) by reading the official RSS feed with AWS Lambda. 
It posts to [AWS Community Africa](https://awscommunityafrica.slack.com/) using Slack App `AWSWhatsNew`.

## Details

- to create a Slack app, follow the four steps listed under [Add a Bot User](https://slack.com/help/articles/115005265703-Create-a-bot-for-your-workspace)
- Get your Bot User OAuth Token from the [Slack APP API](https://api.slack.com/apps/) under OAuth and Permissions, then add it to SSM 
- reads Slack credentials from AWS SSM.
- sets Slack icon emoji - needs [chat:write.customize](https://api.slack.com/scopes/chat:write.customize) OAuth Scope
- python dependencies listed in [`requirements.txt`](requirements.txt)
- Infrastructure defined in CloudFormation in [`template.yml`](template.yml)
- Local testing via Docker and [SAM Local](http://docs.aws.amazon.com/lambda/latest/dg/test-sam-local.html#sam-cli-simple-app)
- Packaging and Deployment done via SAM CLI, using `sam build --use-container` (due to this [bug](https://github.com/aws/aws-sam-cli/issues/2291)) and `sam deploy`
