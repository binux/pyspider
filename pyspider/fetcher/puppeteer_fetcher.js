const express = require("express");
const puppeteer = require('puppeteer');
const bodyParser = require('body-parser');

const app = express();

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({
  	extended: false
}));

async function spider(fetch, http_response) {
	var first_request = true,
		first_response = null,
		finished = false,
		page_loaded = false,
		start_time = Date.now(),
		end_time = null,
		script_executed = false,
		script_result = null,
		error_msg = null,
		wait_before_end = 1000,
		browser_settings = {};

	if (fetch.headless == "false") {
		browser_settings["headless"] = false;
	} else {
		browser_settings["headless"] = true;
	}

	if (fetch.proxy) {
		if (fetch.proxy.indexOf("://") == -1) {
			fetch.proxy = "http://" + fetch.proxy;
		}
		browser_settings["args"] = ['--no-sandbox', "--proxy-server=" + fetch.proxy];
	}

	const browser = await puppeteer.launch(browser_settings);

	browser.on('targetcreated', async (target) => {
		if (!script_executed && fetch.js_script && fetch.js_run_at === "document-start") {
			console.log('running document-start script.');
			const page = await target.page();
			script_result = await page.evaluate(fetch.js_script);
			script_executed = true;
			console.log("script_result is: "+script_result);
		}
	});

	const page = await browser.newPage();

	page.on("console", msg => {
		console.log('console: ' + msg.args());
	});

	page.on("load", async () => {
		page_loaded = true;
		if (!script_executed && fetch.js_script && fetch.js_run_at !== "document-start") {
			console.log('running document-end script.');
			script_result = await page.evaluate(fetch.js_script);
			console.log("end script_result is: ", script_result);
			script_executed = true;
		}
		page_content = await page.content();
		end_time = Date.now() + wait_before_end;
		setTimeout(make_result, wait_before_end+10, page, http_response);
	});

	if (fetch.url && fetch.url.indexOf("://") == -1) {
		fetch.url = "http://" + fetch.url;
	}

	width = fetch.js_viewport_width || 1024;
	height = fetch.js_viewport_height || 768*3;
	await page.setViewport({
		"width": width,
		"height": height
	});

	if (fetch.headers) {
		fetch.headers = JSON.parse(fetch.headers)
		await page.setExtraHTTPHeaders(fetch.headers);
	}

	if (fetch.headers && fetch.headers["User-Agent"]) {
		console.log(fetch.headers["User-Agent"]);
		console.log(typeof fetch.headers["User-Agent"]);
		page.setUserAgent(fetch.headers["User-Agent"]);
	}

	var page_timeout = fetch.timeout ? fetch.timeout*1000 : 20*1000;
	await page.setDefaultNavigationTimeout(page_timeout);

	async function make_result(page, http_response) {
		if (finished) {
			return;
		}

		if (Date.now() - start_time < page_timeout) {
			if (!!!end_time) {
				return;
			}
			if (end_time > Date.now()) {
				setTimeout(make_result, Math.min(Date.now()-end_time, 100), page, http_response);
				return;
			}
		}

		finished = true;

		var cookies = {};
		var tmp_cookies = await page.cookies();
		tmp_cookies.forEach(function(e) {
			cookies[e.name] = e.value;
		})

		var page_content = await page.content();

		var result = {};
		try {
			result = _make_result(page, page_content, cookies);
			console.log("["+result.status_code+"] "+result.orig_url+" "+result.time);
		} catch (e) {
			result = {
				orig_url: fetch.url,
				status_code: 599,
				error: e.toString(),
				content: page_content || "",
				headers: {},
				url: page.url() || fetch.url,
				cookies: {},
				time: (Date.now() - start_time) / 1000,
				js_script_result: null,
				save: fetch.save
			}
		}

		var body = JSON.stringify(result, null, 4);

		http_response.set({
			"Cache": "no-cache",
			"Content-Type": "application/json"
		});

		if (fetch.screenshot_path) {
			await page.screenshot({path: fetch.screenshot_path});
		}

		http_response.send(body);

		await page.close();
		await browser.close();
		return;
	}

	function _make_result(page, page_content, cookies) {
		if (first_response === null) {
			throw "Timeout before first response.";
		}

		var headers = {};
		if (first_response.headers()) {
			var response_headers = first_response.headers();
			for (name in response_headers) {
				headers[name] = response_headers[name];
			}
		}

		return  {
			orig_url: fetch.url,
			status_code: first_response.status() || 599,
			error: error_msg,
			content:  page_content,
			headers: headers,
			url: page.url(),
			cookies: cookies,
			time: (Date.now() - start_time) / 1000,
			js_script_result: script_result,
			save: fetch.save
		}
	}

	if (fetch.method && fetch.method.toLowerCase() === "post") {
		await page.setRequestInterception(true);
		page.on("request", interceptedRequest => {
			end_time = null;
			if (first_request) {
				first_request = false;
				var data = {
					"method": "POST",
					"postData": fetch.data
				};
				console.log(data);
				interceptedRequest.continue(data);
			}
		})
	} else {
		page.on("request", interceptedRequest => {
			end_time = null;
		})
	}

	page.on("response", async (response) => {
		if (first_response === null && response.status() != 301 && response.status() != 302) {
			first_response = response;
		}
		if (page_loaded) {
			end_time = Date.now() + wait_before_end;
			setTimeout(make_result, wait_before_end+10, page, http_response);
		}
	});


	setTimeout(make_result, page_timeout+100, page, http_response);

	try {
		await page.goto(fetch.url);
	} catch (e) {
		console.error("Request error: "+fetch.url+" error_msg:"+e.toString());
		end_time = Date.now() + wait_before_end;
		make_result(page, http_response)
	}
}


app.get("/", function(request, response) {
	body = "method not allowed!";
	response.status(403);
	response.set({
		"cache": "no-cache",
		"Content-Length": body.length
	});
	response.send(body);
});

app.post("/", function (request, response) {
	var fetch = request.body;
	console.log(fetch);
	spider(fetch, response);
});


var port = 22222;
if (process.argv.length === 3) {
	port = parseInt(process.argv[2])
}

app.listen(port, function (){
	console.log("server listen: "+port);
});




