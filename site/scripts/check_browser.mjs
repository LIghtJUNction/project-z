#!/usr/bin/env node
// Browser acceptance in a new, unsigned-in Chromium profile. No npm dependencies.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";
import fs from "node:fs/promises";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const site = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const output = path.join(site, "_validation");
await fs.mkdir(output, { recursive: true });
const profile = await fs.mkdtemp(path.join(os.tmpdir(), "project-z-page-browser-"));
const allowed = new Set(["index.html", "style.css", "app.js", "favicon.svg", "projects.json", ".nojekyll"]);
const types = { ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml" };
const server = http.createServer(async (request, response) => {
  const url = new URL(request.url, "http://127.0.0.1");
  const filename = url.pathname === "/project-z-site/" ? "index.html" : url.pathname.slice("/project-z-site/".length);
  if (!url.pathname.startsWith("/project-z-site/") || !allowed.has(filename)) {
    response.writeHead(404).end("Not found");
    return;
  }
  try {
    response.writeHead(200, { "Content-Type": types[path.extname(filename)] || "text/plain", "Cache-Control": "no-store" });
    response.end(await fs.readFile(path.join(site, "dist", filename)));
  } catch {
    response.writeHead(500).end("Site build missing");
  }
});
server.listen(0, "127.0.0.1");
await once(server, "listening");
const base = `http://127.0.0.1:${server.address().port}/project-z-site/`;
const log = await fs.open(path.join(output, "chromium.log"), "w");
const browser = spawn(process.env.CHROMIUM || "chromium", [
  "--headless=new", "--no-first-run", "--no-default-browser-check",
  "--disable-extensions", "--disable-background-networking", "--disable-component-update",
  "--disable-default-apps", "--disable-sync", "--remote-debugging-address=127.0.0.1",
  "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank",
], { stdio: ["ignore", log.fd, log.fd] });
let socket;
let sequence = 0;
const pending = new Map();
const events = new Map();
const errors = [];
const requests = new Set();
const report = { schema: "project-z.browser-check.v1", checks: [], screenshots: [], origin: "isolated localhost project subpath" };
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
function nextEvent(name) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("CDP event timeout: " + name)), 15000);
    const callback = value => { clearTimeout(timer); resolve(value); };
    events.set(name, [...(events.get(name) || []), callback]);
  });
}
function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error("CDP timeout: " + method)); }, 15000);
    pending.set(id, { resolve: value => { clearTimeout(timer); resolve(value); }, reject: error => { clearTimeout(timer); reject(error); } });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}
async function navigate(url = base) {
  const loaded = nextEvent("Page.loadEventFired");
  await send("Page.navigate", { url });
  await loaded;
  await evaluate("document.fonts.ready.then(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))))");
  await evaluate("document.documentElement.style.scrollBehavior = 'auto'");
}
async function viewport(width, height, mobile = false) {
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile, screenWidth: width, screenHeight: height });
  await send("Emulation.setTouchEmulationEnabled", { enabled: mobile });
}
async function key(key, code, number, modifiers = 0) {
  for (const type of ["keyDown", "keyUp"]) {
    const text = type === "keyDown" && key === "Enter" ? "\r" : undefined;
    await send("Input.dispatchKeyEvent", { type, key, code, windowsVirtualKeyCode: number, modifiers, ...(text ? { text, unmodifiedText: text } : {}) });
  }
}
async function type(text) { await send("Input.insertText", { text }); }
async function replace(text) {
  await key("a", "KeyA", 65, 2);
  await type(text);
}
async function visible() {
  return evaluate("[...document.querySelectorAll('#project-list > li:not([hidden])')].map(item => item.dataset.project)");
}
async function screenshot(name) {
  const result = await send("Page.captureScreenshot", { format: "jpeg", quality: 86, fromSurface: true, captureBeyondViewport: false });
  const filename = name + ".jpg";
  await fs.writeFile(path.join(output, filename), Buffer.from(result.data, "base64"));
  report.screenshots.push(filename);
}
async function noOverflow(label) {
  const dimensions = await evaluate("({ viewport: innerWidth, document: document.documentElement.scrollWidth })");
  assert.ok(dimensions.document <= dimensions.viewport, label + " has horizontal overflow: " + JSON.stringify(dimensions));
  report.checks.push(label + " has no horizontal overflow");
}
try {
  let port;
  for (let tries = 0; tries < 100; tries += 1) {
    try { port = Number((await fs.readFile(path.join(profile, "DevToolsActivePort"), "utf8")).split("\n")[0]); break; } catch {}
    if (browser.exitCode !== null) throw new Error("Chromium exited before exposing the isolated debugging port");
    await pause(100);
  }
  if (!port) throw new Error("Chromium did not start");
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const target = targets.find(item => item.type === "page");
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await once(socket, "open");
  socket.addEventListener("message", event => {
    const message = JSON.parse(event.data);
    if (message.id) {
      const item = pending.get(message.id);
      if (!item) return;
      pending.delete(message.id);
      if (message.error) item.reject(new Error(JSON.stringify(message.error))); else item.resolve(message.result);
    } else {
      if (message.method === "Runtime.exceptionThrown") errors.push(message.params.exceptionDetails.text);
      if (message.method === "Network.requestWillBeSent") requests.add(message.params.request.url);
      for (const callback of events.get(message.method) || []) callback(message.params);
      events.delete(message.method);
    }
  });
  for (const domain of ["Page", "Runtime", "Network", "Accessibility"]) await send(domain + ".enable");
  await send("Network.setCacheDisabled", { cacheDisabled: true });
  report.browser = await send("Browser.getVersion");
  await viewport(1440, 1000);
  await navigate();
  const snapshot = JSON.parse(await fs.readFile(path.join(site, "projects.json"), "utf8"));
  const count = snapshot.projects.length;
  assert.equal((await visible()).length, count);
  assert.equal(await evaluate("document.querySelectorAll('.crate-link').length"), snapshot.projects.filter(item => item.crate).length);
  await noOverflow("desktop 1440");
  await screenshot("desktop");
  await evaluate("window.scrollTo(0, document.querySelector('#projects').offsetTop - 24)");
  await screenshot("desktop-projects");

  await key("/", "Slash", 191);
  assert.equal(await evaluate("document.activeElement.id"), "project-search");
  await type("zgpui");
  assert.deepEqual(await visible(), ["zgpui"]);
  assert.match(await evaluate("document.querySelector('#result-count').textContent"), /1 \/ /);
  await key("Escape", "Escape", 27);
  assert.equal((await visible()).length, count);
  await key("Tab", "Tab", 9);
  assert.equal(await evaluate("document.activeElement.dataset.category"), "all");
  await key("Tab", "Tab", 9);
  assert.equal(await evaluate("document.activeElement.dataset.category"), "interface");
  await key("Enter", "Enter", 13);
  assert.equal((await visible()).length, snapshot.projects.filter(item => item.category === "interface").length);
  await key("/", "Slash", 191);
  await type("输入");
  assert.deepEqual((await visible()).sort(), ["zinput", "ztype"]);
  const shared = await evaluate("location.href");
  await navigate(shared);
  assert.deepEqual((await visible()).sort(), ["zinput", "ztype"]);
  await key("/", "Slash", 191);
  await replace("zzzz不存在");
  assert.equal((await visible()).length, 0);
  assert.equal(await evaluate("document.querySelector('#empty-state').hidden"), false);
  await screenshot("empty-results");
  await evaluate("document.querySelector('#empty-reset').focus()");
  await key("Enter", "Enter", 13);
  assert.equal((await visible()).length, count);
  assert.equal(await evaluate("document.activeElement.id"), "project-search");
  await type("ｚｇｐｕｉ");
  assert.deepEqual(await visible(), ["zgpui"]);
  await key("Escape", "Escape", 27);
  report.checks.push("keyboard search, Escape reset, Tab/Enter category selection", "Chinese search and shared URL state", "empty results and keyboard recovery", "full-width search normalization");

  const tree = await send("Accessibility.getFullAXTree");
  const roles = tree.nodes.filter(node => !node.ignored).map(node => node.role?.value);
  assert.ok(roles.includes("searchbox") && roles.includes("main") && roles.includes("navigation"));
  report.checks.push("named search, navigation and main landmarks in accessibility tree");
  await evaluate("document.querySelector('.theme-toggle').focus()");
  await key("Enter", "Enter", 13);
  assert.equal(await evaluate("document.documentElement.dataset.theme"), "light");
  await evaluate("window.scrollTo(0, 0)");
  await screenshot("desktop-light");
  await navigate();
  assert.equal(await evaluate("document.documentElement.dataset.theme"), "light");
  await evaluate("document.querySelector('.theme-toggle').focus()");
  await key("Enter", "Enter", 13);
  assert.equal(await evaluate("document.documentElement.dataset.theme"), "dark");
  report.checks.push("keyboard theme toggle and persisted warm light/dark preference");
  await viewport(768, 1024);
  await navigate();
  await noOverflow("tablet 768");
  await viewport(390, 844, true);
  await navigate();
  await noOverflow("mobile 390");
  await screenshot("mobile");
  await evaluate("window.scrollTo(0, document.querySelector('#projects').offsetTop - 16)");
  await screenshot("mobile-projects");
  await key("/", "Slash", 191);
  await type("zrc");
  assert.deepEqual(await visible(), ["zrc"]);
  const crateHref = await evaluate("document.querySelector('[data-project=zrc] .crate-link')?.href");
  const zrcVersion = snapshot.projects.find(item => item.id === "zrc").crate;
  assert.equal(crateHref, zrcVersion.url);
  report.checks.push("mobile search reaches the verified zrc " + zrcVersion.version + " registry entry");
  await viewport(320, 800, true);
  await navigate();
  await noOverflow("narrow mobile 320");

  await viewport(1280, 900);
  await send("Network.setBlockedURLs", { urls: [base + "app.js"] });
  await navigate(base + "?script-blocked=1");
  assert.equal((await visible()).length, count);
  assert.equal(await evaluate("document.querySelector('.project-controls').hidden"), true);
  await screenshot("javascript-unavailable");
  await send("Network.setBlockedURLs", { urls: [] });
  report.checks.push("all projects and links remain available when JavaScript fails to load");

  await send("Emulation.setScriptExecutionDisabled", { value: true });
  const loaded = nextEvent("Page.loadEventFired");
  await send("Page.navigate", { url: base + "?javascript-disabled=1" });
  await loaded;
  const document = await send("DOM.getDocument", { depth: -1, pierce: true });
  let staticCards = 0;
  function walk(node) {
    if (node.attributes?.includes("data-project")) staticCards += 1;
    for (const child of node.children || []) walk(child);
  }
  walk(document.root);
  assert.equal(staticCards, count);
  await screenshot("javascript-disabled");
  await send("Emulation.setScriptExecutionDisabled", { value: false });
  report.checks.push("complete pre-rendered project list with JavaScript disabled");

  assert.deepEqual(errors, []);
  const external = [...requests].filter(url => !url.startsWith(base) && !url.startsWith("data:"));
  assert.deepEqual(external, []);
  report.checks.push("no page JavaScript exceptions", "no external page requests, fonts, analytics or runtime APIs");
  report.projects = count;
  report.verified_crates = snapshot.projects.filter(item => item.crate).length;
  report.result = "passed";
  await fs.writeFile(path.join(output, "browser-validation.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify(report, null, 2));
} catch (error) {
  report.result = "failed";
  report.error = error.stack;
  await fs.writeFile(path.join(output, "browser-validation.json"), JSON.stringify(report, null, 2) + "\n");
  throw error;
} finally {
  socket?.close();
  browser.kill("SIGTERM");
  await Promise.race([once(browser, "exit").catch(() => {}), pause(3000)]);
  server.closeAllConnections();
  server.close();
  await log.close();
  await fs.rm(profile, { recursive: true, force: true });
}
