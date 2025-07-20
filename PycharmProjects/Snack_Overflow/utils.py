import pdfplumber
import re
from collections import defaultdict, Counter


def clean_text(text):
    return re.sub(r'\s+', ' ', text.replace('\u00a0', ' ')).strip()


def is_heading_candidate(line):
    text = line['text'].strip()

    # Reject lines that are too long or small
    if len(text) < 3 or len(text) > 120:
        return False

    # Block section-like entries like form fields: "1. Name of employee:"
    if re.match(r'^\d{1,2}\.', text) and text.endswith(":"):
        return False

    # Mostly numeric → not heading
    if len(re.findall(r'[a-zA-Z]', text)) < 3:
        return False

    # Table rows or form options with colons/bullets
    if ':' in text and len(text.split()) <= 3:
        return False

    # Heading-like patterns
    if re.match(r'^\d(\.\d){0,2}', text): return True
    if text.isupper(): return True
    if text.istitle(): return True
    return False


def get_heading_level(text, size, thresholds):
    if re.match(r'^\d+\.\d+\.\d+', text):  # e.g. 2.3.1
        return "H3"
    elif re.match(r'^\d+\.\d+', text):  # e.g. 3.2
        return "H2"
    elif re.match(r'^\d+[^.a-zA-Z]', text):  # e.g. 4 Introduction
        return "H1"

    # Font Size fallback
    if size == thresholds[0]:
        return "H1"
    elif size == thresholds[1]:
        return "H2"
    elif size == thresholds[2]:
        return "H3"
    return None


def merge_words(words, y_tol=3):
    lines = defaultdict(list)
    for w in words:
        y = round(w["top"] / y_tol) * y_tol
        lines[y].append(w)

    merged_lines = []
    for line in lines.values():
        line = sorted(line, key=lambda x: x["x0"])
        text_fragments = []
        last_x = None
        for w in line:
            if last_x and w["x0"] - last_x > 2:
                text_fragments.append(" ")
            text_fragments.append(w["text"])
            last_x = w["x1"]
        text = clean_text("".join(text_fragments))
        avg_size = round(sum(w["size"] for w in line) / len(line), 1)
        merged_lines.append({
            "text": text,
            "size": avg_size,
            "fontname": line[0]["fontname"]
        })
    return merged_lines


def extract_outline(pdf_path):
    outline = []
    with pdfplumber.open(pdf_path) as pdf:
        font_counter = Counter()
        lines_by_page = defaultdict(list)

        for i, page in enumerate(pdf.pages):
            words = page.extract_words(extra_attrs=["x0", "x1", "top", "size", "fontname"])
            lines = merge_words(words)

            for line in lines:
                lines_by_page[i].append({**line, "page": i})
                font_counter[line["size"]] += 1

        thresholds = [fs[0] for fs in font_counter.most_common(3)]
        if not thresholds:
            thresholds = [12.0, 11.0, 10.0]

        # Title resolution
        try:
            title = pdf.metadata.get("Title", "").strip()
            if "Microsoft Word" in title or len(title) < 5:
                raise ValueError()
        except:
            title = (
                max(lines_by_page[0], key=lambda x: x["size"])["text"]
                if lines_by_page[0] else "Untitled"
            )
        title = clean_text(title)

        for page, lines in lines_by_page.items():
            for line in lines:
                if not is_heading_candidate(line):
                    continue
                level = get_heading_level(line["text"], line["size"], thresholds)
                if level:
                    outline.append({
                        "level": level,
                        "text": line["text"],
                        "page": page
                    })

    return {
        "title": title,
        "outline": outline
    }
