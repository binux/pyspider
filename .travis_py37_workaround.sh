# The MIT License (MIT)
#
# Copyright (c) 2018 Łukasz Langa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
echo "The ready-made virtualenv is not the one we want. Deactivating..."
deactivate

echo "Installing 3.7 from deadsnakes..."
sudo apt-get --yes install python3.7

echo "Creating a fresh virtualenv. We can't use `ensurepip` because Debian."
python3.7 -m venv ~/virtualenv/python3.7-deadsnakes --without-pip
source ~/virtualenv/python3.7-deadsnakes/bin/activate

echo "We ensure our own pip."
curl -sSL https://bootstrap.pypa.io/get-pip.py | python3.7

echo
echo "Python version:"
python3.7 -c "import sys; print(sys.version)"