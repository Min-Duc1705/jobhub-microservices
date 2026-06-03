import pdfplumber

pdf = pdfplumber.open(r"t:\TryHard_IT_Project\Final\Backend\CV\template-6.pdf")

with open("inspect_t6_coords.txt", "w", encoding="utf-8") as out:
    out.write(f"Total Pages: {len(pdf.pages)}\n")

    for page_idx, p in enumerate(pdf.pages):
        out.write(f"\n--- PAGE {page_idx + 1} ---\n")
        words = p.extract_words()
        # Group words that are on approximately the same line (same top within 2 pt)
        lines = {}
        for w in words:
            top_rounded = round(w['top'] / 3.0) * 3.0  # group within ~3 pt
            lines.setdefault(top_rounded, []).append(w)
            
        for top in sorted(lines.keys()):
            line_words = lines[top]
            line_words.sort(key=lambda w: w['x0'])
            line_str = " | ".join(f"[{w['x0']:.1f}] {w['text']}" for w in line_words)
            out.write(f"y={top:.1f}: {line_str}\n")
print("Done")
