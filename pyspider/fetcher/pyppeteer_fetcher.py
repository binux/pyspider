import json
import datetime
import asyncio
import tornado.web
import tornado.httpclient
from tornado.ioloop import IOLoop
from tornado.platform.asyncio import AsyncIOMainLoop
import traceback
import re,os
from tornado.httputil import HTTPHeaders
from urllib.parse import urlparse,urlunparse
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    AsyncIOMainLoop().install()
except:
    pass
import logging
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S',level=logging.INFO)

def patch_pyppeteer():
    import websockets
    import pyppeteer
    if float(websockets.__version__) > 6.0:
        original_method = pyppeteer.connection.websockets.client.connect

        def new_method(*args, **kwargs):
            kwargs['ping_interval'] = None
            kwargs['ping_timeout'] = None
            return original_method(*args, **kwargs)
        pyppeteer.connection.websockets.client.connect = new_method
patch_pyppeteer()
import pyppeteer

class Application(tornado.web.Application):
    def __init__(self):
        self.pages = 0
        tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
        self.http_client = tornado.httpclient.AsyncHTTPClient(max_clients=100)
        handlers = [
            (r"/", PostHandler),
        ]
        super(Application, self).__init__(handlers, settings = {"debug": False,"autoreload": False,})
    def init_browser(self, loop):
       self.browser = loop.run_until_complete(run_browser())

async def run_browser():
    browser_settings = {}
    browser_settings["headless"] = False
    browser_settings['devtools'] = True
    browser_settings['autoClose'] = True
    browser_settings['ignoreHTTPSErrors'] = True
    if env == "production":
        browser_settings['executablePath'] = '/usr/bin/google-chrome-stable'
        browser_settings["headless"] = True
    browser_settings["args"] = ['--no-sandbox', "--disable-setuid-sandbox","--disable-gpu"];
    browser =  await pyppeteer.launch(browser_settings)
    return browser

def _parse_cookie(cookie_list):
    if cookie_list:
        cookie_dict = dict()
        for item in cookie_list:
            cookie_dict[item['name']] = item['value']
        return cookie_dict
    return {}

class PostHandler(tornado.web.RequestHandler):
    async def request_check(self,req,fetch):
        proxy = fetch.get('proxy', None)
        if req.resourceType == 'image':
            await req.abort()
        else:
            if proxy:
                timeout = fetch.get('timeout', 10)
                connect_timeout = fetch.get('connect_timeout', 10)
                method=req.method
                headers= req.headers
                body= req.postData
                regex = re.compile("^http://|^https://|^socks5://")
                proxy_host, proxy_port = regex.sub('', proxy).split(":")
                try:
                    t_response = await self.application.http_client.\
                        fetch(req.url, method = method,body=body,request_timeout=timeout,proxy_host=proxy_host,proxy_port=int(proxy_port),
                              connect_timeout=connect_timeout,headers=headers,validate_cert=False)
                except Exception as e:
                    await req.respond({"body":str(e)})
                    logging.exception(e)
                    raise
                p_response = {}
                p_response['status'] = t_response.code
                p_response['headers'] = t_response.headers
                p_response['contentType'] = t_response.headers['Content-Type']
                p_response['body'] = t_response.body
                await req.respond(p_response)
            else:
                await req.continue_()
    async def _fetch(self,fetch,page):
        result = {'orig_url': fetch['url'],
                  'status_code': 200,
                  'error': '',
                  'content': '',
                  'headers': {},
                  'url': '',
                  'cookies': {},
                  'time': 0,
                  'js_script_result': '',
                  'save': '' if fetch.get('save') is None else fetch.get('save')
                  }
        try:
            start_time = datetime.datetime.now()
            await page.evaluateOnNewDocument('''() => {
                  Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                  });
                }''')
            await page.setExtraHTTPHeaders(fetch['headers'])
            await page.setUserAgent(fetch['headers']['User-Agent'])
            page_settings = {}
            page_settings["waitUntil"] = ["domcontentloaded","networkidle0"]
            page_settings["timeout"] = fetch.get('timeout',10) * 1000
            await page.setRequestInterception(True)
            page.on('request',lambda req:asyncio.ensure_future(self.request_check(req,fetch)))
            response = await page.goto(fetch['url'], page_settings)

            #response.text 会强制用utf8解码
            result['content'] = await response.text()
            result['url'] = page.url
            result['status_code'] = response.status
            result['cookies'] = _parse_cookie(await page.cookies())
            result['headers'] = response.headers
            end_time = datetime.datetime.now()
            result['time'] = (end_time - start_time).total_seconds()
        except Exception as e:
            result['error'] = str(e)
            result['status_code'] = 599
            traceback.print_exc()
        finally:
            pass
        #print('result=', result)
        return result
    async def get(self, *args, **kwargs):
        body = "method not allowed!"
        self.set_header('cache-control','no-cache,no-store')
        self.set_header('Content-Length',len(body))
        self.set_status(403)
        self.write(body)
    async def post(self, *args, **kwargs):
        logging.info(self.application.pages)
        browser = self.application.browser
        page = await browser.newPage()

        if self.application.pages > 5:
            body = "browser pages is too many, open new browser process!"
            self.set_status(403)
            logging.info(body)
            self.finish(body)
            return
        raw_data = self.request.body.decode('utf8')
        fetch = json.loads(raw_data, encoding='utf-8')
        try:
            self.application.pages += 1
            result = await self._fetch(fetch,page)
        except Exception as e:
            logging.info(e)
        finally:
            await page.close()
            self.application.pages -= 1

        logging.info('{} {}'.format(fetch['url'],result['status_code']))
        #print(result)
        self.write(result)

def run():
    global env
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../../config.json')) as f:
            config = json.load(f)
            env = config.get('env','production')
    except Exception as e:
        logging.error(e)
        env = "production"
    loop = asyncio.get_event_loop()
    app = Application()
    app.init_browser(loop)
    app.listen(8071)
    loop.run_forever()

if __name__ == '__main__':
    run()
