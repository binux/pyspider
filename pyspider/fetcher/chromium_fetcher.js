'use strict';

const puppeteer = require('puppeteer'),
    device = require('puppeteer/DeviceDescriptors'),
    Koa = require('koa'),
    bodyParser = require('koa-bodyparser'),
    request = require('request'),
    // to get the port which server run
    port = process.argv[2],
    // wait time after a request
    wait_before_end = 1000;

// start Koa server
const app = new Koa();
app.use(bodyParser());


let _fetch = "",
    result = "",
    browser = "",
    browser_with_proxy = "",
	body = "";

// koa server
app.use(async (ctx,next) => {
	await next();
	if(ctx.request.method === 'POST') {
		_fetch = JSON.parse(ctx.request.rawBody);
		if(_fetch.method === 'POST' || _fetch.method === 'post') {
			body = await post(_fetch);
		} else {
		    await launch_browser(_fetch);
		    if(_fetch.proxy)
			    body = await get(_fetch,browser_with_proxy);
            else
                body = await get(_fetch,browser);
		}
		ctx.response.status_code = 200;
		ctx.response.set({
			'Cache': 'no-cache',
			'Content-Type': 'application/json',
		});
		ctx.response.body = body;
	} else {
		console.log("forbidden!!!");
		const body = "method not allowed !!! ";
		ctx.response.statusCode = 403;
		ctx.response.set({
			'Cache': 'no-cache',
        	'Content-Length': body.length
		});
		ctx.response.body = `<h1>${body}</h1>`;
	}
});

// get method with puppeteer
const get = async (_fetch, browser) => {
    return new Promise(async resolve  => {
        const start_time = Date.now();
        let response = "",
            script_result = "",
            content = "",
            loaded = "",
            end_time = "",
            page_timeout = "",
            finished = false,
            page = "";

        // create and set page
        page = await browser.newPage();
        page_timeout = _fetch.timeout ? _fetch.timeout * 1000 : 20*1000;
        page.setDefaultNavigationTimeout(page_timeout);

        await page.setRequestInterception(true);

        // set user-agent
        if (_fetch.headers && _fetch.headers['User-Agent']) {
            await page.setUserAgent(_fetch.headers['User-Agent']);
        }

        // choice browse device or set page size
        if (_fetch.device) {
            await page.emulate(device[_fetch.device]);
        } else {
            await page.setViewport({
                width:_fetch.js_viewport_width || 1024,
                height:_fetch.js_viewport_height || 768*3
            })
        }

        // when base page load finish
        page.once('domcontentloaded',async () => {
            loaded = true;
            console.log("base page load finished !!!");
            // run js_script
            if(_fetch.js_script && _fetch.js_run_at !== "document-start") {
                script_result = await page.evaluate(_fetch.js_script);
            }
        });

        // load images ?
        page.on('request', request => {
           if(request.resourceType() === 'image' && !_fetch.load_images){
                request.abort();
           } else {
                console.log(`Starting request: [${request.method()}] ${request.url()} `);
                request.continue();
           }
        });

        // set request headers
        page.setExtraHTTPHeaders(_fetch.headers);

        // set cookies
        if(_fetch.cookies) {
            const cookies = [];
            for(let each of _fetch.cookies){
                cookies.push({name:each,value:_fetch.cookies[each],url:_fetch.url})
            }
            await page.setCookie(cookies);
        }

        // print the page console messages (filter type=image if load_images=False or undefined)
        page.on('console', msg => {
            if (typeof msg === 'object' && msg.text() !== "Failed to load resource: net::ERR_FAILED") {
                console.log('console:' + msg.text())
            }
        });

        // request failed
        // page.on('requestfailed', request => {
        // 	console.log(`failure：${request.url()} because：${request.failure().errorText}`);
        // });

        page.on('requestfinished', async request => {
            console.log(`Request finished: [${request.method()}] ${request.url()}`);
            if (loaded) {
                end_time = Date.now() + wait_before_end;
                resolve(await make_result()) 
            }
        });

        const make_result = () => {
            return new Promise(resolve => {
                setTimeout(async() => {
                    if (finished) {
                        return "";
                    }
                    if (Date.now() - start_time < page_timeout) {
                        if (!!!end_time) {
                            return "";
                        }
                        if (end_time > Date.now()) {
                            setTimeout(make_result, Math.min(Date.now() - end_time, 100));
                            return "";
                        }
                    }
                    console.log("make_result !!!");
                    // to make result
                    content = content + "\n" + await page.content();
                    const cookies = await page.cookies(_fetch.url);
                    try {
                        result = {
                            orig_url: _fetch.url,
                            status_code: response.status() || 599,
                            error: null,
                            content: content,
                            headers: response.headers(),
                            url: page.url(),
                            cookies: cookies,
                            time: (Date.now() - start_time) / 1000,
                            js_script_result: script_result,
                            save: _fetch.save
                        };
                        console.log("["+result.status_code+"] "+result.orig_url+" "+result.time);
                        finished = true;
                    } catch(e) {
                        result = {
                            orig_url: _fetch.url,
                            status_code: 599,
                            error: e.toString(),
                            content: content || "",
                            headers: {},
                            url: _fetch.url,
                            cookies: {},
                            time: (Date.now() - start_time) / 1000,
                            js_script_result: null,
                            save: _fetch.save
                        }
                    }
                    resolve(result);
                    await page.close();
                },wait_before_end + 10);
            })
        };

        try {
            response = await page.goto(_fetch.url);
        } catch (e) {
            result = {
                orig_url: _fetch.url,
                status_code: 599,
                error: e.toString(),
                content: content || "",
                headers: {},
                url: _fetch.url,
                cookies: {},
                time: (Date.now() - start_time) / 1000,
                js_script_result: null,
                save: _fetch.save
            };
            await page.close();
            resolve (result)
        }
    });
};

// post method with request
const post = _fetch => {
	return new Promise((resolve, reject) => {
		const start_time = Date.now();
        request({
            url: _fetch.url,
            method: 'POST',
            headers:_fetch.headers,
            body: JSON.stringify(_fetch.data),
        },(error, response, body) => {
            if (!error && response.statusCode === 200) {
                //return the content
				result = {
					orig_url: _fetch.url,
					status_code: response.statusCode || 599,
					error: null,
					content: body,
					headers: response.headers,
					url: response.url,
					cookies: {},
					time: (Date.now() - start_time) / 1000,
					js_script_result: null,
					save: _fetch.save
				};
				console.log("["+result.status_code+"] "+result.orig_url+" "+result.time);
                resolve(result)
            }else{
				// when request failure
				// console.log("something error !");
				result = {
					orig_url: _fetch.url,
					status_code: response.statusCode || 599,
					error: null,
					content: body,
					headers: response.headers,
					url: response.url,
					cookies: {},
					time: (Date.now() - start_time) / 1000,
					js_script_result: null,
					save: _fetch.save
				};
				console.log("["+result.status_code+"] "+result.orig_url+" "+result.time);
				resolve(result)
			}
        });
    })
};

// launch two browsers a browser launch with proxy (if has proxy)
const launch_browser = _fetch => {
    return new Promise(async resolve => {
        if (!browser && !_fetch.proxy) {
            browser = await puppeteer.launch({
                headless: _fetch.headless !== false,
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            });
            resolve(browser)
        }else if (!browser_with_proxy && _fetch.proxy) {
            if (!_fetch.proxy.includes("://")) {
                _fetch.proxy = `--proxy-server=http://${_fetch.proxy}`;
            } else {
                _fetch.proxy = `--proxy-server=${_fetch.proxy}`;
            }
            browser_with_proxy = await puppeteer.launch({
                headless: _fetch.headless !== false,
                args: [_fetch.proxy,'--no-sandbox', '--disable-setuid-sandbox']
            });
            resolve(browser_with_proxy)
        }else if (_fetch.proxy) {
            resolve(browser_with_proxy);
        } else
            resolve(browser);

    })
};

app.listen(port);

// start server
if (app) {
	console.log('Chromium fetcher runing on port ' + port);
}else{
	console.log('Error: Could not create web server listening on port ' + port);
}