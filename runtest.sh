#!/bin/sh

cd $(dirname $0)
python -m unittest discover -s test -p "test_*.py"
