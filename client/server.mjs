// @ts-check

import Fastify from "fastify";
import fastifyStatic from "@fastify/static";
import { join } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = join(__filename, "..");
const port = 8001;

const fastify = Fastify({
  logger: true,
});

// Register static file plugin
fastify.register(fastifyStatic, {
  root: join(__dirname, "public"),
  prefix: "/", // optional: default '/'
});

// Serve index.html for the root
fastify.get("/", (req, reply) => {
  reply.sendFile("index.html");
});

const start = async () => {
  try {
    await fastify.listen({
        host: "0.0.0.0",
        port,
    });
    console.log("Server running: http://localhost:"+port);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();
