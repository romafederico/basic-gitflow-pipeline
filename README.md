# AWS Delivery Pipeline

Deploy this by using 


```
aws cloudformation create-stack --region {your_region} --stack-name dreamlab-builder --template-body file://codebuild/template.yml --capabilities CAPABILITY_IAM --parameters ParameterKey=BaseName,ParameterValue={your_project_name}
```