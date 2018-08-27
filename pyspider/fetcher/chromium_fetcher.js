'use strict';

const puppeteer = require('puppeteer');
const device = require('puppeteer/DeviceDescriptors');
const Koa = require('koa');
const bodyParser = require('koa-bodyparser');
var request = require('request');

const app = new Koa();
app.use(bodyParser());
// to get the port which server run
const port = process.argv[2];

let result = "",
	_fetch = "",
	browser = "",
	// use for judge proxy switch ? 
	pre_proxy = "",
	finish = false,
	body = "";

// koa server
app.use(async (ctx,next) => {
	await next();
	if(ctx.request.method === 'POST') {
		_fetch = JSON.parse(ctx.request.rawBody);
		if(_fetch.method === 'POST' || _fetch.method === 'post'){
			body = await post(_fetch);
		}else{
			body = await get(_fetch);
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
const get = async (_fetch) => {
	const start_time = Date.now();
	let response = "",
		script_result = "",
		content = "",
		page = "";
	try{
		// use proxy ?
		// Frequent opening and closing of the browser affects performance, so only the proxt changes will restart the browser.
		if (_fetch.proxy) {
			const now_proxy = _fetch.proxy;

			if (!_fetch.proxy.includes("://")){
				_fetch.proxy = `--proxy-server=http://${_fetch.proxy}`;
			}else{
                _fetch.proxy = `--proxy-server=${_fetch.proxy}`;
            }

			if (browser !== "" && pre_proxy !== now_proxy) {
				console.log(`Swith proxy to: ${_fetch.proxy}`);
				await browser.close();
				browser = await puppeteer.launch({
					headless: _fetch.headless !== false,
					timeout: _fetch.timeout ? _fetch.timeout * 1000 : 30 * 1000,
					args: [_fetch.proxy, '--no-sandbox', '--disable-setuid-sandbox']
				});
			}else if (browser === ""){
				browser = await puppeteer.launch({
					headless: _fetch.headless !== false,
					timeout: _fetch.timeout ? _fetch.timeout * 1000 : 30 * 1000,
					args: [_fetch.proxy,'--no-sandbox', '--disable-setuid-sandbox']
				});
			}
			
		} else {
			if (browser === ""){
				browser = await puppeteer.launch({
					headless: _fetch.headless !== false,
					timeout:_fetch.timeout ? _fetch.timeout * 1000 : 30*1000,
					args: ['--no-sandbox', '--disable-setuid-sandbox']
				});
			} else if (pre_proxy !== ""){
				pre_proxy = "";
				await browser.close();
				browser = await puppeteer.launch({
				    	headless: _fetch.headless !== false,
					timeout:_fetch.timeout ? _fetch.timeout * 1000 : 30*1000,
					args: ['--no-sandbox', '--disable-setuid-sandbox']
				});
			} 
		}
		// pre_proxy is last request to use there compare it to now_proxy to judge the proxy is switch ?
		pre_proxy = _fetch.proxy;

		// create and set page
		page = await browser.newPage();
		await page.setRequestInterception(true);

		// set user-agent
		if (_fetch.headers && _fetch.headers['User-Agent']) {
			await page.setUserAgent(_fetch.headers['User-Agent']);
		}

		// choice browse device or set page size
		if (_fetch.device) {
			await page.emulate(device[_fetch.device]);
		}else{
			await page.setViewport({
				width:_fetch.js_viewport_width || 1024,
				height:_fetch.js_viewport_width || 768*3
			})
		}

		// when base page load finish
		// page.once('domcontentloaded',() => {
		// 	console.log("base page load finished !!! ");
		// });

		const logRequest =  (interceptedRequest,request) => {
			console.log('A request was made:', interceptedRequest.url());
		};
		page.on('request', logRequest);

		// load images ?
		if(!_fetch.load_images){
			page.on('request',request => {
				if (request.resourceType() === 'image')
					request.abort();
				else
					request.continue();
			})
		}

		// set request headers
		page.setExtraHTTPHeaders(_fetch.headers);

		// set cookies
		if(_fetch.cookies){
			const cookies = [];
			for(let each in _fetch.cookies){
				cookies.push({name:each,value:_fetch.cookies[each],url:_fetch.url})
			}
			await page.setCookie(cookies);
		}

		// print the page console messages
		page.on('console', msg => {
			if (typeof msg === 'object') {
				console.log('console:' + msg.text())
			}else{
				console.log('console:' + msg)
			}
		});

		// request failed
		// page.on('requestfailed', request => {
		// 	console.log(`failure：${request.url()} because：${request.failure().errorText}`);
		// });

		// to make sure request finish
		let counter_1 = 0,
			counter_2;
		const counter = () => {
			counter_1 += 1;
		};
		page.on('requestfinished',counter);

		// every 200ms check request is completed ?
		const make_result = () =>{
			return new Promise((resolve,reject) => {
				setTimeout(function(){
					if(counter_1 === counter_2){
						// console.log(counter_1 + " --- " + counter_2);
						// console.log("Finish!!!");
						resolve (true);
					}else {
						// console.log(counter_1 + " --- " + counter_2);
						// console.log("Not finish");
                        counter_2 = counter_1;
                        resolve(make_result());
                    }
				},200)
			})
		};

		// go to the page crawled
		response = await page.goto(_fetch.url);
		finish = await make_result();

        // get <frame> and <iframe> tag content
		// const iframes = await page.frames();
		// for(let i in iframes){
		// 	console.log(`this is ${i} iframe`);
		// 	let iframe_content = await iframes[i].content();
		// 	content = content + iframe_content + "\n";
		// }

		if(finish){
			// run js_script
			if(_fetch.js_script){
				script_result = await page.evaluate(_fetch.js_script);
				await make_result();
			}

			// to make result
			content = content + "\n" + await page.content();
			const cookies = await page.cookies(_fetch.url);
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
			finish = false;
			// console.log("finish");
		}else{
			throw "Timeout to get page !"
		}
	}catch(e){
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
	// console.log(JSON.stringify(result, null, 2));
	await page.close();
    return JSON.stringify(result, null, 2);
};

// post method with request
const post = async (_fetch) => {
	return new Promise((resolve, reject) => {
		const start_time = Date.now();
        request({
            url: _fetch.url,
            method: 'POST',
            headers:_fetch.headers,
            body: JSON.stringify(_fetch.data),
        },(error, response, body) => {
            if (!error && response.statusCode == 200) {
                //return the content
				// console.log("success !");
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
app.listen(port);

// start server
if (app) {
	console.log('Chromium fetcher runing on port ' + port);
}else{
	console.log('Error: Could not create web server listening on port ' + port);
}