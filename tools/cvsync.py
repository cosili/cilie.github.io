#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cvsync -- generate the website's publication list from the LaTeX CV.

Reads the \\pub{} entries out of the CV source and emits the matching
<div class="pub"> blocks for index.html, so a paper is added in one place.

Website-only metadata that the CV does not carry (research themes, journal
short names) lives in SIDECAR below; anything missing is reported rather than
guessed.
"""
from __future__ import unicode_literals
import io, re, sys, json, os

# ---------------------------------------------------------------- sidecar ---
# Website-only fields, keyed by CV publication id.
SIDECAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'cvsync-sidecar.json')

# Journal names the site abbreviates everywhere. Deliberately empty: the site
# currently spells out "Proceedings of the National Academy of Sciences" for
# the two refereed PNAS papers but abbreviates the one under review, so that
# single exception is carried as a per-entry "journal" override in the sidecar
# rather than applied as a rule. Add a pair here to normalise site-wide.
ABBREV = {}


# ------------------------------------------------------------- tex parsing ---
def brace(s, i):
    """Return (contents, index_after) for the {...} group starting at s[i]."""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == '{':
            depth += 1
        elif s[j] == '}':
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    raise ValueError('unbalanced brace at %d' % i)


def parse_pubs(tex):
    body = tex.split(r'\begin{document}')[1]
    out = []
    for m in re.finditer(r'\\pub\{', body):
        i = m.end() - 1
        pid, i = brace(body, i)
        text, i = brace(body, i)
        year, i = brace(body, i)
        out.append({'id': pid, 'raw': text, 'year': year.strip()})
    return out


# ------------------------------------------------------------ tex -> html ---
def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def inline(s):
    """Convert the LaTeX inline markup actually used in this CV."""
    s = re.sub(r'\\textit\{([^{}]*)\}', r'<em>\1</em>', s)
    s = re.sub(r'\\textbf\{([^{}]*)\}', r'<strong>\1</strong>', s)
    # The site quotes a nested title with straight quotes and leaves the
    # sentence period outside it, where LaTeX convention tucks it inside.
    s = s.replace('.``', '``').replace(".''", "''")
    s = s.replace('``', '"').replace("''", '"')
    s = s.replace('--', '\u2013').replace(r'\ ', ' ').replace('~', ' ')
    s = re.sub(r'\\&', '&', s)
    return re.sub(r'\s+', ' ', s).strip()


def authors_html(chunk):
    """Author list -> HTML, turning \\student{X ('YY)} into a dagger marker."""
    def stu(m):
        inner = m.group(1)
        nm = re.match(r"^(.*?)\s*(\('\d{2}\))\s*$", inner)
        if nm:
            return '%s<span class="ug">\u2020</span> %s' % (nm.group(1), nm.group(2))
        return '%s<span class="ug">\u2020</span>' % inner
    chunk = re.sub(r'\\student\{([^{}]*)\}', stu, chunk)
    chunk = chunk.replace(r'\cvname', 'C. Ilie')
    chunk = inline(chunk)
    return chunk.rstrip('. ').strip()


def split_entry(raw):
    """Split a \\pub body into (authors, url, title, tail)."""
    m = re.search(r'\\href\{([^}]*)\}\{', raw)
    if not m:
        raise ValueError('no \\href')
    url = m.group(1)
    inner, after = brace(raw, m.end() - 1)
    return raw[:m.start()], url, inner, raw[after:]


def title_html(inner):
    t = re.sub(r'^\\textit\{(.*)\}\s*\.?\s*$', r'\1', inner.strip(), flags=re.S)
    t = t.strip()
    if t.endswith('.'):
        t = t[:-1]
    return inline(t)


def build(entry, sidecar):
    pid = entry['id']
    authors_raw, url, title_raw, tail = split_entry(entry['raw'])

    kind = pid[0]                                  # P / N / S
    cls = {'P': 'pub', 'N': 'pub non', 'S': 'pub sub'}[kind]
    ug = '1' if r'\student' in entry['raw'] else '0'
    first = '1' if authors_raw.strip().startswith(r'\cvname') else '0'

    side = sidecar.get(pid, {})
    # None => id unknown to the sidecar, so omit the attribute entirely.
    # "" => known, deliberately themeless; the site still carries data-theme="".
    theme = side.get('theme') if pid in sidecar else None

    # --- note badge -------------------------------------------------------
    note = side.get('note')
    if note is None:
        if kind == 'S':
            note = 'under review'
        elif kind == 'N':
            note = 'non-refereed'
        elif re.search(r'[Ff]eatured on the journal cover', tail):
            note = 'journal cover'
        elif re.search(r'Cozzarelli Prize', tail):
            note = 'Cozzarelli Prize'

    # --- journal line -----------------------------------------------------
    journal = side.get('journal')
    if journal is None:
        j = tail
        # "Featured on the journal cover." becomes a badge only.
        j = re.sub(r'\s*Featured on the journal cover\.', '', j)
        # The Cozzarelli Prize gets a badge AND stays as a trailing clause.
        j = re.sub(r'\.?\s*Recipient of the (\d{4} [^.]*Cozzarelli Prize)\.',
                   r' · \1', j)
        # "arXiv:X. Non-refereed letter companion to P11." -> bullet clause,
        # absorbing the sentence period that preceded it.
        j = re.sub(r'\.?\s*Non-refereed letter companion to (\w+)\.',
                   r' · letter companion to @@CV:\1@@', j)
        # "(Revise and Resubmit, revision submitted September 2026). arXiv:X"
        #   -> "— revise and resubmit, revision submitted September 2026 · arXiv:X"
        j = re.sub(r'\s*\(Revise and Resubmit,\s*([^)]*)\)\.\s*',
                   lambda m: ' — revise and resubmit, %s · ' % m.group(1).strip(), j)
        j = inline(j).strip().rstrip('.').strip()
        for long, short in ABBREV.items():
            j = j.replace(long, short)
        journal = j

    notehtml = '<span class="note">%s</span>' % esc(note) if note else ''
    themeattr = '' if theme is None else ' data-theme="%s"' % esc(theme)

    return (
        '        <div class="{cls}"{theme} data-ug="{ug}" data-first="{first}">\n'
        '          <div>\n'
        '            <div class="t"><a href="{url}" target="_blank" rel="noopener">{title}</a>{note}</div>\n'
        '            <div class="a">{authors}</div>\n'
        '            <div class="j">{journal}</div>\n'
        '          </div>\n'
        '          <span class="yr">{year}</span>\n'
        '        </div>'
    ).format(cls=cls, theme=themeattr, ug=ug, first=first, url=url,
             title=title_html(title_raw), note=notehtml,
             authors=authors_html(authors_raw), journal=journal,
             year=entry['year'])



def resolve_companions(blocks, pubs):
    """A CV entry may cite another by its id ("companion to P11"). The CV
    prints those ids in the margin, but they appear nowhere on the website,
    so swap the id for the cited paper's own citation, linked."""
    cite = {}
    for pub, block in zip(pubs, blocks):
        j = re.search(r'<div class="j">(.*?)</div>', block, re.S)
        u = re.search(r'<a href="([^"]+)"', block)
        if j and u:
            cite[pub['id']] = (u.group(1), j.group(1).strip())
    out = []
    for block in blocks:
        def sub(m):
            pid = m.group(1)
            if pid not in cite:
                sys.stderr.write('companion reference %s not found\n' % pid)
                return pid
            url, text = cite[pid]
            return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (url, text)
        out.append(re.sub(r'@@CV:(\w+)@@', sub, block))
    return out


# -------------------------------------------------------------------- main ---
def main():
    if len(sys.argv) < 2:
        sys.stderr.write('usage: cvsync.py CV.tex [--check index.html]\n')
        return 2
    tex = io.open(sys.argv[1], encoding='utf-8').read()
    sidecar = {}
    if os.path.exists(SIDECAR_PATH):
        sidecar = json.load(io.open(SIDECAR_PATH, encoding='utf-8'))

    pubs = parse_pubs(tex)
    order = {'S': 0, 'P': 1, 'N': 2}
    pubs.sort(key=lambda p: (order[p['id'][0]], -int(re.sub(r'\D', '', p['id']))))

    blocks = [build(p, sidecar) for p in pubs]
    blocks = resolve_companions(blocks, pubs)
    # A sidecar entry with an empty theme is a deliberate "no theme chip"
    # (P7 and P8 sit outside the four research themes). Only an id the
    # sidecar has never seen needs a decision.
    unknown = [p['id'] for p in pubs if p['id'] not in sidecar]
    if unknown:
        sys.stderr.write(
            'NEW publication(s) with no sidecar entry: %s\n'
            'Add a theme (dark-stars / seeds / detectors / early, space-separated\n'
            'for more than one, or "" for none) to %s\n'
            % (', '.join(unknown), os.path.basename(SIDECAR_PATH)))

    if '--apply' in sys.argv:
        path = sys.argv[sys.argv.index('--apply') + 1]
        html = io.open(path, encoding='utf-8').read()
        begin, end = '<!-- PUBS:BEGIN', '<!-- PUBS:END -->'
        b = html.find(begin)
        e = html.find(end)
        if b < 0 or e < 0:
            sys.stderr.write('markers %s / %s not found in %s\n'
                             % (begin, end, path))
            return 1
        b = html.index('-->', b) + 3
        new = html[:b] + '\n\n' + '\n\n'.join(blocks) + '\n\n      ' + html[e:]
        if new == html:
            print('%s already up to date (%d publications)' % (path, len(blocks)))
            return 0
        io.open(path, 'w', encoding='utf-8').write(new)
        print('wrote %d publications into %s' % (len(blocks), path))
        return 0

    if '--check' in sys.argv:
        html = io.open(sys.argv[sys.argv.index('--check') + 1],
                       encoding='utf-8').read()
        have = re.findall(r'(        <div class="pub[^"]*"[^>]*>.*?\n        </div>)',
                          html, re.S)
        same = sum(1 for a, b in zip(blocks, have) if a == b)
        print('generated %d, existing %d, byte-identical %d'
              % (len(blocks), len(have), same))
        for i, (a, b) in enumerate(zip(blocks, have)):
            if a != b:
                print('\n--- #%d %s ---\nCV-> %s\nWEB- %s'
                      % (i, pubs[i]['id'],
                         a.replace('\n', '\n     '), b.replace('\n', '\n     ')))
        return 0

    sys.stdout.write('\n\n'.join(blocks) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
