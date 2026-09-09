const mongoose = require('mongoose');
const env = require('../env');

async function connectDb() {
  mongoose.set('strictQuery', true);
  await mongoose.connect(env.MONGODB_URI);
  // eslint-disable-next-line no-console
  console.log('MongoDB connected');
}

module.exports = { connectDb };