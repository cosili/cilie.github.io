# cosminilie.com — personal academic website

Static site. No build step, no dependencies. Everything is in `index.html`
plus the `assets/` folder and the CV PDF.

```
index.html               the whole site (7 tabs, all inline CSS/JS)
Cosmin_Ilie_CV.pdf       compiled from the LaTeX CV source
assets/                  photos (hero, blackboards, group, poster)
assets/people/           student portraits, 420x420
.nojekyll                tells GitHub Pages to serve files as-is
```

## Putting it online (GitHub Pages)

1. Create a GitHub repo named `<your-username>.github.io` (or any name — then
   the site lives at `<username>.github.io/<repo>`).
2. Upload the contents of this folder to the repo root (drag and drop works in
   the GitHub web interface).
3. Repo → **Settings → Pages** → Source: *Deploy from a branch*, branch `main`,
   folder `/ (root)`. Save. The site is live in about a minute.

### Custom domain

1. Buy the domain (Cloudflare Registrar or Porkbun, ~$11/yr, same at renewal).
2. In **Settings → Pages → Custom domain**, enter `cosminilie.com`. GitHub
   writes a `CNAME` file into the repo.
3. At the registrar, add DNS records:
   - `A` records for `@` → `185.199.108.153`, `185.199.109.153`,
     `185.199.110.153`, `185.199.111.153`
   - `CNAME` for `www` → `<your-username>.github.io`
4. Back in Settings → Pages, tick **Enforce HTTPS** once the certificate is
   issued (usually within an hour).

Verify the current GitHub Pages IP addresses in GitHub's docs before you paste
them — they change rarely, but they do change.

## Editing

Everything is plain HTML with comments marking each tab:

```html
<!-- ===================== MENTORING ===================== -->
```

- **New paper** — copy an existing `<div class="pub">` block at the top of the
  publications list, change the id/title/authors/journal/year. Set
  `data-ug="1"` if an undergraduate is a coauthor and `data-first="1"` if you
  are first or sole author, so the filter chips stay correct. Those same two
  attributes feed the stat strip, so the counts follow on their own — see
  "Counts look after themselves" below. Use `class="pub non"` for a
  non-refereed item and `class="pub sub"` for one under review; a plain
  `class="pub"` counts as refereed.
- **New student** — copy a `<div class="mentee">` block, drop a square portrait
  (about 420×420) into `assets/people/`. The mentee count updates itself.
- **New press item** — copy a `<li>` in the relevant year group on the Press
  tab.
- **New CV** — recompile the LaTeX and overwrite `Cosmin_Ilie_CV.pdf`.

## Counts look after themselves

The tallies on the Mentoring stat strip and in the Publications blurb are
counted from the lists they describe, so adding a paper or a mentee updates
them with no second edit. Each one carries a `data-count` key:

| Key              | Counts                                    |
| ---------------- | ----------------------------------------- |
| `pubs-refereed`  | `#publist .pub:not(.non):not(.sub)`       |
| `pubs-ug`        | `#publist .pub[data-ug="1"]`              |
| `pubs-first`     | `#publist .pub[data-first="1"]`           |
| `pubs-non`       | `#publist .pub.non`                       |
| `pubs-sub`       | `#publist .pub.sub`                       |
| `mentees`        | `#m-past .mentee`                         |

Add `data-count-words` to render the number as a word ("two") rather than a
digit, for numbers that sit inside prose.

The number written in the HTML is the no-JS fallback, not a placeholder — it
renders if the script never runs, and the script overwrites it otherwise. If
the two disagree the console says so on load; the page is already showing the
right value at that point, the warning just means the fallback text is worth
refreshing.

Two stats are deliberately left unbound because they have no list to count:
"1 APS Apker Award national finalist" and "1 Goldwater Scholar". So is the
phrase "three seemingly distinct puzzles" on the Home tab, which counts
puzzles rather than the single paper linked beside it.

## Notes

- Fonts load from Google Fonts; everything else is local. The site works
  offline apart from the font request.
- The starfield in the hero is a small canvas script and switches itself off
  for visitors who have "reduce motion" enabled.
- Tabs use `#hash` URLs, so `cosminilie.com/#mentoring` links straight to the
  mentoring tab and the back button behaves normally.
