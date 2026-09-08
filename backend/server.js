// const express = require("express");
// require("dotenv").config();

// const app = express();

// app.use(express.json());

// app.get("/health", (req, res) => {
//   res.status(200).json({
//     status: "ok",
//   });
// });

// const PORT = process.env.PORT || 5000;

// app.listen(PORT, () => {
//   console.log(`Backend server running on port ${PORT}`);
// });j

const express = require("express");
require("dotenv").config();

const connectDB = require("./src/shared/db/connection");

const app = express();

app.use(express.json());

app.get("/health", (req, res) => {
  res.status(200).json({
    status: "ok",
  });
});

const PORT = process.env.PORT || 5000;

const startServer = async () => {
  await connectDB();

  app.listen(PORT, () => {
    console.log(`Backend server running on port ${PORT}`);
  });
};

startServer();
