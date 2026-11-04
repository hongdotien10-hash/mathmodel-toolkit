# Journal figure specifications

Compiled from publicly published author guidelines. **Column widths and minimum
font sizes are the two numbers that cause rejections**, and both differ slightly
between a journal's "author guidelines" page and its actual LaTeX/Word template.
When the target journal is known, check its current guide before finalizing.

## IEEE (journals and conferences, two-column)

| Item | Value |
|---|---|
| Single column width | 3.5 in / 88.9 mm |
| Double column width | 7.16 in / 181.9 mm |
| Body font | Times New Roman (serif) |
| Minimum text size inside figure | 8 pt |
| Minimum line width | 0.5 pt |
| Raster resolution | 300 dpi minimum, 600 dpi for line art |
| Preferred format | PDF / EPS (vector) |

Notes: IEEE templates often embed figures at exactly the column width, so a
figure authored at 3.5 in will not be scaled and its 8 pt text stays 8 pt. A
figure authored at 6 in and scaled down to 3.5 in turns 8 pt text into 4.7 pt —
this is the single most common cause of "text too small" rejections.

## Elsevier (single column 90 mm)

| Item | Value |
|---|---|
| Single column width | 90 mm / 3.54 in |
| 1.5 column width | 140 mm / 5.51 in |
| Double column width | 190 mm / 7.48 in |
| Font | sans-serif preferred (Arial / Helvetica) |
| Minimum text size inside figure | 7 pt |
| Raster resolution | 300 dpi (halftone), 500 dpi (combination), 1000 dpi (line art) |
| Preferred format | EPS / PDF |

## Chinese journals (学报 / 中文核心)

| Item | Value |
|---|---|
| Single column width | 7.5 cm / 2.95 in |
| Double column width | 15 cm / 5.91 in |
| Chinese font | 宋体 (SimSun) |
| Latin font | Times New Roman |
| Minimum text size | 7.5 pt (六号) for figure text, 9 pt (小五号) for captions |
| Raster resolution | 300 dpi minimum, 600 dpi for line art |

Notes: Chinese journals generally require 中文宋体 + 西文 Times New Roman in the
same figure. matplotlib cannot mix fonts per glyph, so this is approximated by
using 宋体 for everything — SimSun's Latin glyphs are Times-derived, so numerals
and units still look correct. If the journal is strict about Latin glyphs, set
the Latin labels with `fontfamily="Times New Roman"` explicitly per text object.

## Other commonly cited widths

Verify against the journal's current guide before relying on these.

| Publisher / journal | Single column | Double column |
|---|---|---|
| Nature | 89 mm | 183 mm |
| Science | 55 mm / 120 mm | 183 mm |
| Springer (most journals) | 84 mm | 174 mm |
| ACS | 82.6 mm | 177.8 mm |
| PLOS ONE | 83 mm | 173 mm |

## Resolution decision rule

- Line art, plots, diagrams → **vector (PDF/EPS)**. Resolution is irrelevant.
- Photos, heatmaps, microscopy → raster at 300–600 dpi, sized at final width.
- Never scale a raster figure up. Scaling down is acceptable if the source dpi
  is high enough that `dpi_after_scaling >= 300`.
