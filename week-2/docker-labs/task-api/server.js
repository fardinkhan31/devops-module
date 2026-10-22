const express = require('express');
const mongoose = require('mongoose');

const app = express();
app.use(express.json());


const taskSchema = new mongoose.Schema(
	{
		title: {
			type: String,
			required: true,
			trim: true,
		},
		completed: {
			type: Boolean,
			default: false,
		}
	},
	{ timestamps: true }
);

const Task = mongoose.model("Task", taskSchema);

app.get("/", (req, res) => {
	res.json({
		message: "Task API running with Docker Compose",
		endpoint: ["/health", "/api/tasks", "/api/version"]
	});
});

app.get("/health", (req, res) => {
	res.json({
		status: "ok",
		database: mongoose.connection.readyState === 1 ? "connected" : "disconnected"
	});
});

app.get("/api/version", (req, res) => {
	res.json({
		app: "docker-task-api",
		revision: "v3",
	});
});

app.get("/api/tasks", async (req, res, next) => {
	try {
		const tasks = await Task.find().sort({ createdAt: 1});
		res.json(tasks);
	} catch (error) {
		next(error);
	}
});

app.post("/api/tasks", async (req, res, next) => {
  const title = typeof req.body.title === "string"
    ? req.body.title.trim()
    : "";

  if (!title) {
    return res.status(400).json({
      error: "Task title is required"
    });
  }

  try {
    const task = await Task.create({ title });
    res.status(201).json(task);
  } catch (error) {
    next(error);
  }
});

app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({ error: "Internal server error" });
});


async function start() {
  await mongoose.connect(process.env.MONGO_URL);

  console.log("MongoDB connected");

  const port = Number(process.env.PORT) || 3000;

  app.listen(port, "0.0.0.0", () => {
    console.log(`Task API v3 listening on port ${port}`);
  });
}

start().catch((error) => {
  console.error("Application startup failed:", error.message);
  process.exit(1);
});
