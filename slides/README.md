# Slides

The talk is written in Markdown (`markdown/*.md`) and rendered with [reveal.js](https://revealjs.com) 6.0.2 (`index.html`).

## Start the slideshow

From this `slides/` folder, install the dev dependencies once, then start the dev server:

```bash
npm install
npm run dev
```

This opens <http://localhost:8080> and reloads the browser whenever a Markdown or HTML file in `slides/` changes.

Without Node, any static server works, but it will not reload on change. Run it from this `slides/` folder and open the root URL:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000/> in a browser (not `/slides`: the folder is served at the root).

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| `→` / `←` | Next / previous slide |
| `↓` / `↑` | Next / previous vertical slide (`--` in the Markdown) |
| `S` | Speaker view (notes are written after a `Note:` line) |
| `F` | Fullscreen |
| `Esc` / `O` | Slide overview |

## Editing

- One Markdown file per topic in `markdown/`. Slides are separated by a line containing `---`, vertical slides by a line containing `--`.
- The list of files played, and their transitions, is in the `<section>` elements of `index.html`.
- Images live in `img/`, referenced relatively (`./img/...`).
- reveal.js assets are in `dist/`. Do not edit them by hand; they are the 6.0.2 release.
