#!/bin/bash

export ENV_HASH=$(echo $CODEBUILD_WEBHOOK_HEAD_REF | md5sum|awk '{print $1}')

# Defines environment type. FEATURE, DEVELOP, MASTER
if [ $CODEBUILD_WEBHOOK_EVENT = "PULL_REQUEST_MERGED" ]; then
    export ENV_NAME="develop"
fi

if [ $CODEBUILD_WEBHOOK_EVENT = "PUSH" ]; then
    export ENV_NAME=$(echo $CODEBUILD_WEBHOOK_HEAD_REF | cut -f3 -d"/")
    if [ $ENV_NAME = "release" ]; then export ENV_NAME="staging"; fi
    if [ $ENV_NAME = "master" ]; then export ENV_NAME="production"; fi
fi

#  Defines source bucket names for all environments types
if [ $ENV_NAME = "feature" ]; then 
    export SOURCE_BUCKET="feature-source-$ENV_HASH"
else
    export SOURCE_BUCKET="$BASE_NAME-$ENV_NAME-source"
fi
