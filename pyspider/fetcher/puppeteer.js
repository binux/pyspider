const express = require("express");
const puppeteer = require('puppeteer');
const bodyParser = require('body-parser');

const app = express();



app.get("/", function (request, response) {
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
    response.send("hello world")
});


var port = 22222;
if (process.argv.length === 3) {
    port = parseInt(process.argv[2])
}

app.listen(port, function () {
    console.log("server listen: " + port);
});