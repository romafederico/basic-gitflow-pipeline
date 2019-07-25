# AWS Delivery Pipeline

Deploy this by using 

* Clone this repo into a new {your_project_name} folder
* Remove `.git` folder and start a new repository with `git init`
* Push all files to the new repository and get the repo url
* Execute the following command

```
aws cloudformation create-stack --region {your_region} --stack-name {your_project_name}-builder --template-body file://builder/template.yml --capabilities CAPABILITY_IAM --parameters ParameterKey=Prefix,ParameterValue={your_project_name}
```