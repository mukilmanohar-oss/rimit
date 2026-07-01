#!/usr/bin/env python3
"""
Merge the cover PDF with the body PDF, normalize page sizes,
add metadata, and write the final deliverable to /home/z/my-project/download/.
"""
import os
from pypdf import PdfReader, PdfWriter

COVER_PDF = "/home/z/my-project/scripts/cover.pdf"
BODY_PDF = "/home/z/my-project/scripts/body.pdf"
OUTPUT_PDF = "/home/z/my-project/download/RIMIT_Development_Plan.pdf"

A4_W, A4_H = 595.28, 841.89  # A4 in points

def normalize_page_to_a4(page):
    """Force every page to exact A4 dimensions (no tolerance) for consistency."""
    box = page.mediabox
    w, h = float(box.width), float(box.height)
    # Always scale to exact A4 (even tiny mismatches cause QA failures)
    if abs(w - A4_W) > 0.1 or abs(h - A4_H) > 0.1:
        page.scale_to(A4_W, A4_H)
    return page

def main():
    os.makedirs(os.path.dirname(OUTPUT_PDF), exist_ok=True)

    writer = PdfWriter()

    # Cover as page 1
    cover_reader = PdfReader(COVER_PDF)
    print(f"Cover PDF: {len(cover_reader.pages)} page(s)")
    for page in cover_reader.pages:
        writer.add_page(normalize_page_to_a4(page))

    # Body pages follow
    body_reader = PdfReader(BODY_PDF)
    print(f"Body PDF: {len(body_reader.pages)} page(s)")
    for page in body_reader.pages:
        writer.add_page(normalize_page_to_a4(page))

    # Metadata
    writer.add_metadata({
        '/Title': 'RIMIT B2B Aggregator Development Plan',
        '/Author': 'Z.ai',
        '/Subject': 'Comprehensive Development Plan & Architectural Blueprint for RIMIT Education & SPES Education',
        '/Creator': 'Z.ai',
        '/Producer': 'Z.ai PDF Pipeline',
        '/Keywords': 'RIMIT, SPES, B2B, University Aggregator, Admission Management, Django, PostgreSQL, Architecture',
    })

    with open(OUTPUT_PDF, 'wb') as f:
        writer.write(f)

    final_size = os.path.getsize(OUTPUT_PDF)
    print(f"\n✓ Final PDF written to: {OUTPUT_PDF}")
    print(f"  Total pages: {len(cover_reader.pages) + len(body_reader.pages)}")
    print(f"  File size: {final_size / 1024:.1f} KB ({final_size / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    main()
