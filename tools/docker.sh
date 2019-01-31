#!/usr/bin/env bash

# docker toolbox
# args:
# build, pull, push, list, run, stop, go

PROD_VERSION=`git rev-parse --short HEAD`
REGISTRY_TAG=harbor.lizc.in
PROD_GROUP=ops
PROD_NAME=pyspier
PROD_TAG=${REGISTRY_TAG}/${PROD_GROUP}/${PROD_NAME}:${PROD_VERSION}

echo "#################### Current Product Version: ${PROD_TAG} ####################"

if [[ $1 = "run" ]]
then
    echo "#################### Docker Run ####################"
    docker run --restart=always -itd --name ${PROD_VERSION} -p 5000:5000 -p 23333:23333 -p 24444:24444 -p 25555:25555 ${PROD_TAG}
fi

if [[ $1 = "stop" ]]
then
    echo "#################### Docker Stop ####################"
    running_container_name=`docker ps | grep ${PROD_TAG}| awk '{print $1}'`
    docker stop ${running_container_name}
    if [[ $2 = "f" ]]
    then
        docker rm -f ${running_container_name}
    fi
fi

if [[ $1 = "list" ]]
then
    if [[ $2 = "all" ]]
    then
        docker ps -a | grep ${PROD_NAME}
    else
        docker ps -a | grep ${PROD_NAME}:${PROD_VERSION}
    fi
fi

if [[ $1 = "go" ]]
then
    echo "#################### Build ${PROD_TAG} ####################"
    docker build -t ${PROD_TAG} .
    echo "#################### Pull ${PROD_TAG} ####################"
    docker push ${PROD_TAG}
fi

if [[ $1 = "build" ]]
then
    echo "#################### Build ${PROD_TAG} ####################"
    docker build -t ${PROD_TAG} .
fi

if [[ $1 = "push" ]]
then
    echo "#################### Pull ${PROD_TAG} ####################"
    docker push ${PROD_TAG}
fi

if [[ $1 = "pull" ]]
then
    echo "#################### Pull ${PROD_TAG} ####################"
    docker pull ${PROD_TAG}
fi

echo "#################### DONE. ####################"