from __future__ import annotations
from enum import Enum
from typing import Optional
import xml.etree.ElementTree as ElementTree

def openXMLAndStripNs(path: str) -> ElementTree.Element:
    file = open(path, 'r', encoding='utf-8')
    it = ElementTree.iterparse(file)

    # strip namespace
    for _, el in it:
        _, _, el.tag = el.tag.rpartition('}')

    return it.root

def injectRootAttr(node: ElementTree.Element, root: ElementTree.Element):
    for child in node:
        child.attrib['__root__'] = root
        injectRootAttr(child, root)

def getDocumentRoot(node: ElementTree.Element) -> ElementTree.Element:
    return node.attrib.get('__root__')

class Presence(Enum):
    REQUIRED = 'required'
    OPTIONAL = 'optional'
    CONSTANT = 'constant'

class ByteOrder(Enum):
    LITTLE_ENDIAN = 'littleEndian'
    BIG_ENDIAN = 'bitEndian'

def cast(value: Optional[str], type) -> Optional[dest]:
    if value:
        return type(value)
    return None

class PrimitiveType:
    def __init__(self, name: str, size: int, nullValue: str, minValue: str, maxValue: str):
        self.name = name
        self.size = size
        self.nullValue = nullValue
        self.minValue = minValue
        self.maxValue = maxValue

    @staticmethod
    def get(name: str) -> PrimitiveType:
        storage = {
            'char': PrimitiveType('char', 1,  "CHAR_NULL", "CHAR_MIN", "CHAR_MAX"),
            'int8': PrimitiveType('int8', 1,  "INT8_NULL", "INT8_MIN", "INT8_MAX"),
            'int16': PrimitiveType('int16', 2,  "INT16_NULL", "INT16_MIN", "INT16_MAX"),
            'int32': PrimitiveType('int32', 4,  "INT32_NULL", "INT32_MIN", "INT32_MAX"),
            'int64': PrimitiveType('int64', 8,  "INT64_NULL", "INT64_MIN", "INT64_MAX"),
            'uint8': PrimitiveType('uint8', 1,  "INT8_NULL", "INT8_MIN", "INT8_MAX"),
            'uint16': PrimitiveType('uint16', 2,  "UINT16_NULL", "UINT16_MIN", "UINT16_MAX"),
            'uint32': PrimitiveType('uint32', 4,  "UINT32_NULL", "UINT32_MIN", "UINT32_MAX"),
            'uint64': PrimitiveType('uint64', 8,  "UINT64_NULL", "UINT64_MIN", "UINT64_MAX"),
            'float': PrimitiveType('float', 4,  "FLOAT_NULL", "FLOAT_MIN", "FLOAT_MAX"),
            'double': PrimitiveType('double', 8,  "DOUBLE_NULL", "DOUBLE_MIN", "DOUBLE_MAX")
        }

        return storage.get(name)

class Type:
    def __init__(self, root: ElementTree.Element) -> None:
        self.name = root.attrib.get('name')
        self.description = root.attrib.get('description', None)
        self.presence = Presence(root.attrib.get('presence', 'required'))
        self.nullValue = root.attrib.get('nullValue')
        self.minValue = root.attrib.get('minValue')
        self.maxValue = root.attrib.get('maxValue')
        self.length = int(root.attrib.get('length', '1'))
        self.offset = cast(root.attrib.get('offset', None), int)
        self.primitiveType = PrimitiveType.get(root.attrib.get('primitiveType'))
        self.semanticType = root.attrib.get('semanticType', None)
        self.sinceVersion = int(root.attrib.get('sinceVersion', '0'))
        self.deprecated = cast(root.attrib.get('deprecated', None), int)
        self.valueRef = root.attrib.get('valueRef', None)
        self._constValue = root.text.strip() if root.text else None

        if self.valueRef:
            if self.valueRef.find('.') == -1:
                raise Exception(f'valueRef ({self.valueRef}) format not valid (type: "{self.name}")')
            if self.presence != Presence.CONSTANT:
                raise Exception(f'presence must be "constant" when valueRef is set (type: "{self.name}")')

        if self.presence == Presence.CONSTANT:
            if self.valueRef is None:
                if self._constValue is None:
                    raise Exception(f'type presence is "constant" but XML node has no data (type: "{self.name}")')
            else:
                name, value = self.valueRef.split('.')
                node = getDocumentRoot(root).find(f'.//types/enum[@name="{name}"]')
                if node is None:
                    raise Exception(f'type {name} not found (type: "{self.name}")')
                if Enum(node).hasValue(value) is None:
                    raise Exception(f'value {value} is not exists in enum {name} (type: "{self.name}")')

        if self.nullValue is None:
            self.nullValue = self.primitiveType.nullValue

        if self.minValue is None:
            self.minValue = self.primitiveType.minValue

        if self.maxValue is None:
            self.maxValue = self.primitiveType.maxValue

    def __str__(self) -> str:
        return f'Type(name="{self.name}", primitiveType={self.primitiveType.name}, encodedLength={self.encodedLength}, constValue={self._constValue})'

    @property
    def encodedLength(self) -> int:
        if self.presence == Presence.CONSTANT:
            return 0
        return self.primitiveType.size * self.length

    @property
    def constValue(self) -> str:
        if self.presence != Presence.CONSTANT:
            raise Exception(f'type is not "constant" presence (type: "{self.name}")')
        return self._constValue

class Composite:
    def __init__(self, root: ElementTree.Element) -> None:
        self.name = root.attrib.get('name')
        self.offset = cast(root.attrib.get('offset', None), int)
        self.description = root.attrib.get('description', None)
        self.semanticType = root.attrib.get('semanticType', None)
        self.sinceVersion = int(root.attrib.get('sinceVersion', '0'))
        self.deprecated = cast(root.attrib.get('deprecated', None), int)
        self.elements = Composite.loadElements(root)

        # check valid offset
        offset = 0
        for element in self.elements:
            if element.offset:
                if offset > element.offset:
                    raise Exception(f'composite element has incorrect offset (composite: "{self.name}")')
                offset = element.offset
            else:
                offset += element.encodedLength

    def __str__(self) -> str:
        return f'Composite(name="{self.name}", elements=({len(self.elements)}), encodedLength={self.encodedLength})'

    @staticmethod
    def loadElements(root: ElementTree.Element) -> list:
        result = []
        for node in root:
            if node.tag == 'type':
                result.append(Type(node))
            elif node.tag == 'composite':
                result.append(Composite(node))
            elif node.tag == 'enum':
                result.append(Enum(node))
            elif node.tag == 'set':
                result.append(Set(node))
        return result

    @property
    def encodedLength(self) -> int:
        length = 0

        for element in self.elements:
            if element.offset:
                length = element.offset
            if element.presence != Presence.CONSTANT:
                length += element.encodedLength

        return length

class Enum:
    def __init__(self, root: ElementTree.Element) -> None:
        self.name = root.attrib.get('name')
        self.description = root.attrib.get('description', None)
        self.sinceVersion = int(root.attrib.get('sinceVersion', '0'))
        self.deprecated = cast(root.attrib.get('deprecated', None), int)
        self.offset = cast(root.attrib.get('offset', None), int)
        self.validValues = self.loadValidValues(root)

        encodingTypeStr = root.attrib.get('encodingType')
        if encodingTypeStr in [ 'char', 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64' ]:
            self.encodingType = PrimitiveType.get(encodingTypeStr)
        else:
            node = getDocumentRoot(root).find(f'.//types/type[@name="{encodingTypeStr}"]')
            if node is None:
                raise Exception(f'type {encodingTypeStr} not found (enum: "{self.name}")')
            type = Type(node)
            if type.length != 1:
                raise Exception(f'illegal encodingType "{encodingTypeStr}" (enum: "{self.name}")')
            self.encodingType = type.primitiveType

        self.nullValue =  root.attrib.get('nullValue', self.encodingType.nullValue)

    def __str__(self) -> str:
        return f'Enum(name="{self.name}", encodingType={self.encodingType.name}, encodedLength={self.encodedLength})'

    @staticmethod
    def loadValidValues(root: ElementTree.Element) -> list:
        result = []
        for node in root.findall('./validValue'):
            result.append({
                'name': node.attrib.get('name'),
                'description': node.attrib.get('description', None),
                'sinceVersion': int(node.attrib.get('sinceVersion', '0')),
                'deprecated': cast(node.attrib.get('deprecated', None), int),
                'value': node.text.strip()
            })
        return result

    def hasValue(self, name: str) -> bool:
        return len([entry for entry in self.validValues if entry['name'] == name]) > 0

    @property
    def encodedLength(self) -> int:
        return self.encodingType.size

class Set:
    def __init__(self, root: ElementTree.Element) -> None:
        self.name = root.attrib.get('name')
        self.description = root.attrib.get('description', None)
        self.sinceVersion = int(root.attrib.get('sinceVersion', '0'))
        self.deprecated = cast(root.attrib.get('deprecated', None), int)
        self.offset = cast(root.attrib.get('offset', None), int)
        self.choices = self.loadChoices(root)

        encodingTypeStr = root.attrib.get('encodingType')
        if encodingTypeStr in [ 'uint8', 'uint16', 'uint32', 'uint64' ]:
            self.encodingType = PrimitiveType.get(encodingTypeStr)
        else:
            node = getDocumentRoot(root).find(f'.//types/type[@name="{encodingTypeStr}"]')
            if node is None:
                raise Exception(f'type {encodingTypeStr} not found (enum: "{self.name}")')
            type = Type(node)
            if type.length != 1:
                raise Exception(f'illegal encodingType "{encodingTypeStr}" (enum: "{self.name}")')
            self.encodingType = type.primitiveType

    def __str__(self) -> str:
        return f'Set(name="{self.name}", encodingType={self.encodingType.name}, encodedLength={self.encodedLength})'

    @property
    def encodedLength(self) -> int:
        return self.encodingType.size

    @staticmethod
    def loadChoices(root: ElementTree.Element) -> list:
        result = []
        for node in root.findall('./choice'):
            result.append({
                'name': node.attrib.get('name'),
                'description': node.attrib.get('description', None),
                'sinceVersion': int(node.attrib.get('sinceVersion', '0')),
                'deprecated': cast(node.attrib.get('deprecated', None), int),
                'value': int(node.text.strip())
            })
        return result

class Message:
    def __init__(self, root: ElementTree.Element) -> None:
        self.name = root.attrib.get('name')
        self.id = int(root.attrib.get('id'))
        self.description = root.attrib.get('description', None)
        self.blockLength = cast(root.attrib.get('blockLength', None), int)
        self.semanticType = root.attrib.get('semanticType', None)
        self.sinceVersion = int(root.attrib.get('sinceVersion', '0'))
        self.deprecated = cast(root.attrib.get('deprecated', None), int)
        self.elements = self.loadElements(root)

    def __str__(self) -> str:
        return f'Message(name="{self.name}", id="{self.id}", elements={len(self.elements)})'

    @staticmethod
    def loadElements(root: ElementTree.Element) -> list:
        result = []
        groupEncountered = False
        for node in root:
            if node.tag == 'field':
                if groupEncountered:
                    raise Exception('field node specified after group node')
                result.append(Field(node))
            elif node.tag == 'group':
                result.append(Group(node))
                groupEncountered = True

        uniqueNames = { element.name for element in result }
        if len(uniqueNames) != len(result):
            raise Exception('duplicate elements name found (message: "{self.name}")')

        uniqueIds = { element.id for element in result }
        if len(uniqueIds) != len(result):
            raise Exception('duplicate elements id found (message: "{self.name}")')

        return result

class Field:
    def __init__(self, root: ElementTree.Element) -> None:
        self.name = root.attrib.get('name')
        self.id = int(root.attrib.get('id'))
        self.description = root.attrib.get('description', None)
        self.type = root.attrib.get('type')
        self.offset = cast(root.attrib.get('offset', None), int)
        self.presence = Presence(root.attrib.get('presence', 'required'))
        self.valueRef = root.attrib.get('valueRef', None)
        self.sinceVersion = int(root.attrib.get('sinceVersion', '0'))
        self.deprecated = cast(root.attrib.get('deprecated', None), int)

    def __str__(self) -> str:
        return f'Field(name="{self.name}", id={self.id}, type={self.type})'

class Group:
    def __init__(self, root: ElementTree.Element) -> None:
        self.name = root.attrib.get('name')
        self.id = int(root.attrib.get('id'))
        self.description = root.attrib.get('description', None)
        self.dimensionType = root.attrib.get('dimensionType', 'groupSizeEncoding')
        self.elements = self.loadElements(root)

    def __str__(self) -> str:
        return f'Group(name="{self.name}", id={self.id})'

    @staticmethod
    def loadElements(root: ElementTree.Element) -> list:
        result = []
        groupEncountered = False
        for node in root:
            if node.tag == 'field':
                if groupEncountered:
                    raise Exception('field node specified after group node')
                result.append(Field(node))
            elif node.tag == 'group':
                result.append(Group(node))
                groupEncountered = True

        uniqueNames = { element.name for element in result }
        if len(uniqueNames) != len(result):
            raise Exception('duplicate elements name found (group: "{self.name}")')

        uniqueIds = { element.id for element in result }
        if len(uniqueIds) != len(result):
            raise Exception('duplicate elements id found (group: "{self.name}")')

        return result

class Schema:
    def __init__(self, root: ElementTree.Element) -> None:
        # inject reference to root for each element in doc
        injectRootAttr(root, root)

        self.types = self.loadTypes(root)
        self.messages = self.loadMessages(root)

    @staticmethod
    def loadFromFile(path: str) -> Schema:
        root = openXMLAndStripNs(path)
        return Schema(root)

    @staticmethod
    def loadTypes(root: ElementTree.Element) -> dict:
        result = {}

        def insert(entry):
            if entry.name in result:
                raise Exception(f'type {entry.name} already exists')
            result[entry.name] = entry


        for node in root.findall('./types/type'):
            entry = Type(node)
            print(entry)
            insert(entry)

        for node in root.findall('./types/composite'):
            entry = Composite(node)
            print(entry)
            insert(entry)

        for node in root.findall('./types/enum'):
            entry = Enum(node)
            print(entry)
            insert(entry)

        for node in root.findall('./types/set'):
            entry = Set(node)
            print(entry)
            insert(entry)

        return result

    @staticmethod
    def loadMessages(root: ElementTree.Element) -> list:
        result = {}

        def insert(entry):
            if entry.name in result:
                raise Exception(f'message {entry.name} already exists')
            result[entry.name] = entry

        for node in root.findall('./message'):
            entry = Message(node)
            print(entry)
            insert(entry)

        return [*result.values()]
