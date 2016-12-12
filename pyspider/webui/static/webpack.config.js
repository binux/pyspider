var webpack = require("webpack");
var ExtractTextPlugin = require("extract-text-webpack-plugin");

module.exports = {
  entry: {
    index: "./src/index",
    debug: "./src/debug",
    result: "./src/result.less",
    task: "./src/task.less",
    tasks: "./src/tasks.less",
  },
  output: {
    //path: "./dist",
    filename: "[name].min.js"
  },
  module: {
    loaders: [
      { test: /\.js$/, loader: "babel-loader" },
      { test: /\.less$/, loader: ExtractTextPlugin.extract("style-loader", "css-loader?sourceMap!less-loader?sourceMap") }
    ]
  },
  devtool: 'source-map',
  plugins: [
    new ExtractTextPlugin("[name].min.css"),
    new webpack.optimize.UglifyJsPlugin({ compress: { warnings: false } }),
  ]
}
