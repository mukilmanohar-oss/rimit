#!/usr/bin/env python3
"""
Build the RIMIT B2B Aggregator Development Plan body PDF.

Pipeline:
  1. helpers.py registers fonts, palette, styles, helpers (no circular deps)
  2. TocDocTemplate + multiBuild for auto-TOC
  3. 16 content sections with rich body text, tables, diagrams
  4. Output: /home/z/my-project/scripts/body.pdf (cover merged separately)
"""
import os
import sys

# Ensure local scripts dir is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from helpers import (
    TocDocTemplate, footer_arabic,
    PAGE_W, PAGE_H, MARGIN, CONTENT_W, CONTENT_H,
    TOC_LEVEL_0, TOC_LEVEL_1,
)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import PageBreak
from reportlab.platypus.tableofcontents import TableOfContents

# Import section builders
from sections_content import (
    section_exec_strategy,
    section_rfp_deconstruction,
    section_arch_visualizations,
    section_component_spec,
    section_db_schema,
    section_api_specs,
    section_ui_inventory,
    section_integrations,
    section_security,
    section_sprint_plan,
    section_cost,
    section_risk,
    section_test_strategy,
    section_devops,
    section_assumptions,
    section_validation,
)


def section_toc():
    """Table of Contents."""
    toc = TableOfContents()
    toc.levelStyles = [TOC_LEVEL_0, TOC_LEVEL_1]
    return [toc, PageBreak()]


def main():
    output = "/home/z/my-project/scripts/body.pdf"

    doc = TocDocTemplate(
        output,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title="RIMIT B2B Aggregator Development Plan",
        author="Z.ai",
        subject="Comprehensive Development Plan & Architectural Blueprint",
        creator="Z.ai",
    )

    story = []
    story.extend(section_toc())

    builders = [
        section_exec_strategy,
        section_rfp_deconstruction,
        section_arch_visualizations,
        section_component_spec,
        section_db_schema,
        section_api_specs,
        section_ui_inventory,
        section_integrations,
        section_security,
        section_sprint_plan,
        section_cost,
        section_risk,
        section_test_strategy,
        section_devops,
        section_assumptions,
        section_validation,
    ]

    for builder in builders:
        story.extend(builder())

    doc.multiBuild(story, onFirstPage=footer_arabic, onLaterPages=footer_arabic)
    print(f"Body PDF written to: {output}")
    print(f"Total pages: {doc.page}")


if __name__ == "__main__":
    main()
