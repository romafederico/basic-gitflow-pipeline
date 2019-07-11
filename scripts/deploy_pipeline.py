import boto3
import hashlib
import json
import os
import time


def parse_template(template):
    """
    Imports template file from pipeline folder and 
    parses it as a string
    """
    with open(template) as template_fileobj:
        template_data = template_fileobj.read()
    cloudformation.validate_template(TemplateBody=template_data)
    return template_data

def cleanup_feature_env(env_hash, pipeline_config):
    """
    Removes all infrastructure for a specific feature
    by deleting all cloudformation stacks that have the env_hash identifier
    in its name. Feature pipeline stack is ignored at first and removed last
    since it has the role to create, update and delete all other stacks.
    Cloudformation and S3 clients is initialized internally 
    to use the feature environment region and avoid conflicts with the "parent" 
    clients. 
    """
    _cloudformation = boto3.client('cloudformation', region_name=pipeline_config['feature']['region'])
    _dynamodb = boto3.client('dynamodb', region_name=pipeline_config['feature']['region'])
    _available_stacks = _cloudformation.describe_stacks()
    _available_tables = _dynamodb.list_tables()
    _s3 = boto3.resource('s3')


    for item in _available_tables['TableNames']:
        try:
            if env_hash in item:
                _dynamodb.delete_table(
                    TableName=item
                )
        except Exception as e:
            print(e)

    for item in _available_stacks['Stacks']:
        if env_hash in item['StackName'] and f"{env_hash}-pipeline" not in item['StackName']:
            try:
                print(f"CLEANING UP {item['StackName']}")
                _cloudformation.delete_stack(
                    StackName=item['StackName']
                )
            except Exception as e:
                print(e)

            stack_deleted = False
            while stack_deleted == False:
                time.sleep(5)
                stack_details = _cloudformation.describe_stacks(
                    StackName=item['StackId']
                )
                stack_status = stack_details['Stacks'][0]['StackStatus']
                print(stack_status)

                if stack_status == "DELETE_FAILED":
                    print("STACK FAILED TO DELETE. Exiting now.")
                    quit()

                if stack_status == "DELETE_COMPLETE":
                    print("STACK DELETED. Exiting now.")
                    stack_deleted = True
                    
        if item["StackName"] == f"{base_name}-{env_hash}-pipeline":
            pipeline_stack = item
    
    if pipeline_stack:
        try:
            print(f"CLEANING UP {pipeline_stack['StackName']}")
            source_bucket = _s3.Bucket(f"{base_name}-{env_hash}-source")
            artifact_bucket = _s3.Bucket(f"{base_name}-{env_hash}-artifact")        
            if source_bucket in _s3.buckets.all(): source_bucket.object_versions.all().delete()
            if artifact_bucket in _s3.buckets.all(): artifact_bucket.object_versions.all().delete()
            _cloudformation.delete_stack(
                StackName=pipeline_stack['StackName']
            )
        except Exception as e:
            print(e)

    
# Takes environment variables defined in parent process (see codebuild/buildspec.yml)
base_name = os.environ['BASE_NAME']
env_hash = os.environ['ENV_HASH']
env_name = os.environ['ENV_NAME']


# Imports pipeline configuration file for both environment types
with open(f"config/pipeline.json", "r") as config_file:
    pipeline_config = json.load(config_file,)


# Initializes boto3 cloudformation client using parameters from the previously imported file
cloudformation = boto3.client('cloudformation', region_name=pipeline_config[env_name]['region'])


# Defines parameters according to environment type 
# Checks the existence of current feature environments
# If this is a master environment it will attempt to remove the feature environment from which PULL REQUEST comes from
try:
    available_stacks = cloudformation.describe_stacks()
except Exception as e:
    print(e)
    quit()

existing_stack = False

use_hash = True if "use_hash" in pipeline_config[env_name] else False

stack_name = "{}-{}-pipeline".format(base_name, env_hash if use_hash else env_name) 
stack_params = [
    {
        "ParameterKey": "BaseName",
        "ParameterValue": base_name
    },
    {
        "ParameterKey": "EnvName",
        "ParameterValue": env_hash if use_hash else env_name
    }
]
for item in available_stacks['Stacks']:
    if stack_name == item['StackName']:
        existing_stack = True

if "force_feature_cleanup" in pipeline_config[env_name]:
    cleanup_feature_env(env_hash, pipeline_config)


# Creates or updates the pipeline stack depending on its existence
template_data = parse_template("pipeline/template.yml")
if not existing_stack:
    print(f"CREATING STACK {stack_name}")
    try:
        stack = cloudformation.create_stack(
            StackName=stack_name,
            TemplateBody=template_data,
            Parameters=stack_params,
            Capabilities=["CAPABILITY_NAMED_IAM",]
        )
    except Exception as e:
        print(e)
        quit()
else:
    print(f"UPDATING STACK {stack_name}")
    try:
        stack = cloudformation.update_stack(
            StackName=stack_name,
            TemplateBody=template_data,
            Parameters=stack_params,
            Capabilities=["CAPABILITY_NAMED_IAM",]
        )
    except Exception as e:
        print(e)
        quit()
        

# Checks stack creation or update progress
deploy_finished = False
while deploy_finished == False:
    time.sleep(5)
    stack_details = cloudformation.describe_stacks(
        StackName=stack['StackId']
    )
    stack_status = stack_details['Stacks'][0]['StackStatus']
    print(stack_status)

    if stack_status == "DELETE_COMPLETE":
        print("STACK DELETED. Exiting now.")
        quit()

    if stack_status == "ROLLBACK_COMPLETE" or stack_status == "UPDATE_ROLLBACK_COMPLETE" or stack_status == 'ROLLBACK_FAILED':
        print(f"{stack_status}. Stack failed to create, proceeding to DELETE.")
        cloudformation.delete_stack(
            StackName=stack['StackId']
        )

    if stack_status == "CREATE_COMPLETE" or stack_status == "UPDATE_COMPLETE":
        deploy_finished = True