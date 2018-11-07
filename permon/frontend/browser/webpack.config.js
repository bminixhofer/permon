const path = require('path');

module.exports = {
  entry: './src/index.js',
  mode: 'production',
  output: {
    path: path.resolve(__dirname, 'static'),
    filename: 'bundle.min.js',
  },
};
