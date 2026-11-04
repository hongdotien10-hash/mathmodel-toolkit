# Five pitfalls that produce a figure that looks fine and fails review

Each of these was reproduced and confirmed against matplotlib 3.11. All five are
silent: the code runs, the notebook renders, and the defect only surfaces at
export or at the editor.

## 1. matplotlib does not fall back per glyph — CJK becomes tofu

`font.sans-serif` is a *list*, which invites the assumption that matplotlib tries
each font in turn for any glyph the previous one lacks. It does not.

```python
# WRONG: Chinese renders as empty boxes
mpl.rcParams["font.sans-serif"] = ["Times New Roman", "SimSun"]

# RIGHT: CJK font first
mpl.rcParams["font.sans-serif"] = ["SimSun", "Times New Roman"]
```

Times New Roman has no CJK coverage, so every Chinese character becomes a box.
Putting 宋体 first works for both scripts because SimSun's Latin glyphs are
Times-derived.

Detect it before export: render the strings and catch matplotlib's
`Glyph NNN missing from font` warning (see `journal_fig.py check-text`). Looking
at the figure in a notebook is not enough — the warning is easy to miss in a
cell that emits a long traceback-free output.

## 2. A preset is a no-op when the font is absent

`Times New Roman` and `SimSun` do not exist on stock Linux or macOS. matplotlib
resolves the first available font and silently uses DejaVu instead. The figure
looks "styled" — different from matplotlib's default — but matches no journal
spec at all.

Detect it: `journal_fig.py doctor`. Fix it by installing the font
(`ttf-mscorefonts-installer` on Debian/Ubuntu, or drop the .ttf into
`~/.local/share/fonts` and rebuild matplotlib's font cache) or by changing the
chain.

## 3. `/Image` in a PDF does not mean the figure contains a raster

matplotlib writes `/ProcSet [/PDF /Text /ImageB /ImageC /ImageI]` into every PDF
it produces. A naive substring search for `/Image` therefore reports a raster
object in a pure line plot — a 100% false positive rate.

Match the object subtype instead: `/Subtype /Image`.

## 4. rcParams rejects keys it does not know

Passing a dictionary that contains bookkeeping keys (anything prefixed with `_`)
into `rcParams.update()` raises `KeyError: "'_x' is not a valid value for
rcParam"`. Strip private keys before updating, and set `figure.figsize`
separately.

## 5. `ax.clear()` does not clear the twin axis

`ax.twinx()` creates a second `Axes` that is not a child of the first. Calling
`ax.clear()` on the primary axis leaves the twin's artists in place, so a figure
that is "cleared and redrawn" ends up with a stray curve and a wrong y-range.

Also note: **rcParams only affect artists created after the change.** To restyle
an existing figure, redraw the artists — do not clear and hope the style
reapplies.

## Bonus: negative sign in CJK figures

With a CJK font active, the Unicode minus `U+2212` is often missing and renders
as a box. Setting `axes.unicode_minus = False` makes matplotlib emit an ASCII
hyphen instead. This fixes the box but makes the minus sign shorter than a
typeset one — acceptable for most journals, worth knowing if a copy-editor
complains about minus length.
