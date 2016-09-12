--#! /usr/bin/env lua
--
-- splash_fetcher.lua
-- Copyright (C) 2016 Binux <roy@binux.me>
--
-- Distributed under terms of the Apache license, version 2.0.
--


function render(splash, fetch)
    local debug = false
    local function log_message(message, level)
        if debug or level ~= nil then
            print(message)
        end
    end
    if not splash.with_timeout then
        function with_timeout(self, func, timeout)
            log_message(func)
            return true, func()
        end
        splash.with_timeout = with_timeout
    end

    log_message(fetch)

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
    splash.resource_timeout = (fetch.timeout or 20)
    fetch.timeout = splash.resource_timeout
    

    -- callbacks
    splash:on_request(function(request)
        log_message("Starting request: [" .. toString(request.method) .. "]" .. toString(request.url))

        --if fetch.proxy_host and fetch.proxy_port then
            --request:set_proxy({
                --host = fetch.proxy_host,
                --port = fetch.proxy_port,
                --username = fetch.proxy_username,
                --password = fetch.proxy_password
            --})
        --end
    end)

    local first_response = nil
    splash:on_response(function(response)
        if first_response == nil then
            first_response = response
        end
        log_message("Request finished: [" .. toString(response.status) .. "]" .. toString(response.url))
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
                log_message("js_script error: " .. toString(js_script), 1)
                js_script = nil
            end
        end

        if js_script and fetch.js_run_at == "document-start" then
            log_message("running document-start script.");
            ok, js_script_result = pcall(js_script)
            if not ok then
                log_message("running document-start script error: " .. toString(js_script_result), 1)
            end
        end

        local ok, reason = splash:go{url=fetch.url, http_method=fetch.method, body=fetch.data}

        if js_script and fetch.js_run_at ~= "document-start" then
            log_message("running document-end script.");
            ok, js_script_result = pcall(js_script)
            if not ok then
                log_message("running document-end script error: " .. toString(js_script_result), 1)
            end
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
            status_code = first_response.status or 599,
            error = nil,
            content = splash:html(),
            headers = first_response.headers,
            url = splash:url(),
            cookies = cookies,
            time = os.time() - start_time,
            js_script_result = toString(js_script_result),
            save = fetch.save
        }
    else
        if first_response then
            return {
                orig_url = fetch.url,
                status_code = first_response.status or 599,
                error = reason,
                content = splash:html(),
                headers = first_response.headers,
                url = splash:url(),
                cookies = cookies,
                time = os.time() - start_time,
                js_script_result = js_script_resul and toString(js_script_result),
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
                js_script_result = toString(js_script_result),
                save = fetch.save
            }
        end
    end

end

function main(splash)
    return render(splash, splash.args)
end
