from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


def build_pdf(title: str, chapters: list[dict], output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=1.2 * inch,
        rightMargin=1.2 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "BookTitle",
        parent=styles["Title"],
        fontSize=28,
        textColor=colors.HexColor("#1A1A2E"),
        alignment=TA_CENTER,
        spaceAfter=20,
    )

    chapter_heading_style = ParagraphStyle(
        "ChapterHeading",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#16213E"),
        spaceBefore=12,
        spaceAfter=10,
    )

    subheading_style = ParagraphStyle(
        "SubHeading",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#0F3460"),
        spaceBefore=8,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "BookBody",
        parent=styles["Normal"],
        fontSize=11,
        leading=18,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    )

    toc_style = ParagraphStyle(
        "TOC",
        parent=styles["Normal"],
        fontSize=11,
        leading=20,
    )

    story = []

    # title page
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph(title, title_style))
    story.append(PageBreak())

    # table of contents
    story.append(Paragraph("Table of Contents", chapter_heading_style))
    story.append(Spacer(1, 0.2 * inch))
    for ch in chapters:
        story.append(Paragraph(f"{ch['chapter_number']}. {ch['title']}", toc_style))
    story.append(PageBreak())

    # chapters
    for ch in chapters:
        story.append(Paragraph(f"Chapter {ch['chapter_number']}: {ch['title']}", chapter_heading_style))
        story.append(Spacer(1, 0.15 * inch))

        for block in ch["content"].split("\n\n"):
            block = block.strip()
            if not block:
                continue

            if block.startswith("##"):
                text = block.replace("##", "").strip()
                story.append(Paragraph(text, subheading_style))
            else:
                story.append(Paragraph(block, body_style))

        story.append(PageBreak())

    doc.build(story)