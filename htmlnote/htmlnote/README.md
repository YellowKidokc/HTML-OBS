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

## Change the target folder

Pass any path as the first argument:
```
node server.js "C:\some\other\folder" 3377
```
