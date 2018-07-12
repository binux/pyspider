const Koa = require('koa');
const bodyParser = require('koa-bodyparser');

var app = new Koa();

app.use(bodyParser());

app.use(async (ctx,next) =>{
    await next();
    if(ctx.request.method === 'POST'){
        console.log("POST !!!");
        console.log(JSON.parse(ctx.request.rawBody));
        ctx.response.status_code = 200;
		ctx.response.set({
			'Cache': 'no-cache',
			'Content-Type': 'application/json',
		});
		ctx.response.body = {data:"this is a post response !!!"};
    }else{
        console.log("GET !!!");
        ctx.response.status_code = 200;
        ctx.response.type = 'text/html';
        ctx.response.body = '<h1>Hello, koa2!</h1>';
    }
})
app.listen(3333);