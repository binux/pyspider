#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
cd ${dir}
echo ">> enter into $(pwd)"

REGISTRY_TAG=harbor.lizc.in
PROD_GROUP=ops
PROD_NAME=pyspier
PROD_TAG=${REGISTRY_TAG}/${PROD_GROUP}/${PROD_NAME}:base

cp ../requirements.txt requirements.txt
docker build -t ${PROD_TAG} .
docker push ${PROD_TAG}

rm requirements.txt