import xml.etree.ElementTree as ElementTree
from typing import Union, Optional
import app.schema

def open_xml(path) -> ElementTree.Element:
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

class Parser:
    def __init__(self, path: str) -> None:
        self._node = open_xml(path)
        self.schema: app.schema.Schema = None
        self._parse_schema()

    def _parse_schema(self) -> None:
        node = self._node
        self.schema = app.schema.Schema(
            package = node.attrib.get('package'),
            id = int(node.attrib.get('id')),
            version = int(node.attrib.get('version')),
            semantic_version = node.attrib.get('semanticVersion', None),
            byte_order = app.schema.ByteOrder(node.attrib.get('byteOrder', 'littleEndian')),
            description = node.attrib.get('description', None),
            header_type = node.attrib.get('headerType', 'messageHeader')
        )

        for child_node in node.findall('./types/*'):
            self._parse_type(child_node)

        for child_node in node.findall('./message'):
            self._parse_message(child_node)

    def _parse_type(self, node: ElementTree.Element, parent: Optional[app.schema.Composite] = None) -> None:
        if node.tag == 'type':
            entry = app.schema.Type(
                name = node.attrib.get('name'),
                primitive_type = node.attrib.get('primitiveType'),
                description = node.attrib.get('description', None),
                presence = app.schema.Presence(node.attrib.get('presence', 'required')),
                null_value = node.attrib.get('nullValue', None),
                min_value = node.attrib.get('minValue', None),
                max_value = node.attrib.get('maxValue', None),
                length = int(node.attrib.get('length', '1')),
                offset = node.attrib.get('offset', None),
                semantic_type = node.attrib.get('semanticType', None),
                since_version = int(node.attrib.get('sinceVersion', 0)),
                deprecated = node.attrib.get('deprecated', None),
                value = node.text
            )
            if entry.value:
                entry.value.strip()
            if parent:
                parent.elements.append(entry)
            else:
                self.schema.types.append(entry)
        elif node.tag == 'enum':
            entry = app.schema.Enum(
                name = node.attrib.get('name'),
                encoding_type = node.attrib.get('encodingType'),
                description = node.attrib.get('description', None),
                offset = node.attrib.get('offset', None),
                since_version = int(node.attrib.get('sinceVersion', 0)),
                deprecated = node.attrib.get('deprecated', None)
            )
            for child_node in node.findall('./validValue'):
                valid_value_entry = app.schema.ValidValue(
                    name = child_node.attrib.get('name'),
                    value = child_node.text,
                    description = child_node.attrib.get('description', None),
                    since_version = int(child_node.attrib.get('sinceVersion', 0)),
                    deprecated = child_node.attrib.get('deprecated', None)
                )
                entry.elements.append(valid_value_entry)
            if parent:
                parent.elements.append(entry)
            else:
                self.schema.types.append(entry)
        elif node.tag == 'set':
            entry = app.schema.Set(
                name = node.attrib.get('name'),
                encoding_type = node.attrib.get('encodingType'),
                description = node.attrib.get('description', None),
                offset = node.attrib.get('offset', None),
                since_version = int(node.attrib.get('sinceVersion', 0)),
                deprecated = node.attrib.get('deprecated', None)
            )
            for child_node in node.findall('./choice'):
                choice_entry = app.schema.Choice(
                    name = child_node.attrib.get('name'),
                    value = child_node.text,
                    description = child_node.attrib.get('description', None),
                    since_version = int(child_node.attrib.get('sinceVersion', 0)),
                    deprecated = child_node.attrib.get('deprecated', None)
                )
                entry.elements.append(choice_entry)
            if parent:
                parent.elements.append(entry)
            else:
                self.schema.types.append(entry)
        elif node.tag == 'composite':
            entry = app.schema.Composite(
                name = node.attrib.get('name'),
                description = node.attrib.get('description', None),
                offset = node.attrib.get('offset', None),
                semantic_type = node.attrib.get('semanticType', None),
                since_version = int(node.attrib.get('sinceVersion', 0)),
                deprecated = node.attrib.get('deprecated', None)
            )
            for child_node in node:
                self._parse_type(child_node, entry)
            if parent:
                parent.elements.append(entry)
            else:
                self.schema.types.append(entry)
        elif node.tag == 'ref':
            raise Exchange('ref not implemented')
        else:
            print(f'WARNING: unknown element {child_node.tag} inside type node')

    def _parse_group(self, node: ElementTree.Element, parent: Union[app.schema.Message, app.schema.Group]) -> None:
        for child_node in node:
            if child_node.tag == 'field':
                entry = app.schema.Field(
                    name = child_node.attrib.get('name'),
                    id = int(child_node.attrib.get('id')),
                    type = child_node.attrib.get('type'),
                    description = child_node.attrib.get('description', None),
                    offset = child_node.attrib.get('offset', None),
                    presence = app.schema.Presence(child_node.attrib.get('presence', 'required')),
                    value_ref = child_node.attrib.get('valueRef', None),
                    since_version = int(child_node.attrib.get('sinceVersion', 0)),
                    deprecated = child_node.attrib.get('deprecated', None)
                )
                parent.elements.append(entry)
            elif child_node.tag == 'group':
                entry = app.schema.Group(
                    name = child_node.attrib.get('name'),
                    id = int(child_node.attrib.get('id')),
                    description = child_node.attrib.get('description', None),
                    dimension_type = child_node.attrib.get('dimensionType', 'groupSizeEncoding')
                )
                self._parse_group(child_node, entry)
                parent.elements.append(entry)
            elif child_node.tag == 'data':
                entry = app.schema.Field(
                    name = child_node.attrib.get('name'),
                    id = int(child_node.attrib.get('id')),
                    type = child_node.attrib.get('type'),
                    description = child_node.attrib.get('description', None),
                    semantic_type = child_node.attrib.get('semanticType', None),
                    since_version = int(child_node.attrib.get('sinceVersion', 0)),
                    deprecated = child_node.attrib.get('deprecated', None)
                )
                parent.elements.append(entry)
            else:
                print(f'WARNING: unknown element {child_node.tag} inside message or repeating group node')

    def _parse_message(self, node: ElementTree.Element) -> None:
        entry = app.schema.Message(
            name = node.attrib.get('name'),
            id = int(node.attrib.get('id')),
            description = node.attrib.get('description', None),
            block_length = node.attrib.get('blockLength', None),
            semantic_type = node.attrib.get('semanticType', None),
            since_version = int(node.attrib.get('sinceVersion', 0)),
            deprecated = node.attrib.get('deprecated', None)
        )
        self._parse_group(node, entry)
        self.schema.messages.append(entry)
