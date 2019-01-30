#!/usr/bin/env bash

# docker toolbox
# args:
# build, pull, push, list, run, stop, go
PROD_VERSION=`git rev-parse --short HEAD`
REGISTRY_TAG=harbor.lizc.in
PROD_GROUP=ops
PROD_NAME=pyspier
PRO_TAG=${REGISTRY_TAG}/${PROD_GROUP}/${PROD_NAME}:${PROD_VERSION}

echo "####################current product version ${PRO_TAG} ####################"

#if [ $1 = "run" ]
#then
#    if [ -n "$3" ]; then
#        PORT=$3
#    fi
#    if [ -n "$4" ]; then
#        WORKERS=$4
#    fi
#    MEMORY=$[WORKERS*10]
#    docker run --restart=always -itd -v '/data/litnav/datas:/opt/litnav/datas' -v '/data/litnav/csv:/opt/litnav/csv' -e "WORKERS=${WORKERS}" -e "ENV=$2" -e "PYTHONPATH=/opt/litnav" --memory=${MEMORY}G --name nav.$2.${PORT} -p ${PORT}:10002 ${PRO_TAG}
#fi

#if [ $1 = "stop" ]
#then
#    echo "####################docker stop####################"
#    if [ $2 = "all" ]
#    then
#        docker rm -f $(docker ps | grep nav| awk '{print $1}')
#    else
#        docker rm -f $(docker ps | grep nav_$2| awk '{print $1}')
#    fi
#    echo "#################### $2 stop done####################"
#fi

if [[ $1 = "list" ]]
then
    echo "####################docker list####################"
    if [[ $2 = "all" ]]
    then
        docker ps -a | grep ${PROD_NAME}
    else
        docker ps -a | grep ${PROD_NAME}:${PROD_VERSION}
    fi
fi

if [[ $1 = "go" ]]
then
    docker build -t ${PRO_TAG} .
    echo "####################docker build done####################"
    docker push ${PRO_TAG}
    echo "####################docker push done####################"
fi

if [[ $1 = "build" ]]
then
    docker build -t ${PRO_TAG} .
    echo "####################docker build done####################"
fi

if [[ $1 = "push" ]]
then
    echo "####################pull ${PRO_TAG} ####################"
    docker push ${PRO_TAG}
    echo "####################pull done####################"
fi


if [[ $1 = "pull" ]]
then
    echo "####################pull ${PRO_TAG} ####################"
    docker pull ${PRO_TAG}
    echo "####################pull done####################"
fi