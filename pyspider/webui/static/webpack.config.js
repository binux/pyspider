var ExtractTextPlugin = require("extract-text-webpack-plugin");

module.exports = {
  entry: {
    index: "./src/index",
    debug: "./src/debug",
    css_selector_helper: "./src/css_selector_helper",
    result: "./src/result.less",
		task: "./src/task.less",
		tasks: "./src/tasks.less",
  },
  output: {
    //path: "./dist",
    filename: "[name].js"
  },
  module: {
    loaders: [
      { test: /\.js$/, loader: "babel-loader" },
      { test: /\.less$/, loader: ExtractTextPlugin.extract("style-loader", "css-loader!less-loader") }
    ]
  },
  //devtool: "#inline-source-map",
	devtool: 'source-map',
  plugins: [
    new ExtractTextPlugin("[name].css")
  ]
}
