# cvsync

Generates the site's publication list from the LaTeX CV, so a paper is
added in one place.

## Use

From the folder that holds the CV source and this repo:

```
python3 cilie.github.io/tools/cvsync.py Cosmin_Ilie_Academic_CV.tex --check cilie.github.io/index.html
python3 cilie.github.io/tools/cvsync.py Cosmin_Ilie_Academic_CV.tex --apply cilie.github.io/index.html
```

`--check` diffs without writing and prints how many blocks it reproduces
byte-for-byte; it should say 28 of 28 (or whatever the current count is).
`--apply` rewrites the list in place. Running it twice is a no-op. With
neither flag it prints the blocks to stdout.

Only the region between `<!-- PUBS:BEGIN -->` and `<!-- PUBS:END -->` in
`index.html` is touched, so a bad run cannot damage the rest of the page.
Edits made by hand inside that region are overwritten — change the CV
instead.

## Adding a paper

1. Add a `\pub{P<n>}{...}{<year>}` entry to the CV.
2. Run `--apply`. It will refuse to guess a research theme and will name
   the new id.
3. Add that id to `cvsync-sidecar.json` with one of `dark-stars`,
   `seeds`, `detectors`, `early` (space-separated for more than one, or
   `""` for none — P7 and P8 sit outside all four).
4. Run `--apply` again, then `--check` to confirm.

## What the sidecar holds

Only what the CV does not carry: the research theme per paper, and rarely
a per-entry override of the rendered journal line. Everything else —
title, authors, undergraduate daggers, first-authorship, journal, volume,
page, year, prize and cover badges — is derived from the CV.

## Conventions it encodes

- `\student{}` in the CV becomes `data-ug="1"` and a dagger.
- `\cvname` opening the author list becomes `data-first="1"`.
- `P` ids are refereed, `N` non-refereed, `S` under review.
- "Featured on the journal cover." becomes a badge only; the Cozzarelli
  Prize becomes a badge *and* stays in the journal line.
- A CV cross-reference such as "companion to P11" is resolved to the
  cited paper's own citation, linked, because the ids the CV prints in
  its margin mean nothing on the website.
