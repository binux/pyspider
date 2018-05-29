'use strict';

const puppeteer = require('puppeteer')
const http = require('http')
const devices = require('puppeteer/DeviceDescriptors');

let port,server,fetch="",browser,browserWSEndpoint,
	wait_before_end = 1000

server = http.createServer(function(request,response){
	// fetch用于存储web界面传过来的内容
	fetch=""
	if (request.method == 'GET') {
		const body = "method not allowed!"
		response.statusCode = 403
		response.headers = {
			'Cache': 'no-cache',
        	'Content-Length': body.length
		}
		response.write(body)
		response.end()
		return 
	}

	request.on('data',function(chunk){
		fetch += chunk
	})

	request.on('end',function(data){
		(async () => {
		    console.log("fetch的内容："+ JSON.stringify(fetch))
			const start_time = await Date.now()
			let end_time = await null,
				first_response = await null,
				finished = await false,
				page_loaded = await false;

			fetch = await JSON.parse(fetch)
			await console.log("服务器接收到的数据：　"+fetch.url);
			// 是否启用代理
			if (fetch.proxy && fetch.proxy.includes("://")) {
		        fetch.proxy = '--proxy-server=' + fetch.proxy.replace(/http:\/\//,"").replace(/https:\/\//,"")
		    }else if (fetch.proxy){
		    	fetch.proxy = '--proxy-server=' + fetch.proxy
		    }
		    if (fetch.proxy) {
		    	browser = await puppeteer.launch({
					headless: false,
					args: [fetch.proxy]
				});
		    }else{
		    	browser = await puppeteer.connect({browserWSEndpoint}) 
		    }
			
			const page = await browser.newPage();
			// 设置浏览器视窗的大小
			page.setViewport({
				width:fetch.js_viewport_width || 1024,
				height:fetch.js_viewport_width || 768*3
			}) 
			// 监听网页的console输出的内容
			page.on('console', msg => {
			  	if (typeof msg === 'object') {
			  		console.log(msg.text())
			  	}else{
			  		console.log(msg)
			  	}
			})

			// 页面加载完毕时输出
			page.once('load',() => console.log(" page load finished !!! "))
			// 选择设备
			if (fetch.devices) {
				await page.emulate(devices[fetch.devices]);
			}
			// 翻页
			if (fetch.next) {
				while(true) {
					const next = await page.$(fetch.next);
					if (next) {
						await next.click();
						await page.waitFor(fetch.pageInterval)
					}else{
						break
					}
				}
			}
			// 滚动
			let scrollStep = fetch.scrollStep; //每次滚动的步长
			while (false) {
				scrollEnable = await page.evaluate(() => {
				 	let scrollTop = document.scrollingElement.scrollTop;
				 	document.scrollingElement.scrollTop = scrollTop + fetch.scrollStep;
				 	if (fetch.scrollPosition) {
				 		return fetch.scrollPosition > scrollTop + 1080 ? true : false
				 	}else{
				 		return document.body.clientHeight > scrollTop + 1080 ? true : false
				 	}
			 	}, fetch.scrollStep);
			 	await page.waitFor(fetch.scrollTime) // 每次滚动的间隔时间
			}
			// 用于存储结果
			let result = {}

			try{
				const response = await page.goto(fetch.url)
				await page.waitFor(1000)
				const content = await page.content()
				result = await {
						orig_url: fetch.url,
				        status_code: response.status() || 599,
				        error: null,
				        content: content,
				        headers: response.headers(),
				        url: page.url(),
				        cookies: page.cookies(fetch.url),
				        time: (Date.now() - start_time) / 1000,
				        js_script_result: null,
				        save: fetch.save
					}
				page.close()
			}catch(e){
				result = await {
			        orig_url: fetch.url,
			        status_code: response.status() || 599,
			        error: e.toString(),
			        content: content,
			        headers: response.headers(),
			        url: page.url(),
			        cookies: page.cookies(fetch.url),
			        time: (Date.now() - start_time) / 1000,
			        js_script_result: null,
			        save: fetch.save
		  		}
			}
			
			const body = await JSON.stringify(result, null, 2)

			response.writeHead(200, {
		        'Cache': 'no-cache',
		        'Content-Type': 'application/json',
		    })
			response.write(body)
			response.end()
			
		})()

	})

}).listen('22222');

port = server.address().port

if (server) {
	puppeteer.launch({headless: false,}).then(async browser => {
   		// 保存 Endpoint，这样就可以重新连接 Chromium
    	browserWSEndpoint = browser.wsEndpoint();
    	// 从Chromium 断开连接
    	browser.disconnect();
	});
	console.log('chromeheadless fetcher runing on port ' + port)
}else{
	console.log('Error: Could not create web server listening on port ' + port);
}


 



