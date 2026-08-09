const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ─── Config ───
const ROOT = process.argv[2] || 'D:\\faiththruphysics.com';
const PORT = process.argv[3] || 3377;

const NUMERIC_PREFIX = /^(\d+)[-_. ]+/;

function readJson(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch { return {}; }
}

function readHtmlNoteMetadata(file) {
  if (!/\.html?$/i.test(file)) return {};
  try {
    const source = fs.readFileSync(file, 'utf8');
    const match = source.match(/<script\b[^>]*\bid=["']htmlnote-meta["'][^>]*>([\s\S]*?)<\/script>/i);
    return match ? JSON.parse(match[1]) : {};
  } catch { return {}; }
}

function displayName(name, metadata = {}) {
  return metadata.title || name.replace(NUMERIC_PREFIX, '').replace(/\.[^.]+$/, '').replace(/[-_]+/g, ' ');
}

function orderEntries(entries, folderConfig) {
  const manual = Array.isArray(folderConfig.children) ? folderConfig.children : [];
  const manualOrder = new Map(manual.map((name, index) => [name, index]));
  return entries.sort((a, b) => {
    const aManual = manualOrder.has(a.name) ? manualOrder.get(a.name) : Infinity;
    const bManual = manualOrder.has(b.name) ? manualOrder.get(b.name) : Infinity;
    if (aManual !== bManual) return aManual - bManual;

    const aOrder = Number.isFinite(Number(a.metadata?.order)) ? Number(a.metadata.order) : Infinity;
    const bOrder = Number.isFinite(Number(b.metadata?.order)) ? Number(b.metadata.order) : Infinity;
    if (aOrder !== bOrder) return aOrder - bOrder;

    const aPrefix = Number(a.name.match(NUMERIC_PREFIX)?.[1] ?? Infinity);
    const bPrefix = Number(b.name.match(NUMERIC_PREFIX)?.[1] ?? Infinity);
    if (aPrefix !== bPrefix) return aPrefix - bPrefix;
    if (a.type !== b.type) return a.type === 'folder' ? -1 : 1;
    return a.title.localeCompare(b.title, undefined, { numeric: true, sensitivity: 'base' });
  });
}

// ─── Recursive scan ───
function scanDir(dir, base = dir) {
  const entries = [];
  const folderConfig = readJson(path.join(dir, '_htmlnote.json'));
  let items;
  try { items = fs.readdirSync(dir, { withFileTypes: true }); }
  catch { return entries; }

  for (const item of items) {
    const full = path.join(dir, item.name);
    const rel = path.relative(base, full).replace(/\\/g, '/');

    if (item.isDirectory()) {
      // skip node_modules, .git, etc
      if (/^(node_modules|\.git|__pycache__)$/.test(item.name)) continue;
      const metadata = readJson(path.join(full, '_htmlnote.json'));
      if (metadata.hidden === true || metadata.draft === true) continue;
      entries.push({
        type: 'folder',
        name: item.name,
        title: displayName(item.name, metadata),
        path: rel,
        metadata,
        children: scanDir(full, base)
      });
    } else {
      if (item.name === '_htmlnote.json') continue;
      const ext = path.extname(item.name).toLowerCase();
      const metadata = readHtmlNoteMetadata(full);
      if (metadata.draft === true || metadata.hidden === true || metadata.headless === true) continue;
      const stat = fs.statSync(full);
      entries.push({
        type: 'file',
        name: item.name,
        title: displayName(item.name, metadata),
        path: rel,
        ext,
        size: stat.size,
        modified: stat.mtime.toISOString(),
        category: categorize(ext),
        metadata
      });
    }
  }

  // Deterministic precedence: folder sidecar → file metadata → numeric prefix → title.
  return orderEntries(entries, folderConfig);
}

function categorize(ext) {
  if (['.html', '.htm'].includes(ext)) return 'html';
  if (['.md', '.markdown', '.txt'].includes(ext)) return 'markdown';
  if (['.mp4', '.webm', '.mov', '.avi'].includes(ext)) return 'video';
  if (['.mp3', '.wav', '.ogg', '.m4a', '.flac'].includes(ext)) return 'audio';
  if (['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico'].includes(ext)) return 'image';
  if (['.css', '.js', '.json', '.xml'].includes(ext)) return 'code';
  if (['.pdf'].includes(ext)) return 'pdf';
  return 'other';
}

// ─── Version detection ───
// Groups files by stem, e.g. article.html, article_v2.html, article (copy).html
function detectVersions(tree) {
  const groups = {};

  function walk(nodes, parentPath) {
    for (const node of nodes) {
      if (node.type === 'folder') {
        walk(node.children, node.path);
      } else if (node.category === 'html') {
        // Strip version suffixes to find the base name
        const dir = parentPath || '';
        const base = node.name
          .replace(/\.(html|htm)$/i, '')
          .replace(/[_\- ]*(v\d+|copy|backup|old|new|final|draft|rev\d*|\(\d+\))$/i, '')
          .toLowerCase()
          .trim();
        const key = dir ? `${dir}/${base}` : base;
        if (!groups[key]) groups[key] = [];
        groups[key].push(node);
      }
    }
  }

  walk(tree, '');
  return groups;
}

// ─── Flatten for search ───
function flattenTree(tree, result = []) {
  for (const node of tree) {
    result.push(node);
    if (node.type === 'folder' && node.children) {
      flattenTree(node.children, result);
    }
  }
  return result;
}

// ─── Rename file ───
function renameFile(oldRel, newName) {
  const oldFull = path.join(ROOT, oldRel);
  const dir = path.dirname(oldFull);
  const newFull = path.join(dir, newName);
  if (fs.existsSync(newFull)) return { error: 'Target already exists' };
  fs.renameSync(oldFull, newFull);
  return { ok: true, newPath: path.relative(ROOT, newFull).replace(/\\/g, '/') };
}

// ─── Simple markdown→HTML ───
function renderMarkdown(text) {
  return text
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>');
}

// ─── HTTP Server ───
const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);

  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.writeHead(200); res.end(); return; }

  // API routes
  if (url.pathname === '/api/tree') {
    const tree = scanDir(ROOT);
    const versions = detectVersions(tree);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ root: ROOT, tree, versions }));
    return;
  }

  if (url.pathname === '/api/file') {
    const relPath = url.searchParams.get('path');
    if (!relPath) { res.writeHead(400); res.end('Missing path'); return; }
    const fullPath = path.join(ROOT, relPath);
    // Security: prevent traversal
    if (!fullPath.startsWith(ROOT)) { res.writeHead(403); res.end('Forbidden'); return; }
    if (!fs.existsSync(fullPath)) { res.writeHead(404); res.end('Not found'); return; }

    const ext = path.extname(fullPath).toLowerCase();
    const cat = categorize(ext);

    if (cat === 'html') {
      const content = fs.readFileSync(fullPath, 'utf-8');
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(content);
    } else if (cat === 'markdown') {
      const content = fs.readFileSync(fullPath, 'utf-8');
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ raw: content, html: renderMarkdown(content) }));
    } else if (cat === 'video' || cat === 'audio' || cat === 'image' || cat === 'pdf') {
      // Stream binary
      const stat = fs.statSync(fullPath);
      const mimeMap = {
        '.mp4': 'video/mp4', '.webm': 'video/webm', '.mov': 'video/quicktime',
        '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.ogg': 'audio/ogg',
        '.m4a': 'audio/mp4', '.flac': 'audio/flac',
        '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.gif': 'image/gif', '.svg': 'image/svg+xml', '.webp': 'image/webp',
        '.pdf': 'application/pdf'
      };
      res.writeHead(200, {
        'Content-Type': mimeMap[ext] || 'application/octet-stream',
        'Content-Length': stat.size
      });
      fs.createReadStream(fullPath).pipe(res);
    } else {
      const content = fs.readFileSync(fullPath, 'utf-8');
      res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end(content);
    }
    return;
  }

  if (url.pathname === '/api/rename' && req.method === 'POST') {
    let body = '';
    req.on('data', c => body += c);
    req.on('end', () => {
      try {
        const { oldPath, newName } = JSON.parse(body);
        const result = renameFile(oldPath, newName);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result));
      } catch (e) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: e.message }));
      }
    });
    return;
  }

  // Serve static frontend
  const staticDir = path.join(__dirname, 'public');
  let filePath = path.join(staticDir, url.pathname === '/' ? 'index.html' : url.pathname);
  if (!fs.existsSync(filePath)) {
    filePath = path.join(staticDir, 'index.html'); // SPA fallback
  }

  const extS = path.extname(filePath).toLowerCase();
  const mimes = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml' };
  res.writeHead(200, { 'Content-Type': mimes[extS] || 'text/plain' });
  fs.createReadStream(filePath).pipe(res);
});

server.listen(PORT, () => {
  console.log(`\n  ╔══════════════════════════════════════╗`);
  console.log(`  ║  HTMLNote — scanning:                 ║`);
  console.log(`  ║  ${ROOT.padEnd(36)}║`);
  console.log(`  ║                                      ║`);
  console.log(`  ║  Open: http://localhost:${String(PORT).padEnd(13)}║`);
  console.log(`  ╚══════════════════════════════════════╝\n`);
});
