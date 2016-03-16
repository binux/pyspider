#   Copyright (c) 2006-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#   Origin: https://code.google.com/p/wsgi-xmlrpc/

import unittest2 as unittest
import tornado.wsgi
import tornado.ioloop
import tornado.httpserver
from pyspider.libs import utils

class TestXMLRPCServer(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        from pyspider.libs import wsgi_xmlrpc
        
        def test_1():
            return 'test_1'
            
        class Test2(object):
            def test_3(self, obj):
                return obj
                
        test = Test2()
        
        application = wsgi_xmlrpc.WSGIXMLRPCApplication()
        application.register_instance(Test2())
        application.register_function(test_1)

        container = tornado.wsgi.WSGIContainer(application)
        self.io_loop = tornado.ioloop.IOLoop.current()
        http_server = tornado.httpserver.HTTPServer(container, io_loop=self.io_loop)
        http_server.listen(3423)
        self.thread = utils.run_in_thread(self.io_loop.start)

    @classmethod
    def tearDownClass(self):
        self.io_loop.add_callback(self.io_loop.stop)
        self.thread.join()
    
    def test_xmlrpc_server(self, uri='http://127.0.0.1:3423'):
        from six.moves.xmlrpc_client import ServerProxy
        
        client = ServerProxy(uri)
        
        assert client.test_1() == 'test_1'
        assert client.test_3({'asdf':4}) == {'asdf':4}
