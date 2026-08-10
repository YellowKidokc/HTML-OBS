# HTMLNote

Obsidian-style notebook viewer for HTML files. Zero dependencies — just Node.

## Run it

```
start.bat
```

Or manually:
```
node server.js "D:\faiththruphysics.com" 3377
```

Then open http://localhost:3377

## What it does

- Recursively scans your folder
- Color-coded by file type (HTML, markdown, video, audio, image, code)
- HTML files render live in an iframe
- Video/audio play inline
- Markdown renders with basic formatting
- Version detection — groups files like `article.html`, `article_v2.html`, `article_final.html` and lets you switch between them
- Search and filter by type
- Right-click to rename or copy path
- Ctrl+F to focus search
- Calm light/dark themes and comfortable/compact density, persisted per browser
- Deterministic navigation ordering and human-friendly display titles

## Navigation metadata

HTMLNote never relies on filesystem enumeration order. Items are sorted by this
precedence chain: a folder's `_htmlnote.json` child list, an item's `order`
metadata, a zero-padded numeric filename prefix, then its display title.

Use a sidecar to control an entire folder:

```json
{
  "title": "Guides",
  "children": ["index.html", "01-getting-started.html"]
}
```

HTML files can carry valid, self-contained metadata:

```html
<script type="application/json" id="htmlnote-meta">
{ "title": "Getting started", "order": 10, "draft": false }
</script>
```

Set `draft`, `hidden`, or `headless` to `true` to keep an item out of navigation.
Numeric prefixes such as `01-` are removed from display labels but remain in the
filename for stable URLs, operating-system sorting, and visible Git diffs.

## Design tokens and theming

`tokens.json` is the canonical DTCG-shaped primitive → semantic → component
token source. The runtime theme surface lives in `public/design-system.css`.
Components consume semantic/component variables; user themes should override
only the documented, non-structural semantic properties at `:root`.

### Appearance panel (two-surface theming)

The ⚙ button opens an appearance panel modeled on the "lock structure, expose
cosmetics" pattern from VS Code and Obsidian. It edits a **whitelist** of
semantic tokens only:

- theme (`light` / `dark` / `contrast`) and density (`comfortable` / `compact`)
- accent hue / saturation / lightness (`--accent-h/-s/-l`)
- interface and reading font stacks (`--font-interface-theme`, `--font-text-theme`)
- reading font size (`--reading-font-size`) and corner radius (`--radius-s/m/l`)

The `ALLOWED_PROPS` set in `index.html` is the enforced boundary — any property
outside it is refused before it reaches the DOM, so a custom look can recolor
and re-space the reading surface but never move or break the interface.
Selections persist per browser under the `htmlnote-appearance` key, and "Reset
to defaults" removes every override so the stylesheet defaults (and the OS
light/dark preference) take over again. Category accent colors are now theme
tokens too, retinting automatically between light, dark, and high-contrast.

## Change the target folder

Pass any path as the first argument:
```
node server.js "C:\some\other\folder" 3377
```
