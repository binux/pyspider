#!/usr/bin/env bash

# docker toolbox
# args:
# build, pull, push, list, run, stop, go

PROD_VERSION=`git rev-parse --short HEAD`
REGISTRY_TAG=harbor.lizc.in
PROD_GROUP=ops
PROD_NAME=pyspier
PROD_TAG=${REGISTRY_TAG}/${PROD_GROUP}/${PROD_NAME}:${PROD_VERSION}

echo "####################current product version ${PROD_TAG} ####################"

if [[ $1 = "run" ]]
then
    docker run --restart=always -itd --name ${PROD_TAG} -p 5000:5000 -p 23333:23333 -p 24444:24444 -p 25555:25555 ${PROD_TAG}
fi

if [[ $1 = "stop" ]]
then
    echo "####################docker stop####################"
    docker rm -f $(docker ps | grep ${PROD_TAG}| awk '{print $1}')
    echo "#################### $2 stop done##################"
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
    docker build -t ${PROD_TAG} .
    echo "####################docker build done####################"
    docker push ${PROD_TAG}
    echo "####################docker push done#####################"
fi

if [[ $1 = "build" ]]
then
    docker build -t ${PROD_TAG} .
    echo "####################docker build done####################"
fi

if [[ $1 = "push" ]]
then
    echo "####################pull ${PROD_TAG} ####################"
    docker push ${PROD_TAG}
    echo "####################pull done############################"
fi

if [[ $1 = "pull" ]]
then
    echo "####################pull ${PROD_TAG} ####################"
    docker pull ${PROD_TAG}
    echo "####################pull done############################"
fi