# AWS Delivery Pipeline

### Requirements
* SSH Access to Github or Bitbucket
* Configured integration between AWS CodeBuild and Github or Bitbucket

### Deploy this by using
* Clone this repo into a new `{your_project_name}` folder
* Remove `.git` folder and start a new repository with `git init`
* Create a new remote repo in Github or Bitbucket and add it remote repository locally
* Push all files to the new remote repo and get the HTTPS url `{your_repo_url}`
* Execute the following command

```
aws cloudformation create-stack --region {your_region} --stack-name {your_project_name}-builder --template-body file://builder/template.yml --capabilities CAPABILITY_IAM --parameters ParameterKey=Prefix,ParameterValue={your_project_name} ParameterKey=RepoUrl,ParameterValue={your_repo_url} ParameterKey=RepoType,ParameterValue={GITHUB|BITBUCKET}
```

### Once the builder is deployed
* Create a new branch from master called `feature/{your_feature_name}`
* Push this new feature branch and a new build in {your_project_name}-builder CodeBuild project should start.
* After a few minues a new CodePipeline should be up and running, deploying a disposable feature environment.