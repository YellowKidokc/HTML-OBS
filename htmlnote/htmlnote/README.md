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
token source (spacing grid, radii, motion ladder, typography roles, and a warm
near-neutral color ramp). The runtime theme surface lives in
`public/design-system.css`. Components consume semantic/component variables
only, never primitives — so dark mode, rebrands, and density changes happen by
re-pointing the semantic layer alone.

### Two customization surfaces

HTMLNote separates structural theming from cosmetic theming so a user theme can
never break the layout:

1. **Structural (built-in):** light / dark / high-contrast theme and
   comfortable / compact density, toggled from the header (☀ ◐ ≡) and applied
   as `data-theme` / `data-density` attributes on `:root`. Persisted per browser.
2. **Cosmetic (⚙ Customize theme):** a Style-Settings-style panel bound to an
   explicit **whitelist** of documented semantic tokens — accent hue/saturation/
   lightness, surface and text colors, reading font, body size, line height, and
   corner radius. The whitelist is defined once in `public/theming.js`
   (`THEMEABLE`) and enforced on apply and import; anything structural (panel
   sizes, spacing, layout) is never exposed. Values are written as inline custom
   properties on `:root`, persist to `localStorage`, and can be reset.

### Portable theme packages

**Export** writes an `htmlnote-theme.json` package; **Import** reads one back:

```json
{
  "name": "HTMLNote custom theme",
  "base": "dark",
  "density": "comfortable",
  "overrides": {
    "--accent-h": "265",
    "--background-primary": "#12121a"
  }
}
```

`base` selects the structural theme the overrides sit on top of. Off-whitelist
keys in an imported file are ignored.

## Change the target folder

Pass any path as the first argument:
```
node server.js "C:\some\other\folder" 3377
```
