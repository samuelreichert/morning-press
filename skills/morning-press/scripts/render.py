"""Portable two-column PDF and Markdown rendering, with bounded pagination."""
from __future__ import annotations

import io
import json
import math
import os
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

from core import private_write, validate_issue


def markdown(issue, profile):
    pub = profile["publication"]
    lines = [f"# {pub['title']}", "", pub["subtitle"], "", f"{issue['date']} | #{issue['number']:03d}", ""]
    if issue["demo"]:
        lines += ["**DEMONSTRATION - fictional content, not current information.**", ""]
    sections = {s["id"]: s for s in issue["sections"]}
    for pref in profile["sections"]:
        if not pref["enabled"]:
            continue
        section = sections[pref["id"]]
        lines += [f"## {pref['title']}", ""]
        if section["note"]:
            lines += [section["note"], ""]
        if section["status"] != "ready":
            lines += [f"Status: {section['status']}", ""]
        for item in section["items"]:
            title = item["title"].replace("[", "\\[").replace("]", "\\]")
            title = f"[{title}]({item['url']})" if item["url"] and pub["links"]["clickable"] else title
            lines += [f"### {title}", "", *[p + "\n" for p in item["paragraphs"]]]
            if item["source"]:
                src = item["source"]
                lines += [f"Source: {src['publisher']}. Checked: {src['checked_at']}.", ""]
    return "\n".join(lines).rstrip() + "\n"


def pdf_bytes(issue, profile):
    import reportlab
    from reportlab.graphics import renderPDF
    from reportlab.graphics.barcode.qr import QrCodeWidget
    from reportlab.graphics.shapes import Drawing
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import BaseDocTemplate, Flowable, Frame, PageTemplate, Paragraph, Spacer
    from pypdf import PdfReader

    pub = profile["publication"]
    fonts = Path(reportlab.__file__).parent / "fonts"
    for name, file in (("Press", "Vera.ttf"), ("PressBold", "VeraBd.ttf")):
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(fonts / file)))
    # Fail clearly instead of silently drawing missing glyphs in an unsupported script.
    texts = [pub["title"], pub["subtitle"]]
    texts += [s["title"] for s in profile["sections"] if s["enabled"]]
    for s in issue["sections"]:
        texts.append(s["note"])
        for item in s["items"]:
            texts += [item["title"], *item["paragraphs"]]
            if item["source"]:
                texts += [item["source"]["publisher"], item["source"]["checked_at"]]
    for text in texts:
        missing = {c for c in text if not c.isspace() and ord(c) not in pdfmetrics.getFont("Press").face.charToGlyph}
        if missing:
            raise ValueError("PDF font does not cover these characters: " + " ".join(sorted(missing)) + ". Use Markdown or add a licensed font covering this script.")

    width, height = A4 if pub["paper"] == "A4" else letter
    margin, gutter = 14 * mm, 7 * mm
    col = (width - margin * 2 - gutter) / 2
    accent = colors.HexColor("#193F45") if pub["color"] == "color" else colors.black
    muted = colors.HexColor("#566365") if pub["color"] == "color" else colors.HexColor("#444444")
    size = pub["body_size"]
    styles = {
        "body": ParagraphStyle("body", fontName="Press", fontSize=size, leading=size * 1.43, spaceAfter=7, textColor=colors.HexColor("#1E2426"), alignment=TA_LEFT, allowWidows=0, allowOrphans=0),
        "section": ParagraphStyle("section", fontName="PressBold", fontSize=15, leading=18, spaceBefore=10, spaceAfter=10, textColor=accent, keepWithNext=True),
        "title": ParagraphStyle("title", fontName="PressBold", fontSize=12, leading=15, spaceAfter=6, textColor=colors.black, keepWithNext=True),
        "source": ParagraphStyle("source", fontName="Press", fontSize=8, leading=11, spaceAfter=10, textColor=muted),
    }
    layout = {"version": 1, "paper": pub["paper"], "pages": 0, "digital_links": [], "qr_codes": [], "boxes": []}

    class TracedParagraph(Paragraph):
        def draw(self):
            x, y = self.canv.absolutePosition(0, 0)
            layout["boxes"].append({"page": self.canv.getPageNumber(), "rect": [x, y, x + self.width, y + self.height]})
            super().draw()

    class Headline(Flowable):
        def __init__(self, item):
            super().__init__()
            self.item = item
            self.qr = bool(pub["links"]["qr"] and item["url"])
            if self.qr:
                self.qr_widget = QrCodeWidget(item["url"], barLevel="M", barBorder=4)
                self.qr_widget.qr.make()
                self.qr_modules = self.qr_widget.qr.getModuleCount() + 8
            self.keepWithNext = True

        def wrap(self, availWidth, availHeight):
            self.width = availWidth
            self.qr_size = max(64, math.ceil(self.qr_modules * 0.4 * mm)) if self.qr else 0
            if self.qr_size > availWidth * 0.45:
                raise ValueError("QR destination is too long for a readable printed code. Use a shorter canonical public URL or disable printed QR codes.")
            self.title = Paragraph(escape(self.item["title"]), styles["title"])
            self.tw, self.th = self.title.wrap(availWidth - (self.qr_size + 8 if self.qr else 0), availHeight)
            self.height = max(self.th, self.qr_size) + 7
            return self.width, self.height

        def draw(self):
            x, y = self.canv.absolutePosition(0, 0)
            top = self.height - 7
            self.title.drawOn(self.canv, 0, top - self.th)
            rect = [x, y + top - self.th, x + self.tw, y + top]
            layout["boxes"].append({"page": self.canv.getPageNumber(), "rect": rect})
            if self.item["url"] and pub["links"]["clickable"]:
                self.canv.linkURL(self.item["url"], (0, top-self.th, self.tw, top), relative=1, thickness=0)
                layout["digital_links"].append({"page": self.canv.getPageNumber(), "rect": rect, "url": self.item["url"]})
            if self.qr:
                qr = self.qr_widget
                a, b, c, d = qr.getBounds()
                drawing = Drawing(self.qr_size, self.qr_size, transform=[self.qr_size/(c-a), 0, 0, self.qr_size/(d-b), 0, 0])
                drawing.add(qr)
                qx, qy = self.width - self.qr_size, top - self.qr_size
                renderPDF.draw(drawing, self.canv, qx, qy)
                layout["qr_codes"].append({"page": self.canv.getPageNumber(), "rect": [x+qx,y+qy,x+qx+self.qr_size,y+qy+self.qr_size], "url": self.item["url"], "module_mm": self.qr_size / self.qr_modules / mm})

    buffer = io.BytesIO()
    document = BaseDocTemplate(buffer, pagesize=(width,height), leftMargin=margin, rightMargin=margin, topMargin=margin, bottomMargin=margin, title=pub["title"], author="Morning Press")

    def furniture(canvas, doc):
        if doc.page > pub["pages"]:
            raise ValueError(f"Content exceeds the requested {pub['pages']} PDF pages. Edit the copy or change the page budget; do not shrink the type.")
        canvas.saveState()
        canvas.setFillColor(accent)
        if doc.page == 1:
            title = pub["title"]
            title_size = 29
            while title_size > 19 and pdfmetrics.stringWidth(title, "PressBold", title_size) > width - 2*margin:
                title_size -= 1
            if pdfmetrics.stringWidth(title, "PressBold", title_size) > width - 2*margin:
                raise ValueError("Newspaper title is too long for the masthead")
            canvas.setFont("PressBold", title_size)
            canvas.drawString(margin, height-margin-28, title)
            if pdfmetrics.stringWidth(pub["subtitle"], "Press", 9) > width - 2*margin:
                raise ValueError("Subtitle is too long for the masthead")
            canvas.setFont("Press", 9)
            canvas.drawString(margin, height-margin-45, pub["subtitle"])
            rule_y = height-margin-57
        else:
            canvas.setFont("PressBold", 9)
            canvas.drawString(margin, height-margin-9, pub["title"])
            rule_y = height-margin-18
        canvas.setStrokeColor(accent)
        canvas.setLineWidth(0.8)
        canvas.line(margin,rule_y,width-margin,rule_y)
        canvas.setFillColor(muted)
        canvas.setFont("Press", 8)
        canvas.drawString(margin, 23, f"{issue['date']}  |  #{issue['number']:03d}  |  {pub['timezone']}")
        canvas.drawRightString(width-margin, 23, f"{doc.page} / {pub['pages']}")
        if issue["demo"]:
            canvas.setFont("PressBold", 8)
            canvas.drawRightString(width-margin, height-19, "DEMONSTRATION - FICTIONAL CONTENT")
        canvas.restoreState()

    def frames(first):
        top = height-margin-(68 if first else 29)
        return [Frame(margin+i*(col+gutter), margin, col, top-margin, leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0, id=f"{first}-{i}") for i in range(2)]

    document.addPageTemplates([PageTemplate(id="cover", frames=frames(True), onPage=furniture, autoNextPageTemplate="inside"), PageTemplate(id="inside", frames=frames(False), onPage=furniture)])
    flow = []
    sections = {s["id"]: s for s in issue["sections"]}
    for pref in profile["sections"]:
        if not pref["enabled"]:
            continue
        section = sections[pref["id"]]
        flow.append(TracedParagraph(escape(pref["title"]), styles["section"]))
        if section["note"]:
            flow.append(TracedParagraph(escape(section["note"]), styles["body"]))
        if section["status"] != "ready":
            flow.append(TracedParagraph("Status: " + section["status"].replace("_", " "), styles["body"]))
        for item in section["items"]:
            flow.append(Headline(item))
            for text in item["paragraphs"]:
                flow.append(TracedParagraph(escape(text), styles["body"]))
            if item["source"]:
                src = item["source"]
                flow.append(TracedParagraph(escape(f"{src['publisher']} | checked {src['checked_at']}"), styles["source"]))
            flow.append(Spacer(1, 5))
    document.build(flow)
    data = buffer.getvalue()
    reader = PdfReader(io.BytesIO(data))
    layout["pages"] = len(reader.pages)
    if layout["pages"] != pub["pages"]:
        raise ValueError(f"Content fills {layout['pages']} of {pub['pages']} requested PDF pages. Add relevant verified material or reduce the page budget.")
    expected = Counter(x["url"] for x in layout["digital_links"])
    actual = Counter()
    for n, page in enumerate(reader.pages, 1):
        if issue["demo"] and "DEMONSTRATION" not in page.extract_text():
            raise ValueError("Missing demonstration label")
        for annotation in page.get("/Annots", []):
            a = annotation.get_object()
            if a.get("/A", {}).get("/URI"):
                actual[str(a["/A"]["/URI"])] += 1
                rect = [float(v) for v in a["/Rect"]]
                if not (margin-1 <= rect[0] < rect[2] <= width-margin+1 and margin-1 <= rect[1] < rect[3] <= height-margin+1):
                    raise ValueError("PDF hyperlink falls outside the content margins")
    if actual != expected:
        raise ValueError("PDF hyperlinks do not match the layout record")
    for box in layout["boxes"] + layout["qr_codes"]:
        x1,y1,x2,y2 = box["rect"]
        if not (margin-1 <= x1 < x2 <= width-margin+1 and margin-1 <= y1 < y2 <= height-margin+1):
            raise ValueError("A content box falls outside the printable area")
    layout["validation"] = {"page_budget": "passed", "margins": "passed", "pdf_links": "passed", "visual_review": "required"}
    return data, layout


def render(issue, profile, destination):
    validate_issue(issue, profile)
    # Build and validate all representations before publishing any files.
    representations = {}
    if profile["publication"]["format"] in ("pdf", "both"):
        data, layout = pdf_bytes(issue, profile)
        representations["edition.pdf"] = data
        representations["layout.json"] = json.dumps(layout, ensure_ascii=False, indent=2).encode()
    if profile["publication"]["format"] in ("markdown", "both"):
        representations["edition.md"] = markdown(issue, profile).encode()
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    for name, data in representations.items():
        path = destination / name
        with path.open("xb") as stream:
            stream.write(data)
        os.chmod(path, 0o600)
    private_write(destination / "issue.json", json.dumps(issue, ensure_ascii=False, indent=2) + "\n")
    private_write(destination / "profile.json", json.dumps(profile, ensure_ascii=False, indent=2) + "\n")
    return list(destination / name for name in representations)
