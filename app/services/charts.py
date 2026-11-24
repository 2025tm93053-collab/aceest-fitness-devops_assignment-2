"""Server-rendered inline SVG line chart (replaces matplotlib plt.show())."""
from markupsafe import Markup, escape


def line_chart(labels, values, y_min=0, y_max=100, color="#d4af37", unit=""):
    if not values:
        return Markup("")
    w, h, pad = 560, 220, 36
    n = len(values)
    span = (y_max - y_min) or 1

    def xy(i, v):
        x = pad + (w - 2 * pad) * (i / (n - 1) if n > 1 else 0.5)
        y = h - pad - (h - 2 * pad) * ((v - y_min) / span)
        return round(x, 1), round(y, 1)

    pts = [xy(i, v) for i, v in enumerate(values)]
    poly = " ".join(f"{x},{y}" for x, y in pts)
    dots = "".join(
        f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"><title>{escape(labels[i])}: '
        f'{values[i]}{unit}</title></circle>' for i, (x, y) in enumerate(pts)
    )
    axis = (
        f'<line x1="{pad}" y1="{h - pad}" x2="{w - pad}" y2="{h - pad}" stroke="#555"/>'
        f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{h - pad}" stroke="#555"/>'
        f'<text x="4" y="{pad + 4}" fill="#aaa" font-size="11">{y_max:g}</text>'
        f'<text x="4" y="{h - pad}" fill="#aaa" font-size="11">{y_min:g}</text>'
    )
    return Markup(
        f'<svg viewBox="0 0 {w} {h}" class="chart" role="img">{axis}'
        f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="2"/>{dots}</svg>'
    )
