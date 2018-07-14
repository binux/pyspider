'use strict';

const puppeteer = require('puppeteer');
const devices = require('puppeteer/DeviceDescriptors');
const Koa = require('koa');
const bodyParser = require('koa-bodyparser');

var app = new Koa();
app.use(bodyParser());
// 获取到系统指定跑在哪个端口
const port = process.argv[2];

let result = "",
	_fetch="",
	browser="",
	first=true,
	browserWSEndpoint="",
	start_time = "",
	finish = false,
	response = "",
	script_result = "";

// 定义koa所运行的内容
app.use(async (ctx,next) => {
	await next();
	if(ctx.request.method === 'POST') {
		console.log("post method !!!");
		_fetch = JSON.parse(ctx.request.rawBody);
		const body = await fetch(_fetch);
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

const fetch = async (_fetch) => {
	try{
		start_time = Date.now();
		if(first){
			browser = await puppeteer.launch({headless:false});
			browserWSEndpoint = await browser.wsEndpoint();
			// await browser.disconnect();
			first = false;
		}else{
			browser = await puppeteer.connect({browserWSEndpoint})
		}
		// 用于存储结果
		// console.log("fetch的内容："+ JSON.stringify(_fetch,null,2));
		console.log("服务器接收到的url：　"+_fetch.url);

		// 是否启用代理
		if (_fetch.proxy && _fetch.proxy.includes("://")) {
			_fetch.proxy = '--proxy-server=' + _fetch.proxy.replace(/http:\/\//,"").replace(/https:\/\//,"")
			browser = await puppeteer.launch({
				headless: false,
				args: [_fetch.proxy]
			});
		} else if (_fetch.proxy){
			_fetch.proxy = '--proxy-server=' + _fetch.proxy;
			browser = await puppeteer.launch({
				headless: false,
				args: [_fetch.proxy]
			});
		}

		// 设置浏览器视窗的大小
		const page = await browser.newPage();
		await page.setRequestInterception(true);

		// 设置user-agent
		if (_fetch.headers && _fetch.headers['User-Agent']) {
			await page.setUserAgent(_fetch.headers['User-Agent']);
		}

		// 选择设备
		if (_fetch.devices) {
			await page.emulate(devices[_fetch.devices]);
		}else{
			await page.setViewport({
				width:_fetch.js_viewport_width || 1024,
				height:_fetch.js_viewport_width || 768*3
			})
		}

		// 初始页面加载完毕时输出
		page.once('domcontentloaded',() => {
			console.log("page load finished !!! ");
		});

		// function logRequest(interceptedRequest,request) {
		// 	console.log('A request was made:', interceptedRequest.url());
		// }
		// page.on('request', logRequest);

		if(!_fetch.load_images){
			page.on('request',request => {
				if (request.resourceType() === 'image')
					request.abort();
				else
					request.continue();
			})
		}

		let index = 0,index1;
		const count= () => {
			index += 1;
			console.log("我是一个index：" + index);
		};
		page.on('requestfinished',count);

		const make_sure = () =>{
			return new Promise((resolve,reject) => {
				setTimeout(function(){
					if(index === index1){
						console.log(index + " --- " + index1);
						console.log("进球了！！！！");
						resolve (true);
					}else {
						console.log("球没有进！！！");
                        index1 = index;
                        resolve(false);
                    }
                    make_sure()
				},200)
			})
		};

		finish = await make_sure();

		console.log("我是finish：" + finish);

		// 设置请求头
		page.setExtraHTTPHeaders(_fetch.headers);

		// 监听网页的console输出的内容
		page.on('console', msg => {
			if (typeof msg === 'object') {
				console.log('console: \n'+msg.text())
			}else{
				console.log('console: \n'+msg)
			}
		});

		// 请求失败的情况
		page.on('requestfailed', request => {
			console.log("失败了："+request.url() + '失败的原因：' + request.failure().errorText);
		});

		// 进入被抓取的页面post or get (暂定)
		if(_fetch.method === 'POST' || _fetch.method === 'post'){
			response = await page.evaluate(`$.post("${_fetch.url}",${_fetch.data})`);
		}else{
			response = await page.goto(_fetch.url);
			finish = await make_sure();
		}

		if(finish){
			// 执行自定义的JS
			if(_fetch.js_script && _fetch.js_script != ""){
				script_result = await page.evaluate(_fetch.js_script);
			}

			console.log('返回数据！！！');

			const content = await page.content();
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
			console.log("["+result.status_code+"] "+result.orig_url+" "+result.time)
			finish = false;
			console.log("我完成了！！！！！！"+finish);
			await page.close();
			return result;
		}
	}catch(e){
		result = {
			orig_url: _fetch.url,
			status_code: 599,
			error: e.toString(),
			content: "",
			headers: "",
			url: "",
			cookies: "",
			time: "",
			js_script_result: null,
			save: _fetch.save
		}
	}

	const body = JSON.stringify(result, null, 2);
	return body;
};
app.listen(port);

// 启动服务器
if (app) {
	console.log('chromeheadless fetcher runing on port ' + port);
}else{
	console.log('Error: Could not create web server listening on port ' + port);
}


