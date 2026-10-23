require("dotenv").config();

const express = require("express");
const mongoose = require("mongoose");

const app = express();
const PORT = process.env.PORT || 3000;
const MONGODB_URI = process.env.MONGODB_URI || "mongodb://localhost:27017/compose-db";

let server;

const userSchema = new mongoose.Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true }
}, { timestamps: true });

const User = mongoose.model("User", userSchema);

app.use(express.json());

app.get("/health", (req, res) => {
  res.status(200).json({
    success: true,
    message: "Server is running\n",
  });
});

app.post("/api/users", async (req, res) => {
  const { name, email } = req.body;

  if (!name || !email) {
    return res.status(400).json({
      success: false,
      message: "Name and email are required\n",
    });
  }

  try {
    const newUser = new User({ name, email });
    await newUser.save();

    res.status(201).json({
      success: true,
      message: "User created successfully\n",
      data: newUser,
    });
  } catch (error) {
    if (error.code === 11000) {
      return res.status(400).json({
        success: false,
        message: "Email already exists\n",
      });
    }
    res.status(500).json({ success: false, message: "Error creating user\n" });
  }
});

app.get("/api/users", async (req, res) => {
  try {
    const users = await User.find();
    res.json({
      success: true,
      data: users,
    });
  } catch (error) {
    res.status(500).json({ success: false, message: "Error fetching users\n" });
  }
});

app.get("/api/users/:id", async (req, res) => {
  try {
    const user = await User.findById(req.params.id);
    if (!user) {
      return res.status(404).json({
        success: false,
        message: "User not found\n",
      });
    }
    res.json({
      success: true,
      data: user,
    });
  } catch (error) {
    res.status(500).json({ success: false, message: "Error fetching user\n" });
  }
});

app.put("/api/users/:id", async (req, res) => {
  const { name, email } = req.body;
  try {
    const updatedUser = await User.findByIdAndUpdate(
      req.params.id,
      { name, email },
      { new: true, runValidators: true }
    );

    if (!updatedUser) {
      return res.status(404).json({
        success: false,
        message: "User not found\n",
      });
    }

    res.json({
      success: true,
      message: "User updated successfully\n",
      data: updatedUser,
    });
  } catch (error) {
    res.status(500).json({ success: false, message: "Error updating user\n" });
  }
});

app.delete("/api/users/:id", async (req, res) => {
  try {
    const deletedUser = await User.findByIdAndDelete(req.params.id);
    if (!deletedUser) {
      return res.status(404).json({
        success: false,
        message: "User not found\n",
      });
    }
    res.json({
      success: true,
      message: "User deleted successfully\n",
    });
  } catch (error) {
    res.status(500).json({ success: false, message: "Error deleting user\n" });
  }
});

app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: "Route not found\n",
  });
});

app.use((err, req, res, next) => {
  console.error(err);

  res.status(err.status || 500).json({
    success: false,
    message: err.status ? err.message : "Internal server error\n",
  });
});

const start_server = async () => {
  try {
    console.log("Connecting to MongoDB...");
    await mongoose.connect(MONGODB_URI);
    console.log("Connected to MongoDB successfully.");

    server = app.listen(PORT, () => {
      console.log(`Server running at http://localhost:${PORT}\n`);
    });

    process.on("SIGTERM", () => {
      if (server) {
        server.close(() => {
          console.log("Server closed\n");
          process.exit(0);
        });
      } else {
        process.exit(0);
      }
    });

  } catch (error) {
    console.error("Database connection failed. Exiting process...", error);
    process.exit(1);
  }
};

start_server();
