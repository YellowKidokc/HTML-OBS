import { useState, useRef, useEffect, useCallback } from "react";

// ─── Mock file system ───
const MOCK_FS = [
  { path: "MDA/MDA-01-The-Signal.html", type: "html", series: "mda", order: 1 },
  { path: "MDA/MDA-02-The-Drift.html", type: "html", series: "mda", order: 2 },
  { path: "MDA/MDA-03-The-Collapse.html", type: "html", series: "mda", order: 3 },
  { path: "MDA/MDA-04-The-Silence.html", type: "html", series: "mda", order: 4 },
  { path: "MDA/MDA-05-The-Return.html", type: "html", series: "mda", order: 5 },
  { path: "MDA/assets/mda-cover.png", type: "image", series: "mda" },
  { path: "GTQ/GTQ-01-Genesis-Equation.html", type: "html", series: "gtq", order: 1 },
  { path: "GTQ/GTQ-02-Quantum-Covenant.html", type: "html", series: "gtq", order: 2 },
  { path: "GTQ/GTQ-03-The-Observer.html", type: "html", series: "gtq", order: 3 },
  { path: "GTQ/notes/research-log.md", type: "markdown" },
  { path: "GTQ/notes/quantum-refs.md", type: "markdown" },
  { path: "Canon/Ten-Laws-v4.html", type: "html" },
  { path: "Canon/Master-Equation.html", type: "html" },
  { path: "Canon/Fruits-Derivation.html", type: "html" },
  { path: "Canon/axiom-index.md", type: "markdown" },
  { path: "Media/sermon-clip-01.mp4", type: "video" },
  { path: "Media/podcast-interview.mp3", type: "audio" },
  { path: "Scripts/build-pipeline.js", type: "code" },
  { path: "Scripts/deploy.sh", type: "code" },
  { path: "Homepage/index.html", type: "html", series: "homepage" },
  { path: "Homepage/styles.css", type: "code" },
];

const SERIES_META = {
  mda: { name: "Moral Decline of America", color: "#c0392b", icon: "◆", home: "Homepage/index.html" },
  gtq: { name: "Genesis to Quantum", color: "#d4a017", icon: "◇", home: "Homepage/index.html" },
  homepage: { name: "Site Home", color: "#3498db", icon: "⌂" },
};

const TYPE_ICONS = {
  html: "⟨/⟩",
  markdown: "M↓",
  video: "▶",
  audio: "♪",
  image: "◻",
  code: "{ }",
};

const TYPE_COLORS = {
  html: "#e8a838",
  markdown: "#7ec8e3",
  video: "#c084fc",
  audio: "#f472b6",
  image: "#34d399",
  code: "#94a3b8",
};

const TYPE_FILTERS = ["All", "HTML", "Markdown", "Video", "Audio", "Image", "Code"];

// ─── Build tree from flat paths ───
function buildTree(files) {
  const root = { name: "", children: {}, files: [] };
  for (const f of files) {
    const parts = f.path.split("/");
    let node = root;
    for (let i = 0; i < parts.length - 1; i++) {
      if (!node.children[parts[i]]) node.children[parts[i]] = { name: parts[i], children: {}, files: [] };
      node = node.children[parts[i]];
    }
    node.files.push({ ...f, name: parts[parts.length - 1] });
  }
  return root;
}

// ─── Folder node ───
function FolderNode({ name, node, depth, selected, onSelect, expanded, onToggle, filter }) {
  const key = name;
  const isOpen = expanded[key] !== false;

  const filteredFiles = node.files.filter(f => filter === "all" || f.type === filter);
  const childKeys = Object.keys(node.children);
  const hasVisibleContent = filteredFiles.length > 0 || childKeys.some(() => true);

  if (!hasVisibleContent && childKeys.length === 0 && filteredFiles.length === 0) return null;

  return (
    <div>
      {name && (
        <div
          onClick={() => onToggle(key)}
          style={{
            display: "flex", alignItems: "center", gap: 6,
            padding: "5px 8px", paddingLeft: depth * 16 + 8,
            cursor: "pointer", fontSize: 13, fontWeight: 500,
            color: "#c8ccd4", letterSpacing: "0.01em",
            borderRadius: 4,
            transition: "background 0.15s",
          }}
          onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.04)"}
          onMouseLeave={e => e.currentTarget.style.background = "transparent"}
        >
          <span style={{
            fontSize: 9, color: "#6b7280", transition: "transform 0.15s",
            transform: isOpen ? "rotate(90deg)" : "rotate(0deg)",
            display: "inline-block", width: 10,
          }}>▶</span>
          <span style={{ color: "#8b95a5" }}>📁</span>
          <span>{name}</span>
          <span style={{ fontSize: 10, color: "#4b5563", marginLeft: "auto" }}>
            {node.files.length}
          </span>
        </div>
      )}
      {(isOpen || !name) && (
        <>
          {childKeys.sort().map(k => (
            <FolderNode
              key={k} name={k} node={node.children[k]}
              depth={name ? depth + 1 : depth}
              selected={selected} onSelect={onSelect}
              expanded={expanded} onToggle={onToggle}
              filter={filter}
            />
          ))}
          {filteredFiles.map(f => (
            <FileRow
              key={f.path} file={f} depth={name ? depth + 1 : depth}
              isSelected={selected?.path === f.path}
              onSelect={onSelect}
            />
          ))}
        </>
      )}
    </div>
  );
}

// ─── File row ───
function FileRow({ file, depth, isSelected, onSelect }) {
  const tc = TYPE_COLORS[file.type] || "#94a3b8";
  const seriesMeta = file.series ? SERIES_META[file.series] : null;

  return (
    <div
      onClick={() => onSelect(file)}
      style={{
        display: "flex", alignItems: "center", gap: 7,
        padding: "5px 8px", paddingLeft: depth * 16 + 26,
        cursor: "pointer", fontSize: 13,
        background: isSelected ? "rgba(228,168,56,0.1)" : "transparent",
        borderLeft: isSelected ? "2px solid #e8a838" : "2px solid transparent",
        color: isSelected ? "#e2e8f0" : "#9ca3af",
        borderRadius: "0 4px 4px 0",
        transition: "all 0.12s",
      }}
      onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = "rgba(255,255,255,0.03)"; }}
      onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = "transparent"; }}
    >
      <span style={{ fontSize: 10, color: tc, fontFamily: "monospace", fontWeight: 700, minWidth: 24 }}>
        {TYPE_ICONS[file.type]}
      </span>
      <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {file.name}
      </span>
      {seriesMeta && (
        <span style={{
          fontSize: 9, color: seriesMeta.color, opacity: 0.8,
          fontWeight: 600, letterSpacing: "0.03em",
        }}>
          {seriesMeta.icon}
        </span>
      )}
    </div>
  );
}

// ─── Series nav bar ───
function SeriesNav({ file, files, onSelect }) {
  if (!file?.series) return null;
  const meta = SERIES_META[file.series];
  const seriesFiles = files
    .filter(f => f.series === file.series && f.type === "html" && f.order)
    .sort((a, b) => a.order - b.order);
  const idx = seriesFiles.findIndex(f => f.path === file.path);
  const prev = idx > 0 ? seriesFiles[idx - 1] : null;
  const next = idx < seriesFiles.length - 1 ? seriesFiles[idx + 1] : null;

  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 10,
      padding: "6px 16px", fontSize: 12,
      background: `${meta.color}12`,
      borderBottom: `1px solid ${meta.color}30`,
      color: meta.color,
    }}>
      <span style={{ fontWeight: 700, letterSpacing: "0.05em", fontSize: 10, textTransform: "uppercase" }}>
        {meta.icon} {meta.name}
      </span>
      <span style={{ color: "#4b5563" }}>·</span>
      <span style={{ color: "#6b7280", fontSize: 11 }}>
        {idx + 1} of {seriesFiles.length}
      </span>
      <div style={{ marginLeft: "auto", display: "flex", gap: 4 }}>
        {meta.home && (
          <button
            onClick={() => { const h = files.find(f => f.path === meta.home); if (h) onSelect(h); }}
            style={{
              background: "transparent", border: `1px solid ${meta.color}40`,
              color: meta.color, borderRadius: 4, padding: "2px 8px",
              fontSize: 11, cursor: "pointer",
            }}
          >⌂ Home</button>
        )}
        <button
          disabled={!prev}
          onClick={() => prev && onSelect(prev)}
          style={{
            background: "transparent", border: `1px solid ${meta.color}40`,
            color: prev ? meta.color : "#333", borderRadius: 4, padding: "2px 10px",
            fontSize: 11, cursor: prev ? "pointer" : "default", opacity: prev ? 1 : 0.3,
          }}
        >← Prev</button>
        <button
          disabled={!next}
          onClick={() => next && onSelect(next)}
          style={{
            background: "transparent", border: `1px solid ${meta.color}40`,
            color: next ? meta.color : "#333", borderRadius: 4, padding: "2px 10px",
            fontSize: 11, cursor: next ? "pointer" : "default", opacity: next ? 1 : 0.3,
          }}
        >Next →</button>
      </div>
    </div>
  );
}

// ─── Context menu ───
function ContextMenu({ x, y, file, onClose, onAction }) {
  const ref = useRef();
  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) onClose(); };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onClose]);

  const items = [
    { label: "Open in new tab", action: "newtab" },
    file?.series && { label: `View ${SERIES_META[file.series]?.name} series`, action: "viewseries" },
    !file?.series && { label: "Add to series…", action: "addseries" },
    file?.series && { label: "Remove from series", action: "removeseries" },
    { divider: true },
    { label: "Set as series home", action: "sethome" },
    { label: "Link to homepage", action: "linkhome" },
    { divider: true },
    { label: "Rename", action: "rename" },
    { label: "Delete", action: "delete", danger: true },
  ].filter(Boolean);

  return (
    <div ref={ref} style={{
      position: "fixed", left: x, top: y, zIndex: 1000,
      background: "#1e2028", border: "1px solid #2d3040",
      borderRadius: 8, padding: "4px 0", minWidth: 200,
      boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
    }}>
      {items.map((item, i) => item.divider ? (
        <div key={i} style={{ height: 1, background: "#2d3040", margin: "4px 8px" }} />
      ) : (
        <div
          key={i}
          onClick={() => { onAction(item.action, file); onClose(); }}
          style={{
            padding: "7px 14px", fontSize: 13, cursor: "pointer",
            color: item.danger ? "#ef4444" : "#c8ccd4",
            transition: "background 0.1s",
          }}
          onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.06)"}
          onMouseLeave={e => e.currentTarget.style.background = "transparent"}
        >
          {item.label}
        </div>
      ))}
    </div>
  );
}

// ─── Main app ───
export default function HTMLNote() {
  const [files] = useState(MOCK_FS);
  const [selected, setSelected] = useState(null);
  const [filter, setFilter] = useState("all");
  const [expanded, setExpanded] = useState({});
  const [sidebarWidth, setSidebarWidth] = useState(260);
  const [ctxMenu, setCtxMenu] = useState(null);
  const [rootPath, setRootPath] = useState("D:\\GitHab\\HTML-OBS");
  const [editingRoot, setEditingRoot] = useState(false);
  const [tab, setTab] = useState("files"); // files | series | search
  const [searchQuery, setSearchQuery] = useState("");
  const dragRef = useRef(null);

  const tree = buildTree(
    filter === "all" ? files : files.filter(f => f.type === filter)
  );

  const toggleExpand = (key) => setExpanded(prev => ({ ...prev, [key]: prev[key] === false ? true : false }));

  const handleContextMenu = useCallback((e) => {
    e.preventDefault();
    // Find the file from the click target
    const row = e.target.closest("[data-filepath]");
    if (row) {
      const fp = row.dataset.filepath;
      const file = files.find(f => f.path === fp);
      setCtxMenu({ x: e.clientX, y: e.clientY, file });
    }
  }, [files]);

  // Resize handle
  const startDrag = (e) => {
    e.preventDefault();
    const startX = e.clientX;
    const startW = sidebarWidth;
    const onMove = (ev) => setSidebarWidth(Math.max(200, Math.min(500, startW + ev.clientX - startX)));
    const onUp = () => { document.removeEventListener("mousemove", onMove); document.removeEventListener("mouseup", onUp); };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  };

  // Count by type
  const counts = {};
  for (const f of files) counts[f.type] = (counts[f.type] || 0) + 1;

  // Series list
  const seriesList = Object.entries(SERIES_META).map(([key, meta]) => ({
    key,
    ...meta,
    count: files.filter(f => f.series === key).length,
    htmlCount: files.filter(f => f.series === key && f.type === "html").length,
  }));

  // Search filter
  const searchResults = searchQuery
    ? files.filter(f => f.path.toLowerCase().includes(searchQuery.toLowerCase()))
    : [];

  // Fake HTML content for preview
  const previewContent = selected?.type === "html" ? `
    <div style="font-family: 'Georgia', serif; max-width: 720px; margin: 0 auto; padding: 48px 32px; color: #e2e8f0;">
      <h1 style="font-size: 32px; font-weight: 300; letter-spacing: -0.02em; margin-bottom: 8px; color: #f1f5f9;">
        ${selected.name.replace(".html", "").replace(/-/g, " ")}
      </h1>
      ${selected.series ? `<div style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.1em; color: ${SERIES_META[selected.series].color}; margin-bottom: 32px; font-weight: 600;">${SERIES_META[selected.series].name} · Part ${selected.order || "—"}</div>` : ""}
      <p style="font-size: 17px; line-height: 1.7; color: #94a3af; margin-bottom: 24px;">
        This is the live preview panel. When connected to your file system, the actual HTML renders here — 
        full styling, scripts, embedded media, everything. Click a file in the sidebar to load it.
      </p>
      <p style="font-size: 17px; line-height: 1.7; color: #94a3af;">
        The series navigation bar above lets you move through linked documents. Right-click any file 
        in the sidebar to add it to a series, set reading order, or link it to a homepage.
      </p>
    </div>
  ` : null;

  return (
    <div style={{
      display: "flex", height: "100vh", width: "100vw",
      background: "#13141a", color: "#c8ccd4",
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      fontSize: 14, overflow: "hidden",
    }}>
      {/* ─── SIDEBAR ─── */}
      <div style={{
        width: sidebarWidth, minWidth: 200, display: "flex", flexDirection: "column",
        background: "#181a22", borderRight: "1px solid #1e2030",
      }}>
        {/* Header */}
        <div style={{ padding: "14px 12px 0", flexShrink: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 2 }}>
            <span style={{
              fontSize: 15, fontWeight: 700, letterSpacing: "-0.02em",
              background: "linear-gradient(135deg, #e8a838, #c0392b)",
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            }}>HTMLNote</span>
            <span style={{ fontSize: 10, color: "#4b5563", fontFamily: "monospace" }}>v0.2</span>
          </div>

          {/* Root path */}
          {editingRoot ? (
            <input
              autoFocus
              value={rootPath}
              onChange={e => setRootPath(e.target.value)}
              onBlur={() => setEditingRoot(false)}
              onKeyDown={e => e.key === "Enter" && setEditingRoot(false)}
              style={{
                width: "100%", background: "#0d0e14", border: "1px solid #2d3040",
                borderRadius: 4, padding: "4px 8px", fontSize: 11, color: "#9ca3af",
                fontFamily: "monospace", outline: "none", marginTop: 4, boxSizing: "border-box",
              }}
            />
          ) : (
            <div
              onClick={() => setEditingRoot(true)}
              style={{
                fontSize: 11, color: "#4b5563", fontFamily: "monospace",
                cursor: "pointer", padding: "4px 0", overflow: "hidden",
                textOverflow: "ellipsis", whiteSpace: "nowrap",
              }}
              title="Click to change root"
            >{rootPath}</div>
          )}

          {/* Sidebar tabs */}
          <div style={{
            display: "flex", gap: 0, marginTop: 10,
            borderBottom: "1px solid #1e2030",
          }}>
            {[
              { key: "files", label: "Files" },
              { key: "series", label: "Series" },
              { key: "search", label: "🔍" },
            ].map(t => (
              <button key={t.key} onClick={() => setTab(t.key)} style={{
                flex: t.key === "search" ? 0 : 1,
                padding: t.key === "search" ? "6px 12px" : "6px 0",
                background: "transparent", border: "none",
                borderBottom: tab === t.key ? "2px solid #e8a838" : "2px solid transparent",
                color: tab === t.key ? "#e2e8f0" : "#6b7280",
                fontSize: 12, fontWeight: tab === t.key ? 600 : 400,
                cursor: "pointer", transition: "all 0.15s",
              }}>{t.label}</button>
            ))}
          </div>
        </div>

        {/* Type filters (only in files tab) */}
        {tab === "files" && (
          <div style={{
            display: "flex", flexWrap: "wrap", gap: 4,
            padding: "8px 12px", borderBottom: "1px solid #1e2030",
          }}>
            {TYPE_FILTERS.map(t => {
              const key = t.toLowerCase();
              const active = filter === key || (t === "All" && filter === "all");
              const count = t === "All" ? files.length : counts[key] || 0;
              const col = t === "All" ? "#e8a838" : TYPE_COLORS[key] || "#6b7280";
              return (
                <button
                  key={t}
                  onClick={() => setFilter(t === "All" ? "all" : key)}
                  style={{
                    padding: "3px 8px", fontSize: 11, fontWeight: 500,
                    background: active ? `${col}18` : "transparent",
                    border: `1px solid ${active ? `${col}50` : "#1e2030"}`,
                    color: active ? col : "#4b5563",
                    borderRadius: 12, cursor: "pointer",
                    transition: "all 0.12s",
                  }}
                >{t} <span style={{ opacity: 0.6 }}>{count}</span></button>
              );
            })}
          </div>
        )}

        {/* Scrollable content area */}
        <div style={{ flex: 1, overflowY: "auto", overflowX: "hidden", padding: "4px 0" }}>
          {tab === "files" && (
            <FolderNode
              name="" node={tree} depth={0}
              selected={selected} onSelect={setSelected}
              expanded={expanded} onToggle={toggleExpand}
              filter={filter === "all" ? "all" : filter}
            />
          )}

          {tab === "series" && (
            <div style={{ padding: "8px" }}>
              {seriesList.map(s => (
                <div key={s.key} style={{
                  padding: "10px 12px", marginBottom: 6,
                  background: `${s.color}08`, border: `1px solid ${s.color}20`,
                  borderRadius: 8, cursor: "pointer",
                }}
                  onClick={() => { setFilter("all"); setTab("files"); }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ color: s.color, fontSize: 16 }}>{s.icon}</span>
                    <span style={{ fontWeight: 600, fontSize: 13, color: "#e2e8f0" }}>{s.name}</span>
                  </div>
                  <div style={{ fontSize: 11, color: "#6b7280", marginTop: 4 }}>
                    {s.htmlCount} articles · {s.count} total files
                  </div>
                </div>
              ))}
              <div style={{
                padding: "10px 12px", marginTop: 12,
                border: "1px dashed #2d3040", borderRadius: 8,
                color: "#4b5563", fontSize: 12, textAlign: "center",
                cursor: "pointer",
              }}
                onMouseEnter={e => e.currentTarget.style.borderColor = "#e8a838"}
                onMouseLeave={e => e.currentTarget.style.borderColor = "#2d3040"}
              >+ Create new series</div>
            </div>
          )}

          {tab === "search" && (
            <div style={{ padding: "8px" }}>
              <input
                autoFocus
                placeholder="Search files…"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                style={{
                  width: "100%", background: "#0d0e14", border: "1px solid #2d3040",
                  borderRadius: 6, padding: "8px 10px", fontSize: 13, color: "#e2e8f0",
                  outline: "none", boxSizing: "border-box", marginBottom: 8,
                }}
              />
              {searchResults.map(f => (
                <FileRow key={f.path} file={{ ...f, name: f.path }} depth={0}
                  isSelected={selected?.path === f.path} onSelect={setSelected} />
              ))}
              {searchQuery && searchResults.length === 0 && (
                <div style={{ padding: 16, color: "#4b5563", fontSize: 12, textAlign: "center" }}>
                  No files match "{searchQuery}"
                </div>
              )}
            </div>
          )}
        </div>

        {/* Status bar */}
        <div style={{
          padding: "6px 12px", borderTop: "1px solid #1e2030",
          fontSize: 10, color: "#3b4252", display: "flex", gap: 12,
          flexShrink: 0,
        }}>
          {Object.entries(counts).map(([type, count]) => (
            <span key={type} style={{ display: "flex", alignItems: "center", gap: 3 }}>
              <span style={{
                width: 6, height: 6, borderRadius: "50%",
                background: TYPE_COLORS[type], display: "inline-block",
              }} />
              {count} {type}
            </span>
          ))}
        </div>
      </div>

      {/* ─── RESIZE HANDLE ─── */}
      <div
        onMouseDown={startDrag}
        style={{
          width: 4, cursor: "col-resize", background: "transparent",
          transition: "background 0.2s", flexShrink: 0,
        }}
        onMouseEnter={e => e.currentTarget.style.background = "#e8a83840"}
        onMouseLeave={e => e.currentTarget.style.background = "transparent"}
      />

      {/* ─── MAIN PANEL ─── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {selected ? (
          <>
            {/* Series navigation */}
            <SeriesNav file={selected} files={files} onSelect={setSelected} />

            {/* File header */}
            <div style={{
              padding: "12px 20px", borderBottom: "1px solid #1e2030",
              display: "flex", alignItems: "center", gap: 12,
              background: "#181a22",
            }}>
              <span style={{
                fontSize: 11, color: TYPE_COLORS[selected.type],
                fontFamily: "monospace", fontWeight: 700,
              }}>{TYPE_ICONS[selected.type]}</span>
              <span style={{ fontSize: 14, fontWeight: 500, color: "#e2e8f0" }}>
                {selected.name}
              </span>
              <span style={{ fontSize: 11, color: "#3b4252", fontFamily: "monospace" }}>
                {selected.path}
              </span>
              <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
                <button style={{
                  background: "transparent", border: "1px solid #2d3040",
                  color: "#6b7280", borderRadius: 4, padding: "4px 10px",
                  fontSize: 11, cursor: "pointer",
                }}>Edit</button>
                <button style={{
                  background: "transparent", border: "1px solid #2d3040",
                  color: "#6b7280", borderRadius: 4, padding: "4px 10px",
                  fontSize: 11, cursor: "pointer",
                }}>AI Build</button>
                <button style={{
                  background: "#e8a83818", border: "1px solid #e8a83840",
                  color: "#e8a838", borderRadius: 4, padding: "4px 10px",
                  fontSize: 11, cursor: "pointer",
                }}>Export</button>
              </div>
            </div>

            {/* Preview */}
            <div style={{ flex: 1, overflow: "auto", background: "#0f1015" }}>
              {selected.type === "html" && (
                <div dangerouslySetInnerHTML={{ __html: previewContent }} />
              )}
              {selected.type === "markdown" && (
                <div style={{ padding: 32, color: "#94a3af", fontFamily: "'Georgia', serif", fontSize: 16, lineHeight: 1.8 }}>
                  <p>Markdown preview would render here. The file <code style={{ background: "#1e2030", padding: "2px 6px", borderRadius: 3, fontSize: 13 }}>{selected.name}</code> would be parsed and displayed with full formatting.</p>
                </div>
              )}
              {(selected.type === "video" || selected.type === "audio") && (
                <div style={{
                  display: "flex", flexDirection: "column", alignItems: "center",
                  justifyContent: "center", height: "100%", gap: 16, color: "#4b5563",
                }}>
                  <span style={{ fontSize: 48 }}>{selected.type === "video" ? "🎬" : "🎵"}</span>
                  <span style={{ fontSize: 14 }}>{selected.name}</span>
                  <span style={{ fontSize: 12 }}>Media player would load here</span>
                </div>
              )}
              {(selected.type === "code" || selected.type === "image") && (
                <div style={{
                  display: "flex", flexDirection: "column", alignItems: "center",
                  justifyContent: "center", height: "100%", gap: 16, color: "#4b5563",
                }}>
                  <span style={{ fontSize: 48 }}>{selected.type === "code" ? "💻" : "🖼"}</span>
                  <span style={{ fontSize: 14 }}>{selected.name}</span>
                </div>
              )}
            </div>
          </>
        ) : (
          /* Empty state */
          <div style={{
            flex: 1, display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center", gap: 20,
          }}>
            <div style={{
              width: 80, height: 80, borderRadius: 16,
              background: "linear-gradient(135deg, #e8a83810, #c0392b10)",
              border: "1px solid #e8a83815",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 32, color: "#e8a83840",
            }}>⟨/⟩</div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 16, fontWeight: 500, color: "#4b5563", marginBottom: 6 }}>
                Select a file to preview
              </div>
              <div style={{ fontSize: 13, color: "#2d3040", maxWidth: 320, lineHeight: 1.5 }}>
                HTML renders live. Markdown, video, audio, images, and code all supported.
                Right-click files to manage series and linking.
              </div>
            </div>
            <div style={{
              display: "flex", gap: 16, marginTop: 8,
            }}>
              {[
                { label: "New HTML", icon: "⟨/⟩", color: TYPE_COLORS.html },
                { label: "New Note", icon: "M↓", color: TYPE_COLORS.markdown },
                { label: "AI Create", icon: "✦", color: "#a78bfa" },
              ].map(b => (
                <button key={b.label} style={{
                  background: `${b.color}10`, border: `1px solid ${b.color}25`,
                  color: b.color, borderRadius: 8, padding: "10px 20px",
                  fontSize: 12, cursor: "pointer", display: "flex",
                  flexDirection: "column", alignItems: "center", gap: 6,
                }}>
                  <span style={{ fontSize: 18 }}>{b.icon}</span>
                  {b.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Context menu */}
      {ctxMenu && (
        <ContextMenu
          x={ctxMenu.x} y={ctxMenu.y} file={ctxMenu.file}
          onClose={() => setCtxMenu(null)}
          onAction={(action, file) => console.log(action, file)}
        />
      )}
    </div>
  );
}
