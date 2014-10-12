#!/bin/sh

cd $(dirname $0)
TEST_MYSQL=1 TEST_RABBITMQ=1 TEST_MONGODB=1 python -m unittest discover -s test -p "test_*.py"
