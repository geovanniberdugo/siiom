module.exports = {
  // This is the "main" file which should include all other modules
  entry: './main.js',
  // Where should the compiled file go?
  output: {
    // To the `dist` folder
    path: __dirname,
    // With the filename `build.js` so it's dist/build.js
    filename: 'index.js'
  },
  module: {
    // Special compilation rules
    loaders: [
      {
        // Ask webpack to check: If this file ends with .js, then apply some transforms
        test: /\.js$/,
        // Transform it with babel
        loader: 'babel-loader',
        // don't transform node_modules folder (which don't need to be compiled)
        exclude: /node_modules/,
        query: {
          presets: ['es2015']
        }
      },
      {
        test: /\.vue$/,
        loader: 'vue'
      }
    ],
    rules: [
      {
        test: /\.vue$/,
        loader: 'vue-loader',
        options: {
          cssModules: {
            localIdentName: '[path][name]---[local]---[hash:base64:5]',
            camelCase: true
          }
        }
      }
    ]
  }
}

