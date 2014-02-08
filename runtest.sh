#!/bin/sh

cd $(dirname $0)
python -m test.test_database_sqlite
