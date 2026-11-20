/**
 * AgriGuard Demo Proxy Server
 * ===========================
 * Serves the pre-built Expo web bundle and proxies API calls:
 *   /api/v1/*  → backend FastAPI  (port 8000)
 *   /api/ai/*  → AI FastAPI       (port 5000)
 *   /uploads/* → backend uploads  (port 8000)
 *
 * Run with:  node proxy.js
 */

const http = require("http");
const https = require("https");
const fs = require("fs");
const path = require("path");
const url = require("url");

// ── Config ──────────────────────────────────────────────────────────────────
const PROXY_PORT   = parseInt(process.env.PROXY_PORT   || "3000", 10);
const BACKEND_PORT = parseInt(process.env.BACKEND_PORT || "8000", 10);
const AI_PORT      = parseInt(process.env.AI_PORT      || "5000", 10);
const DIST_DIR     = path.resolve(__dirname, "../frontend/dist");

// MIME types for static file serving
const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js":   "application/javascript; charset=utf-8",
  ".css":  "text/css; charset=utf-8",
  ".json": "application/json",
  ".png":  "image/png",
  ".jpg":  "image/jpeg",
  ".jpeg": "image/jpeg",
  ".ico":  "image/x-icon",
  ".ttf":  "font/ttf",
  ".otf":  "font/otf",
  ".woff": "font/woff",
  ".woff2":"font/woff2",
  ".svg":  "image/svg+xml",
  ".webp": "image/webp",
  ".txt":  "text/plain",
};

// ── Proxy helper ─────────────────────────────────────────────────────────────
function proxyRequest(req, res, targetPort, pathOverride) {
  const targetPath = pathOverride || req.url;

  const options = {
    hostname: "127.0.0.1",
    port: targetPort,
    path: targetPath,
    method: req.method,
    headers: { ...req.headers, host: `127.0.0.1:${targetPort}` },
  };

  const proxyReq = http.request(options, (proxyRes) => {
    // Forward CORS headers for tunnel access
    const headers = { ...proxyRes.headers };
    headers["access-control-allow-origin"]  = "*";
    headers["access-control-allow-headers"] = "Content-Type, Authorization";
    headers["access-control-allow-methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH";

    res.writeHead(proxyRes.statusCode || 502, headers);
    proxyRes.pipe(res, { end: true });
  });

  proxyReq.on("error", (err) => {
    console.error(`[proxy] Error forwarding to :${targetPort} — ${err.message}`);
    if (!res.headersSent) {
      res.writeHead(502, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "Service unavailable", detail: err.message }));
    }
  });

  // Increase body size limit to 20 MB (for image uploads)
  let bodySize = 0;
  req.on("data", (chunk) => {
    bodySize += chunk.length;
    if (bodySize > 20 * 1024 * 1024) {
      proxyReq.destroy(new Error("Request body too large"));
    } else {
      proxyReq.write(chunk);
    }
  });
  req.on("end", () => proxyReq.end());
  req.on("error", (err) => proxyReq.destroy(err));
}

// ── Static file helper ───────────────────────────────────────────────────────
function serveStatic(req, res) {
  let filePath = path.join(DIST_DIR, url.parse(req.url).pathname);

  // Try exact path, then index.html fallback for SPA routing
  const tryPaths = [filePath, path.join(DIST_DIR, "index.html")];

  function tryNext(paths) {
    if (paths.length === 0) {
      res.writeHead(404);
      res.end("Not found");
      return;
    }
    const p = paths[0];
    fs.stat(p, (err, stat) => {
      if (err || stat.isDirectory()) {
        tryNext(paths.slice(1));
        return;
      }
      const ext  = path.extname(p).toLowerCase();
      const mime = MIME[ext] || "application/octet-stream";
      res.writeHead(200, { "Content-Type": mime });
      fs.createReadStream(p).pipe(res);
    });
  }

  tryNext(tryPaths);
}

// ── Request router ───────────────────────────────────────────────────────────
const server = http.createServer((req, res) => {
  const { pathname } = url.parse(req.url);

  // Handle CORS preflight globally
  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "access-control-allow-origin":  "*",
      "access-control-allow-methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
      "access-control-allow-headers": "Content-Type, Authorization",
      "access-control-max-age":       "86400",
    });
    res.end();
    return;
  }

  // /api/ai/* → AI service (port 5000)
  if (pathname.startsWith("/api/ai")) {
    proxyRequest(req, res, AI_PORT);
    return;
  }

  // /api/v1/* → backend (port 8000)
  if (pathname.startsWith("/api/v1") || pathname.startsWith("/api")) {
    proxyRequest(req, res, BACKEND_PORT);
    return;
  }

  // /uploads/* → backend static uploads (port 8000)
  if (pathname.startsWith("/uploads")) {
    proxyRequest(req, res, BACKEND_PORT);
    return;
  }

  // /health → proxy own health
  if (pathname === "/proxy-health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", proxy_port: PROXY_PORT }));
    return;
  }

  // Everything else → static frontend files
  serveStatic(req, res);
});

server.listen(PROXY_PORT, "0.0.0.0", () => {
  console.log(`\n✅ AgriGuard Proxy ready on http://localhost:${PROXY_PORT}`);
  console.log(`   Frontend : serving ${DIST_DIR}`);
  console.log(`   Backend  : proxying /api/v1/* → :${BACKEND_PORT}`);
  console.log(`   AI       : proxying /api/ai/* → :${AI_PORT}`);
});

server.on("error", (err) => {
  console.error(`[proxy] Server error: ${err.message}`);
  process.exit(1);
});
