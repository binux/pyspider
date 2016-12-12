--#! /usr/bin/env lua
--
-- splash_fetcher.lua
-- Copyright (C) 2016 Binux <roy@binux.me>
--
-- Distributed under terms of the Apache license, version 2.0.
--

json = require("json")

function render(splash, fetch)
    local debug = true
    local function log_message(message, level)
        if debug or level ~= nil then
            print(message)
        end
    end
    if not splash.with_timeout then
        function with_timeout(self, func, timeout)
            return true, func()
        end
        splash.with_timeout = with_timeout
    end

    log_message(json.encode(fetch))

    -- create and set page
    local start_time = os.time()

    splash:clear_cookies()
    splash:autoload_reset()
    splash:on_request_reset()
    splash:on_response_reset()

    splash:set_viewport_size(fetch.js_viewport_width or 1024, fetch.js_viewport_height or 768 * 3)
    if fetch.headers and fetch.headers["User-Agent"] ~= nil then
        splash:set_user_agent(fetch.headers["User-Agent"])
    end
    if fetch.headers then
        fetch.headers['Accept-Encoding'] = nil
        fetch.headers['Connection'] = nil
        fetch.headers['Content-Length'] = nil
        splash:set_custom_headers(fetch.headers)
    end
    splash.images_enabled = (fetch.load_images == true)
    splash.resource_timeout = math.min((fetch.timeout or 20), 58)
    fetch.timeout = splash.resource_timeout

    local wait_before_end = 1.0;
    local end_time = start_time + fetch.timeout - 0.1
    

    -- callbacks
    splash:on_request(function(request)
        -- wait for new request
        end_time = start_time + fetch.timeout - 0.1
        log_message("Starting request: [" .. tostring(request.method) .. "]" .. tostring(request.url))

        if fetch.proxy_host and fetch.proxy_port then
            request:set_proxy({
                host = fetch.proxy_host,
                port = tonumber(fetch.proxy_port),
                username = fetch.proxy_username,
                password = fetch.proxy_password,
                type = 'HTTP'
            })
        end
    end)

    local first_response = nil
    splash:on_response(function(response)
        if first_response == nil then
            first_response = response
        end
        -- wait for some other respond and render
        end_time = math.min(os.time() + wait_before_end + 0.1, start_time + fetch.timeout - 0.1)
        log_message("Request finished: [" .. tostring(response.status) .. "]" .. tostring(response.url))
    end)

    -- send request
    local js_script_result = nil
    local timeout_ok, ok, reason = splash:with_timeout(function()
        local js_script = nil
        if fetch.js_script then
            ok, js_script = pcall(function()
                return splash:jsfunc(fetch.js_script)
            end)
            if not ok then
                log_message("js_script error: " .. tostring(js_script), 1)
                js_script = nil
            end
        end

        if js_script and fetch.js_run_at == "document-start" then
            log_message("running document-start script.");
            ok, js_script_result = pcall(js_script)
            if not ok then
                log_message("running document-start script error: " .. tostring(js_script_result), 1)
            end
        end

        local ok, reason = splash:go{url=fetch.url, http_method=fetch.method, body=fetch.data}
        end_time = math.min(os.time() + wait_before_end + 0.1, start_time + fetch.timeout - 0.1)

        if js_script and fetch.js_run_at ~= "document-start" then
            splash:wait(0.5)
            log_message("running document-end script.");
            ok, js_script_result = pcall(js_script)
            if not ok then
                log_message("running document-end script error: " .. tostring(js_script_result), 1)
            end
        end

        -- wait for all requests finished
        local now = os.time()
        while now <= end_time do
            splash:wait(math.min(end_time - now, 0.1))
            now = os.time()
        end

        return ok, reason
    end, fetch.timeout + 0.1)

    -- make response
    local cookies = {}
    for i, c in ipairs(splash:get_cookies()) do
        cookies[c.name] = c.value
    end
    if (not timeout_ok and first_response.ok) or (timeok and ok) then
        return {
            orig_url = fetch.url,
            status_code = first_response.status == 0 and 599 or first_response.status,
            error = nil,
            content = splash:html(),
            headers = first_response.headers,
            url = splash:url(),
            cookies = cookies,
            time = os.time() - start_time,
            js_script_result = js_script_result and tostring(js_script_result),
            save = fetch.save
        }
    else
        if first_response then
            return {
                orig_url = fetch.url,
                status_code = first_response.status == 0 and 599 or first_response.status,
                error = reason,
                content = splash:html(),
                headers = first_response.headers,
                url = splash:url(),
                cookies = cookies,
                time = os.time() - start_time,
                js_script_result = js_script_result and tostring(js_script_result),
                save = fetch.save
            }
        else
            return {
                orig_url = fetch.url,
                status_code = 599,
                error = reason,
                content = splash:html(),
                headers = {},
                url = splash:url(),
                cookies = cookies,
                time = os.time() - start_time,
                js_script_result = js_script_result and tostring(js_script_result),
                save = fetch.save
            }
        end
    end

end

function main(splash)
    local fetch = splash.args
    local start_time = os.time()

    ok, result = pcall(function()
        return render(splash, fetch)
    end)

    if ok then
        return result
    else
        return {
            orig_url = fetch.url,
            status_code = 599,
            error = result,
            content = splash:html(),
            headers = {},
            url = splash:url(),
            cookies = {},
            time = os.time() - start_time,
            js_script_result = nil,
            save = fetch.save
        }
    end
end
