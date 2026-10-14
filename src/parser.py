"""High-speed .docx text and metadata extractor.
Extracts content by reading the OpenXML package directly via zipfile,
with fallback to python-docx. Operates 100% offline.
"""

import os
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

# OpenXML Namespaces
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "dc": "http://purl.org/dc/elements/1.1/",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dcterms": "http://purl.org/dc/terms/",
    "ep": "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
}

@dataclass
class ParsedDocx:
    file_path: str
    file_name: str
    file_size: int
    modified_time: float
    content: str
    word_count: int
    title: str = ""
    author: str = ""
    last_modified_by: str = ""
    created_at: str = ""
    error: Optional[str] = None

class DocxParser:
    """Extracts text and metadata from .docx files rapidly."""

    @staticmethod
    def parse(file_path: str) -> ParsedDocx:
        path = Path(file_path)
        if not path.exists():
            return ParsedDocx(
                file_path=file_path,
                file_name=path.name,
                file_size=0,
                modified_time=0.0,
                content="",
                word_count=0,
                error="File does not exist"
            )

        stat = path.stat()
        file_size = stat.st_size
        mtime = stat.st_mtime

        # Ignore temporary lock files (e.g. ~$document.docx)
        if path.name.startswith("~$"):
            return ParsedDocx(
                file_path=file_path,
                file_name=path.name,
                file_size=file_size,
                modified_time=mtime,
                content="",
                word_count=0,
                error="Temporary lock file"
            )

        # Attempt fast stream extraction
        try:
            return DocxParser._parse_fast(file_path, stat)
        except Exception as e_fast:
            # Fallback to python-docx if fast parser fails
            try:
                return DocxParser._parse_fallback(file_path, stat)
            except Exception as e_fallback:
                return ParsedDocx(
                    file_path=file_path,
                    file_name=path.name,
                    file_size=file_size,
                    modified_time=mtime,
                    content="",
                    word_count=0,
                    error=f"Extraction failed: {str(e_fast)} | {str(e_fallback)}"
                )

    @staticmethod
    def _parse_fast(file_path: str, stat: os.stat_result) -> ParsedDocx:
        path = Path(file_path)
        content_paragraphs = []
        title = ""
        author = ""
        last_modified_by = ""
        created_at = ""

        with zipfile.ZipFile(file_path, "r") as z:
            # 1. Parse Document Body
            if "word/document.xml" in z.namelist():
                xml_content = z.read("word/document.xml")
                root = ET.fromstring(xml_content)
                
                # Iterate over paragraphs <w:p>
                for p in root.iter(f"{{{NS['w']}}}p"):
                    # Extract all text nodes <w:t> in this paragraph
                    p_text = "".join(t.text for t in p.iter(f"{{{NS['w']}}}t") if t.text)
                    if p_text.strip():
                        content_paragraphs.append(p_text.strip())

            # 2. Parse Core Metadata (Author, Title, Created)
            if "docProps/core.xml" in z.namelist():
                try:
                    core_xml = z.read("docProps/core.xml")
                    core_root = ET.fromstring(core_xml)
                    
                    t_elem = core_root.find("dc:title", NS)
                    if t_elem is not None and t_elem.text:
                        title = t_elem.text.strip()
                        
                    a_elem = core_root.find("dc:creator", NS)
                    if a_elem is not None and a_elem.text:
                        author = a_elem.text.strip()
                        
                    mod_elem = core_root.find("cp:lastModifiedBy", NS)
                    if mod_elem is not None and mod_elem.text:
                        last_modified_by = mod_elem.text.strip()
                        
                    c_elem = core_root.find("dcterms:created", NS)
                    if c_elem is not None and c_elem.text:
                        created_at = c_elem.text.strip()
                except Exception:
                    pass

        full_text = "\n\n".join(content_paragraphs)
        word_count = len(full_text.split())

        return ParsedDocx(
            file_path=str(path.resolve()),
            file_name=path.name,
            file_size=stat.st_size,
            modified_time=stat.st_mtime,
            content=full_text,
            word_count=word_count,
            title=title,
            author=author,
            last_modified_by=last_modified_by,
            created_at=created_at,
            error=None
        )

    @staticmethod
    def _parse_fallback(file_path: str, stat: os.stat_result) -> ParsedDocx:
        import docx
        path = Path(file_path)
        doc = docx.Document(file_path)
        
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    paragraphs.append(row_text)

        full_text = "\n\n".join(paragraphs)
        word_count = len(full_text.split())

        title = ""
        author = ""
        try:
            core_props = doc.core_properties
            title = core_props.title or ""
            author = core_props.author or ""
        except Exception:
            pass

        return ParsedDocx(
            file_path=str(path.resolve()),
            file_name=path.name,
            file_size=stat.st_size,
            modified_time=stat.st_mtime,
            content=full_text,
            word_count=word_count,
            title=title,
            author=author,
            error=None
        )

