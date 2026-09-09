// backend/src/server.js
// NEW FILE

const express = require("express");
const cors = require("cors");
const cookieParser = require("cookie-parser");

const env = require("./src/shared/env");

const {connectDb} = require("./src/shared/db/connection")
const auth = require("./src/modules/auth");
const users = require("./src/modules/users/index");

const app = express();

app.use(
  cors({
    origin: env.CORS_ORIGIN,
    credentials: true, // required so the browser sends/receives the refresh cookie
  }),
);
app.use(express.json());
app.use(cookieParser());

app.get("/health", (_req, res) => res.status(200).json({ status: "ok" }));

app.use("/api/auth", auth.router);
app.use("/api/users", users.router);

// Centralized error handler — catches thrown errors from async
// handlers (e.g. portfolios.getOwnedPortfolioOrThrow's err.status).
// eslint-disable-next-line no-unused-vars
app.use((err, _req, res, _next) => {
  const status = err.status || 500;
  if (status === 500) {
    // eslint-disable-next-line no-console
    console.error(err);
  }
  res.status(status).json({ errors: [err.message || "Internal server error"] });
});

async function start() {
  await connectDb();
  app.listen(env.PORT, () => {
    // eslint-disable-next-line no-console
    console.log(`Server listening on port ${env.PORT}`);
  });
}

if (require.main === module) {
  start();
}

module.exports = { app, start };

// // const express = require("express");
// // require("dotenv").config();

// // const app = express();

// // app.use(express.json());

// // app.get("/health", (req, res) => {
// //   res.status(200).json({
// //     status: "ok",
// //   });
// // });

// // const PORT = process.env.PORT || 5000;

// // app.listen(PORT, () => {
// //   console.log(`Backend server running on port ${PORT}`);
// // });j

// const express = require("express");
// require("dotenv").config();

// const connectDB = require("./src/shared/db/connection");

// const app = express();

// app.use(express.json());

// app.get("/health", (req, res) => {
//   res.status(200).json({
//     status: "ok",
//   });
// });

// const PORT = process.env.PORT || 5000;

// const startServer = async () => {
//   await connectDB();

//   app.listen(PORT, () => {
//     console.log(`Backend server running on port ${PORT}`);
//   });
// };

// startServer();
