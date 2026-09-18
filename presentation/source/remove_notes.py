"""Remove exporter-created empty notes parts before final PPTX validation."""
from pathlib import Path
import sys
import zipfile
import xml.etree.ElementTree as ET


def strip_notes(source: Path, output: Path) -> None:
    with zipfile.ZipFile(source) as archive, zipfile.ZipFile(
        output, "w", zipfile.ZIP_DEFLATED
    ) as target:
        for item in archive.infolist():
            name = item.filename
            if name.startswith(("ppt/notesSlides/", "ppt/notesMasters/")):
                continue
            data = archive.read(name)
            if name == "[Content_Types].xml" or name.endswith(".rels"):
                root = ET.fromstring(data)
                ET.register_namespace("", root.tag.split("}")[0][1:])
                for child in list(root):
                    if any("notesSlide" in value or "notesMaster" in value for value in child.attrib.values()):
                        root.remove(child)
                data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            elif name == "ppt/presentation.xml":
                root = ET.fromstring(data)
                ET.register_namespace("p", "http://schemas.openxmlformats.org/presentationml/2006/main")
                ET.register_namespace("a", "http://schemas.openxmlformats.org/drawingml/2006/main")
                ET.register_namespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")
                for child in list(root):
                    if child.tag.endswith("}notesMasterIdLst"):
                        root.remove(child)
                data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            target.writestr(item, data)
    with zipfile.ZipFile(output) as archive:
        assert not any("notes" in name.lower() for name in archive.namelist())


if __name__ == "__main__":
    strip_notes(Path(sys.argv[1]), Path(sys.argv[2]))
