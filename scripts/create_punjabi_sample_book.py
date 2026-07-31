#!/usr/bin/env python3
"""Regenerate the sample Punjabi booklet PDF (requires reportlab + Noto Sans Gurmukhi)."""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "fonts" / "NotoSansGurmukhi-Regular.ttf"
OUT = ROOT / "punjabi_books" / "sikh_dharam_jaan_pehchaan_punjabi.pdf"
TXT = ROOT / "punjabi_books" / "sikh_dharam_jaan_pehchaan_punjabi.txt"

CHAPTERS = [
    (
        "ਅਧਿਆਇ 1: ਸਿੱਖ ਧਰਮ ਦੀ ਸਥਾਪਨਾ",
        [
            "ਸਿੱਖ ਧਰਮ ਦੀ ਸਥਾਪਨਾ ਗੁਰੂ ਨਾਨਕ ਦੇਵ ਜੀ ਨੇ ਪੰਦਰਵੀਂ ਸਦੀ ਵਿੱਚ ਕੀਤੀ। ਗੁਰੂ ਨਾਨਕ ਦਾ ਜਨਮ 1469 ਈਸਵੀ ਵਿੱਚ ਤਲਵੰਡੀ ਰਾਏ ਭੋਏ (ਅੱਜ ਦਾ ਨਨਕਾਣਾ ਸਾਹਿਬ) ਵਿਖੇ ਹੋਇਆ।",
            "ਉਹਨਾਂ ਨੇ ਇੱਕ ਰੱਬ (ਇੱਕ ਓਅੰਕਾਰ), ਸਭ ਲਈ ਪਿਆਰ, ਸਮਾਨਤਾ ਅਤੇ ਸੱਚ ਉੱਤੇ ਅਧਾਰਿਤ ਧਰਮ ਦਾ ਉਪਦੇਸ਼ ਦਿੱਤਾ। ਗੁਰੂ ਨਾਨਕ ਜੀ ਨੇ ਲੰਬੀਆਂ ਉਦਾਸੀਆਂ (ਯਾਤਰਾਵਾਂ) ਕੀਤੀਆਂ ਅਤੇ ਲੋਕਾਂ ਨੂੰ ਨਾਮ ਜਪਣ, ਕਿਰਤ ਕਰਨ ਅਤੇ ਵੰਡ ਛਕਣ ਦਾ ਸੰਦੇਸ਼ ਦਿੱਤਾ।",
            "ਸਿੱਖ ਸ਼ਬਦ ਦਾ ਅਰਥ ਹੈ ਸਿਖਣ ਵਾਲਾ ਜਾਂ ਚੇਲਾ। ਸਿੱਖ ਧਰਮ ਵਿੱਚ ਦਸ ਗੁਰੂ ਹੋਏ, ਜਿਨ੍ਹਾਂ ਵਿੱਚੋਂ ਪਹਿਲੇ ਗੁਰੂ ਨਾਨਕ ਦੇਵ ਜੀ ਅਤੇ ਦਸਵੇਂ ਗੁਰੂ ਗੋਬਿੰਦ ਸਿੰਘ ਜੀ ਸਨ।",
        ],
    ),
    (
        "ਅਧਿਆਇ 2: ਗੁਰੂ ਗ੍ਰੰਥ ਸਾਹਿਬ",
        [
            "ਗੁਰੂ ਗ੍ਰੰਥ ਸਾਹਿਬ ਸਿੱਖਾਂ ਦਾ ਪਵਿੱਤਰ ਗ੍ਰੰਥ ਹੈ। ਇਸ ਨੂੰ ਗੁਰੂ ਅਰਜਨ ਦੇਵ ਜੀ ਨੇ ਸੰਕਲਿਤ ਕੀਤਾ ਅਤੇ ਬਾਅਦ ਵਿੱਚ ਗੁਰੂ ਗੋਬਿੰਦ ਸਿੰਘ ਜੀ ਨੇ ਗੁਰੂ ਤੇਗ ਬਹਾਦਰ ਜੀ ਦੀ ਬਾਣੀ ਸ਼ਾਮਲ ਕਰਕੇ ਇਸ ਨੂੰ ਅੰਤਿਮ ਰੂਪ ਦਿੱਤਾ।",
            "1708 ਈਸਵੀ ਵਿੱਚ ਗੁਰੂ ਗੋਬਿੰਦ ਸਿੰਘ ਜੀ ਨੇ ਗੁਰੂ ਗ੍ਰੰਥ ਸਾਹਿਬ ਨੂੰ ਸਦੀਵੀ ਗੁਰੂ ਘੋਸ਼ਿਤ ਕੀਤਾ। ਇਸ ਲਈ ਸਿੱਖ ਗੁਰੂ ਗ੍ਰੰਥ ਸਾਹਿਬ ਨੂੰ ਜੀਵਤ ਗੁਰੂ ਮੰਨਦੇ ਹਨ।",
            "ਗੁਰੂ ਗ੍ਰੰਥ ਸਾਹਿਬ ਵਿੱਚ ਗੁਰੂਆਂ ਤੋਂ ਇਲਾਵਾ ਭਗਤਾਂ ਅਤੇ ਭੱਟਾਂ ਦੀ ਬਾਣੀ ਵੀ ਸ਼ਾਮਲ ਹੈ। ਇਹ ਗੁਰਮੁਖੀ ਲਿਪੀ ਵਿੱਚ ਲਿਖਿਆ ਗਿਆ ਹੈ।",
        ],
    ),
    (
        "ਅਧਿਆਇ 3: ਪੰਜ ਕਕਾਰ ਅਤੇ ਖ਼ਾਲਸਾ",
        [
            "1699 ਈਸਵੀ ਵਿੱਚ ਵਿਸਾਖੀ ਦੇ ਦਿਨ ਗੁਰੂ ਗੋਬਿੰਦ ਸਿੰਘ ਜੀ ਨੇ ਅਨੰਦਪੁਰ ਸਾਹਿਬ ਵਿਖੇ ਖ਼ਾਲਸਾ ਪੰਥ ਦੀ ਸਥਾਪਨਾ ਕੀਤੀ। ਉਹਨਾਂ ਨੇ ਪੰਜ ਪਿਆਰਿਆਂ ਨੂੰ ਅੰਮ੍ਰਿਤ ਛਕਾਇਆ ਅਤੇ ਉਹਨਾਂ ਤੋਂ ਖ਼ੁਦ ਵੀ ਅੰਮ੍ਰਿਤ ਲਿਆ।",
            "ਖ਼ਾਲਸਾ ਸਿੱਖਾਂ ਨੂੰ ਪੰਜ ਕਕਾਰ ਰੱਖਣੇ ਹੁੰਦੇ ਹਨ: ਕੇਸ (ਵਾਲ), ਕੰਘਾ (ਕੰਘੀ), ਕੜਾ (ਲੋਹੇ ਦਾ ਕੜਾ), ਕਛਹਿਰਾ (ਚੋਲਾ), ਅਤੇ ਕਿਰਪਾਨ (ਤਲਵਾਰ)। ਇਹ ਪੰਜ ਕਕਾਰ ਖ਼ਾਲਸਾ ਪਛਾਣ ਅਤੇ ਅਨੁਸ਼ਾਸਨ ਦਾ ਚਿੰਨ੍ਹ ਹਨ।",
            "ਖ਼ਾਲਸਾ ਦਾ ਮਤਲਬ ਹੈ ਖ਼ਾਲਿਸ ਜਾਂ ਸ਼ੁੱਧ। ਗੁਰੂ ਗੋਬਿੰਦ ਸਿੰਘ ਜੀ ਨੇ ਸਿੱਖਾਂ ਨੂੰ ਸੰਤ-ਸਿਪਾਹੀ ਬਣਨ ਦਾ ਉਪਦੇਸ਼ ਦਿੱਤਾ — ਅਧਿਆਤਮਕ ਅਤੇ ਨਿਆਂ ਲਈ ਖੜ੍ਹੇ ਰਹਿਣ ਵਾਲੇ।",
        ],
    ),
    (
        "ਅਧਿਆਇ 4: ਮੁੱਖ ਸਿਧਾਂਤ ਅਤੇ ਰੀਤੀਆਂ",
        [
            "ਸਿੱਖ ਧਰਮ ਦੇ ਤਿੰਨ ਮੁੱਖ ਥੰਮ੍ਹ ਹਨ: ਨਾਮ ਜਪੋ (ਰੱਬ ਦਾ ਨਾਮ ਸਿਮਰੋ), ਕਿਰਤ ਕਰੋ (ਇਮਾਨਦਾਰੀ ਨਾਲ ਮਿਹਨਤ ਕਰੋ), ਅਤੇ ਵੰਡ ਛਕੋ (ਕਮਾਈ ਵਿੱਚੋਂ ਹਿੱਸਾ ਵੰਡੋ)।",
            "ਗੁਰਦੁਆਰਾ ਸਿੱਖਾਂ ਦਾ ਪੂਜਾ ਅਸਥਾਨ ਹੈ। ਹਰ ਗੁਰਦੁਆਰੇ ਵਿੱਚ ਲੰਗਰ ਚਲਦਾ ਹੈ, ਜਿੱਥੇ ਬਿਨਾਂ ਭੇਦਭਾਵ ਦੇ ਸਭ ਨੂੰ ਖਾਣਾ ਮਿਲਦਾ ਹੈ। ਇਹ ਸਮਾਨਤਾ ਅਤੇ ਸੇਵਾ ਦਾ ਪ੍ਰਤੀਕ ਹੈ।",
            "ਮੁੱਖ ਸਿੱਖ ਤਿਉਹਾਰਾਂ ਵਿੱਚ ਵਿਸਾਖੀ, ਗੁਰਪੁਰਬ (ਗੁਰੂਆਂ ਦੇ ਜਨਮ ਜਾਂ ਸ਼ਹਾਦਤ ਦਿਵਸ), ਅਤੇ ਬੰਦੀ ਛੋੜ ਦਿਵਸ ਸ਼ਾਮਲ ਹਨ। ਹਰਿਮੰਦਰ ਸਾਹਿਬ (ਸੁਨਹਿਰੀ ਮੰਦਰ) ਅੰਮ੍ਰਿਤਸਰ ਵਿਖੇ ਸਿੱਖਾਂ ਦਾ ਸਭ ਤੋਂ ਪਵਿੱਤਰ ਅਸਥਾਨ ਹੈ।",
        ],
    ),
    (
        "ਅਧਿਆਇ 5: ਗੁਰਮੁਖੀ ਲਿਪੀ ਅਤੇ ਪੰਜਾਬੀ ਭਾਸ਼ਾ",
        [
            "ਗੁਰਮੁਖੀ ਲਿਪੀ ਨੂੰ ਗੁਰੂ ਅੰਗਦ ਦੇਵ ਜੀ ਨੇ ਮਾਨਕ ਰੂਪ ਦਿੱਤਾ। ਇਸ ਲਿਪੀ ਵਿੱਚ ਗੁਰੂ ਗ੍ਰੰਥ ਸਾਹਿਬ ਅਤੇ ਬਹੁਤੀ ਸਿੱਖ ਸਾਹਿਤ ਲਿਖੀ ਗਈ ਹੈ।",
            "ਪੰਜਾਬੀ ਭਾਸ਼ਾ ਪੰਜਾਬ ਖੇਤਰ ਦੀ ਮੁੱਖ ਭਾਸ਼ਾ ਹੈ। ਭਾਰਤ ਵਿੱਚ ਇਹ ਆਮ ਤੌਰ ਤੇ ਗੁਰਮੁਖੀ ਵਿੱਚ ਅਤੇ ਪਾਕਿਸਤਾਨ ਵਿੱਚ ਸ਼ਾਹਮੁਖੀ (ਫ਼ਾਰਸੀ-ਅਰਬੀ) ਲਿਪੀ ਵਿੱਚ ਲਿਖੀ ਜਾਂਦੀ ਹੈ।",
            "ਇਹ ਪੁਸਤਕ ਪੰਜਾਬੀ (ਗੁਰਮੁਖੀ) ਵਿੱਚ ਲਿਖੀ ਗਈ ਹੈ ਤਾਂ ਜੋ ਪਾਠਕ ਸਿੱਖ ਧਰਮ ਦੀਆਂ ਮੁੱਢਲੀਆਂ ਗੱਲਾਂ ਆਪਣੀ ਭਾਸ਼ਾ ਵਿੱਚ ਸਮਝ ਸਕਣ।",
        ],
    ),
]


def draw_wrapped(c, text, x, y, max_w, font="NotoGurmukhi", size=12, leading=18, y_start=None):
    c.setFont(font, size)
    words = text.split(" ")
    line = ""
    width, height = A4
    if y_start is None:
        y_start = height - 2.5 * cm
    for w in words:
        trial = (line + " " + w).strip()
        if c.stringWidth(trial, font, size) <= max_w:
            line = trial
        else:
            c.drawString(x, y, line)
            y -= leading
            line = w
            if y < 2.5 * cm:
                c.showPage()
                y = y_start
                c.setFont(font, size)
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def main():
    if not FONT.exists():
        raise SystemExit(
            f"Missing font at {FONT}. Download Noto Sans Gurmukhi Regular into fonts/ first."
        )
    pdfmetrics.registerFont(TTFont("NotoGurmukhi", str(FONT)))
    OUT.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(OUT), pagesize=A4)
    width, height = A4
    margin = 2 * cm
    max_width = width - 2 * margin
    y_start = height - 2.5 * cm

    c.setFont("NotoGurmukhi", 22)
    c.drawCentredString(width / 2, height - 8 * cm, "ਸਿੱਖ ਧਰਮ: ਜਾਣ-ਪਛਾਣ")
    c.setFont("NotoGurmukhi", 14)
    c.drawCentredString(width / 2, height - 9.5 * cm, "ਪੰਜਾਬੀ (ਗੁਰਮੁਖੀ) ਵਿੱਚ ਇੱਕ ਛੋਟੀ ਪੁਸਤਕ")
    c.showPage()

    for title, paras in CHAPTERS:
        y = y_start
        c.setFont("NotoGurmukhi", 16)
        c.drawString(margin, y, title)
        y -= 28
        for para in paras:
            y = draw_wrapped(c, para, margin, y, max_width, y_start=y_start)
            y -= 10
            if y < 3 * cm:
                c.showPage()
                y = y_start
        c.showPage()
    c.save()

    with TXT.open("w", encoding="utf-8") as f:
        f.write("ਸਿੱਖ ਧਰਮ: ਜਾਣ-ਪਛਾਣ\n\n")
        for title, paras in CHAPTERS:
            f.write(title + "\n\n")
            for p in paras:
                f.write(p + "\n\n")
    print(f"Wrote {OUT}")
    print(f"Wrote {TXT}")


if __name__ == "__main__":
    main()
