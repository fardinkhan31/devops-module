const databaseName = process.env.MONGO_INITDB_DATABASE || "taskdb";

const appUsername = process.env.MONGO_APP_USERNAME;
const appPassword = process.env.MONGO_APP_PASSWORD;

if (!appUsername || !appPassword) {
	throw new Error("Application database credentials are missing");
}

const appDb = db.getSiblingDB(databaseName);

appDb.createUser({
	user: appUsername,
	pwd: appPassword,
	roles: [
		{ role: "readWrite", db : databaseName}
	]
});

print("Application database user created");
