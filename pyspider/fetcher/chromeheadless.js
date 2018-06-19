'use strict';

const puppeteer = require('puppeteer')
const devices = require('puppeteer/DeviceDescriptors');
const Koa = require('./node_modules/koa')
var bodyParser = require('koa-bodyparser');

var app = new Koa()
app.use(bodyParser());
// 获取到系统指定跑在哪个端口
const port = process.argv[2];
let browser,browserWSEndpoint;

// 定义koa所运行的内容
app.use(async (ctx,next) => {
	await next();
	if(ctx.request.method == 'POST') {
		console.log("koa is runing !");
		const _fetch = JSON.parse(ctx.request.rawBody);
		const body = fetch(_fetch);
		ctx.response.status_code = 200;
		ctx.response.set({
			'Cache': 'no-cache',
			'Content-Type': 'application/json',
		});
		ctx.response.body = body;
	} else {
		console.log("forbidden!!!")
		const body = "method not allowed !!! "
		ctx.response.statusCode = 403;
		ctx.response.set({
			'Cache': 'no-cache',
        	'Content-Length': body.length
		})
		ctx.response.body = `<h1>${body}</h1>`;
	}
});

const fetch = async (_fetch) => {
	let result = {}
	try{
		// 用于存储结果
		console.log("fetch的内容："+ JSON.stringify(_fetch))
		const start_time = Date.now()
		const _fetch = JSON.parse(_fetch)
		console.log("服务器接收到的数据：　"+_fetch.url);
		// 是否启用代理
		if (_fetch.proxy && _fetch.proxy.includes("://")) {
			_fetch.proxy = '--proxy-server=' + _fetch.proxy.replace(/http:\/\//,"").replace(/https:\/\//,"")
		}else if (_fetch.proxy){
			_fetch.proxy = '--proxy-server=' + _fetch.proxy
		}
		if (_fetch.proxy) {
			browser = await puppeteer.launch({
				headless: false,
				args: [_fetch.proxy]
			});
		}else{
			browser = await puppeteer.connect({browserWSEndpoint})
		}

		const page = await browser.newPage();
		// 设置浏览器视窗的大小

		// 选择设备
		if (_fetch.devices) {
			await page.emulate(devices[fetch.devices]);
		}else{
			await page.setViewport({
				width:_fetch.js_viewport_width || 1024,
				height:_fetch.js_viewport_width || 768*3
			})
		}

		// 进入被抓取的页面
		const response = await page.goto(_fetch.url)
		await page.waitFor(3000)

		// 页面加载完毕时输出
		await page.once('load',() => console.log(" page load finished !!! "))

		// 监听网页的console输出的内容
		await page.on('console', msg => {
			if (typeof msg === 'object') {
				console.log(msg.text())
			}else{
				console.log(msg)
			}
		})

		// 翻页
		if (_fetch.next) {
			while(true) {
				const next = await page.$(_fetch.next);
				if (next) {
					await next.click();
					await page.waitFor(_fetch.pageInterval)
				}else{
					break
				}
			}
		}
		console.log('我来了！！！！！')
		// 滚动
		let scrollStep = _fetch.scrollStep; //每次滚动的步长
		let scrollEnable = _fetch.scrollEnable // 是否需要启动滚动
		let scrollPosition = _fetch.scrollPosition // 滚动到哪个位置
		while (scrollEnable) {
			scrollEnable = await page.evaluate((scrollStep,scrollPosition) => {
				let scrollTop = document.scrollingElement.scrollTop;
				document.scrollingElement.scrollTop = scrollTop + scrollStep;
				if (scrollPosition) {
					return _fetch.scrollPosition > scrollTop + 768 ? true : false
				}else{
					return document.body.clientHeight > scrollTop + 768 ? true : false
				}
			}, scrollStep,scrollPosition);
			await page.waitFor(_fetch.scrollTime) // 每次滚动的间隔时间
		}

		// 点击
		if(_fetch.click_list.length !== 0){
			const click_list = fetch.click_list
			for (let key in click_list) {
				let click_ele = await page.$(click_list[key])
				await click_ele.click()
				await page.waitFor(300)
			}
		}

		const content = page.content()
		result = {
				orig_url: _fetch.url,
				status_code: response.status() || 599,
				error: null,
				content: content,
				headers: response.headers(),
				url: page.url(),
				cookies: page.cookies(_fetch.url),
				time: (Date.now() - start_time) / 1000,
				js_script_result: null,
				save: _fetch.save
			}
		await page.close()
	}catch(e){
		result = {
			orig_url: _fetch.url,
			status_code: 599,
			error: e.toString(),
			content: "",
			headers: "",
			url: "",
			cookies: "",
			time: (Date.now() - start_time) / 1000,
			js_script_result: null,
			save: _fetch.save
		}
		page.close()
	}

	const body = JSON.stringify(result, null, 2)
	return body
}
app.listen(port)

// 启动puppeteer，并断开与浏览器的连接
if (app) {
	puppeteer.launch({headless: false,}).then(async browser => {
   		// 保存 Endpoint，这样就可以重新连接 Chromium
    	browserWSEndpoint = await browser.wsEndpoint();
    	// 从Chromium 断开连接
    	await browser.disconnect();
	});
	console.log('chromeheadless fetcher runing on port ' + port)
}else{
	console.log('Error: Could not create web server listening on port ' + port);
}








