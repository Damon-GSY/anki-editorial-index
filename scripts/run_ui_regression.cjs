const fs = require("node:fs/promises");
const http = require("node:http");
const path = require("node:path");
const { spawn } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const host = "127.0.0.1";
const requestedPort = Number.parseInt(process.env.PREVIEW_PORT || "0", 10);
const mimeTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".ttf": "font/ttf",
  ".woff2": "font/woff2",
};

const server = http.createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url, `http://${host}`).pathname);
    const filePath = path.resolve(root, pathname.replace(/^\/+/, ""));
    if (filePath !== root && !filePath.startsWith(`${root}${path.sep}`)) {
      response.writeHead(403).end("Forbidden");
      return;
    }
    const body = await fs.readFile(filePath);
    response.writeHead(200, {
      "content-type": mimeTypes[path.extname(filePath)] || "application/octet-stream",
      "cache-control": "no-store",
    });
    response.end(body);
  } catch (error) {
    response.writeHead(error.code === "ENOENT" ? 404 : 500).end("Not found");
  }
});

function listen() {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(requestedPort, host, resolve);
  });
}

function closeServer() {
  return new Promise((resolve) => server.close(resolve));
}

function run(script, previewUrl, environmentName = "PREVIEW_URL") {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [script], {
      cwd: root,
      env: { ...process.env, [environmentName]: previewUrl },
      stdio: "inherit",
    });
    let settled = false;
    const finish = (callback, value) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      callback(value);
    };
    const timeout = setTimeout(() => {
      child.kill("SIGTERM");
      finish(reject, new Error(`${script} exceeded the 240s UI regression timeout`));
    }, 240_000);
    child.once("error", error => finish(reject, error));
    child.once("exit", (code, signal) => {
      if (code === 0) finish(resolve);
      else finish(reject, new Error(`${script} failed (${signal || code})`));
    });
  });
}

(async () => {
  await listen();
  const address = server.address();
  const baseUrl = `http://${host}:${address.port}`;

  try {
    const suites = [
      run(
        "design-exploration/production-preview/verify.cjs",
        `${baseUrl}/design-exploration/production-preview/index.html`,
      ),
      run(
        "design-exploration/editor-preview/verify.cjs",
        `${baseUrl}/design-exploration/editor-preview/index.html`,
        "EDITOR_PREVIEW_URL",
      ),
      run(
        "design-exploration/standalone-preview/verify.cjs",
        `${baseUrl}/design-exploration/standalone-preview/index.html`,
        "STANDALONE_PREVIEW_URL",
      ),
    ];
    const results = await Promise.allSettled(suites);
    const failures = results.filter(result => result.status === "rejected");
    if (failures.length) {
      throw new Error(failures.map(result => result.reason?.message || String(result.reason)).join("\n"));
    }
    console.log("Editorial Index UI regression tests passed");
  } finally {
    await closeServer();
  }
})().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
