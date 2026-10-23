
require("dotenv").config();

const express = require("express");

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());

// Health check
app.get("/health", (req, res) => {
  res.status(200).json({
    success: true,
    message: "Server is running\n",
  });
});

// GET route
app.get("/api/users", (req, res) => {
  res.json({
    success: true,
    data: [],
  });
});

// GET user by ID
app.get("/api/users/:id", (req, res) => {
  res.json({
    success: true,
    data: { id: req.params.id },
  });
});

// POST route
app.post("/api/users", (req, res) => {
  const { name, email } = req.body;

  if (!name || !email) {
    return res.status(400).json({
      success: false,
      message: "Name and email are required\n",
    });
  }

  res.status(201).json({
    success: true,
    message: "User created successfully\n",
    data: { name, email },
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: "Route not found\n",
  });
});

// Global error handler
app.use((err, req, res, next) => {
  console.error(err);

  res.status(err.status || 500).json({
    success: false,
    message: err.status ? err.message : "Internal server error\n",
  });
});

// Start server
const server = app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}\n`);
});

// Graceful shutdown
process.on("SIGTERM", () => {
  server.close(() => {
    console.log("Server closed\n");
    process.exit(0);
  });
});
