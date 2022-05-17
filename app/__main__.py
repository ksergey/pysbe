import xml.etree.ElementTree as ElementTree

from app.schema import Schema

PATH = '/home/ksergey/dev/pysbe/resources/FixBinary.xml'

def open_xml_schema(path) -> ElementTree.Element:
    # strip namespace inside schema
    def strip(node):
        if node.tag.startswith('{'):
            node.tag = node.tag.split('}', 1)[1]
        for key in node.attrib.keys():
            if key.startswith('{'):
                k2 = key.split('}', 1)[1]
                node.attrib[k2] = node.attrib[key]
                del node.attrib[key]
        for child in node:
            strip(child)

    root = ElementTree.parse(path).getroot()
    strip(root)
    return root

def main() -> None:
    schema = Schema(open_xml_schema(PATH))
    print(schema.types)

if __name__ == '__main__':
    main()
