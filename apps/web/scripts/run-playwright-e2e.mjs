import { spawn } from "node:child_process";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { setTimeout as sleep } from "node:timers/promises";

const appDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const port = Number(process.env.PLAYWRIGHT_PORT ?? process.env.PORT ?? "3100");
const baseURL = `http://127.0.0.1:${port}`;
const cliArgs = process.argv.slice(2);
if (cliArgs[0] === "--") {
  cliArgs.shift();
}

function spawnCommand(command, args, options = {}) {
  return spawn(command, args, {
    cwd: appDir,
    env: { ...process.env, ...options.env },
    stdio: options.stdio ?? "inherit",
    windowsHide: true,
  });
}

async function waitForPort(host, targetPort, timeoutMs = 60_000) {
  const startedAt = Date.now();

  while (Date.now() - startedAt < timeoutMs) {
    const isOpen = await new Promise((resolve) => {
      const socket = net.createConnection({ host, port: targetPort });
      socket.once("connect", () => {
        socket.end();
        resolve(true);
      });
      socket.once("error", () => {
        socket.destroy();
        resolve(false);
      });
    });

    if (isOpen) return;
    await sleep(500);
  }

  throw new Error(`Timed out waiting for http://127.0.0.1:${targetPort}`);
}

function waitForExit(child) {
  return new Promise((resolve, reject) => {
    child.once("error", reject);
    child.once("exit", (code, signal) => resolve({ code, signal }));
  });
}

async function runCommand(command, args, options = {}) {
  const child = spawnCommand(command, args, options);
  const { code, signal } = await waitForExit(child);

  if (signal) {
    throw new Error(`${command} exited with signal ${signal}`);
  }

  if (code !== 0) {
    throw new Error(`${command} exited with code ${code}`);
  }
}

async function waitForServer(child, host, targetPort, timeoutMs = 60_000) {
  const exitPromise = waitForExit(child).then(({ code, signal }) => {
    throw new Error(
      `next start exited before ${baseURL} was reachable (code ${code ?? "n/a"}, signal ${
        signal ?? "n/a"
      })`,
    );
  });

  await Promise.race([waitForPort(host, targetPort, timeoutMs), exitPromise]);
}

async function terminateServer(child) {
  if (!child || child.exitCode !== null) return;

  child.kill("SIGTERM");
  const result = await Promise.race([
    waitForExit(child),
    sleep(5_000).then(() => null),
  ]);

  if (result) return;

  if (process.platform === "win32") {
    await new Promise((resolve) => {
      const killer = spawn("taskkill", ["/PID", String(child.pid), "/T", "/F"], {
        stdio: "ignore",
        windowsHide: true,
      });
      killer.once("exit", () => resolve());
      killer.once("error", () => resolve());
    });
    return;
  }

  child.kill("SIGKILL");
}

await runCommand(
  process.execPath,
  ["./node_modules/next/dist/bin/next", "build"],
  { stdio: "inherit" },
);

const nextServer = spawnCommand(
  process.execPath,
  ["./node_modules/next/dist/bin/next", "start", "--port", String(port)],
  { stdio: "inherit" },
);

try {
  await waitForServer(nextServer, "127.0.0.1", port);

  const runner = spawnCommand(
    process.execPath,
    ["./node_modules/@playwright/test/cli.js", "test", ...cliArgs],
    {
      env: {
        PLAYWRIGHT_SKIP_WEBSERVER: "1",
        PLAYWRIGHT_BASE_URL: baseURL,
      },
      stdio: "inherit",
    },
  );

  const { code, signal } = await waitForExit(runner);

  if (signal) {
    throw new Error(`Playwright exited with signal ${signal}`);
  }

  process.exitCode = code ?? 1;
} finally {
  await terminateServer(nextServer);
}
