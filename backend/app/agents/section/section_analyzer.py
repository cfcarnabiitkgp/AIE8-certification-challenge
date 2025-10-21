"""Section parser and analyzer for markdown papers."""
import re
from typing import List
import logging
from app.models.schemas import Section

logger = logging.getLogger(__name__)


class SectionAnalyzer:
    """
    Parses markdown content into sections and manages section-wise analysis.

    Provides utilities for:
    - Parsing markdown into structured sections
    - Extracting section metadata (line numbers, hierarchy)
    - Section filtering and selection
    """

    @staticmethod
    def parse_markdown(content: str) -> List[Section]:
        """
        Parse markdown content into hierarchical sections using numbered format.

        Handles numbered sections like:
        # 1. Introduction
        ## 1.1 Background
        ### 1.1.1 Details

        Subsection content is included in parent section's content.
        Only returns top-level sections (e.g., "1.", "2.", "3.") with all subsection
        content merged into the parent.

        Args:
            content: Markdown text with numbered sections

        Returns:
            List of Section Pydantic models (top-level sections only) with:
                - title: Section title (without number)
                - content: Section content including all subsections
                - level: Header level (1-6)
                - line_start: Starting line number
                - line_end: Ending line number
                - section_number: Extracted section number (e.g., "3.1.2")
                - parent_section: Parent section number if applicable
                - subsections: List of direct child section numbers
        """
        all_sections = []
        lines = content.split('\n')
        current_section_dict = {}
        line_num = 0

        for line in lines:
            line_num += 1

            # Match headers with numbering:
            # Format 1: "# 1. Title" (period after number for top-level)
            # Format 2: "## 3.1 Title" (no period for subsections)
            header_match = re.match(r'^(#{1,6})\s+(\d+(?:\.\d+)*)\.?\s+(.+)$', line)

            if header_match:
                # Save previous section if it exists
                if current_section_dict:
                    current_section_dict["line_end"] = line_num - 1
                    all_sections.append(current_section_dict)

                # Extract header info
                level = len(header_match.group(1))
                section_num = header_match.group(2)  # e.g., "3.1.2" or None
                title = header_match.group(3).strip()

                # Determine parent section
                parent_num = None
                if section_num and '.' in section_num:
                    parent_num = '.'.join(section_num.split('.')[:-1])

                # Start new section
                current_section_dict = {
                    "title": title,
                    "content": "",
                    "level": level,
                    "line_start": line_num,
                    "section_number": section_num,
                    "parent_section": parent_num,
                    "subsections": []
                }
            else:
                # Add content to current section
                if current_section_dict:
                    current_section_dict["content"] += line + "\n"

        # Add last section
        if current_section_dict:
            current_section_dict["line_end"] = line_num
            all_sections.append(current_section_dict)

        # Build parent-child relationships
        section_map = {s["section_number"]: s for s in all_sections if s["section_number"]}
        for section in all_sections:
            if section["section_number"] and section["parent_section"]:
                parent = section_map.get(section["parent_section"])
                if parent:
                    parent["subsections"].append(section["section_number"])

        # Group subsections into parent sections
        # Only return top-level sections (single digit like "1", "2", "3")
        top_level_sections = []

        for section in all_sections:
            section_num = section.get("section_number")

            # Skip sections without numbers (like title, preamble)
            if not section_num:
                continue

            # Check if this is a top-level section (e.g., "1", "2", "3")
            if '.' not in section_num:
                # This is a top-level section
                # Collect all content from subsections
                merged_content = section["content"]

                # Find and merge all subsections recursively
                for other_section in all_sections:
                    other_num = other_section.get("section_number")
                    if other_num and other_num.startswith(section_num + "."):
                        # This is a subsection - add its content with header
                        subsection_header = f"\n## {other_num}. {other_section['title']}\n\n"
                        merged_content += subsection_header + other_section["content"]

                # Create the merged section
                section["content"] = merged_content
                section["line_end"] = max(
                    s["line_end"] for s in all_sections
                    if s.get("section_number") and s.get("section_number").startswith(section_num)
                )

                top_level_sections.append(Section(**section))

        logger.info(f"Parsed {len(top_level_sections)} top-level sections from markdown")
        return top_level_sections

    @staticmethod
    def filter_sections_by_keywords(
        sections: List[Section],
        keywords: List[str]
    ) -> List[Section]:
        """
        Filter sections by title keywords.

        Args:
            sections: List of Section Pydantic models
            keywords: Keywords to match (case-insensitive)

        Returns:
            Filtered list of sections
        """
        if not keywords or "*" in keywords:
            return sections

        filtered = []
        for section in sections:
            title_lower = section.title.lower()
            if any(keyword.lower() in title_lower for keyword in keywords):
                filtered.append(section)

        return filtered

    @staticmethod
    def get_section_summary(sections: List[Section]) -> str:
        """
        Create a summary of section structure.

        Args:
            sections: List of Section Pydantic models

        Returns:
            Formatted string showing document structure
        """
        lines = []
        for i, section in enumerate(sections, 1):
            indent = "  " * (section.level - 1) if section.level > 0 else ""
            lines.append(f"{indent}{i}. {section.title}")

        return "\n".join(lines)

    @staticmethod
    def estimate_section_tokens(section: Section) -> int:
        """
        Estimate token count for a section (rough approximation).

        Args:
            section: Section Pydantic model

        Returns:
            Estimated token count
        """
        # Rough estimate: 4 characters ≈ 1 token
        return len(section.content) // 4

    @staticmethod
    def truncate_section_content(
        section: Section,
        max_tokens: int
    ) -> Section:
        """
        Truncate section content to token limit.

        Args:
            section: Section Pydantic model
            max_tokens: Maximum tokens allowed

        Returns:
            Section with truncated content
        """
        current_tokens = SectionAnalyzer.estimate_section_tokens(section)

        if current_tokens <= max_tokens:
            return section

        # Truncate content
        max_chars = max_tokens * 4
        truncated_content = section.content[:max_chars] + "\n\n... [content truncated for length]"

        return Section(
            title=section.title,
            content=truncated_content,
            level=section.level,
            line_start=section.line_start,
            line_end=section.line_end
        )
