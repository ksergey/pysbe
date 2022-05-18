from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Union

class Presence(Enum):
    REQUIRED = 'required'
    OPTIONAL = 'optional'
    CONSTANT = 'constant'

class ByteOrder(Enum):
    LITTLE_ENDIAN = 'littleEndian'
    BIG_ENDIAN = 'bitEndian'

@dataclass
class Type:
    name: str
    primitive_type: str
    description: Optional[str] = None
    presence: Presence = Presence.REQUIRED
    null_value: Optional[str] = None
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    length: int = 1
    offset: Optional[int] = None
    semantic_type: Optional[str] = None
    since_version: int = 0
    deprecated: Optional[int] = None
    value: Optional[str] = None

@dataclass
class Composite:
    name: str
    description: Optional[str] = None
    offset: Optional[int] = None
    semantic_type: Optional[str] = None
    since_version: int = 0
    deprecated: Optional[int] = None
    elements: List[Union[Type, Composite, Ref, Enum, Set]] = field(default_factory=list)

@dataclass
class Ref:
    name: str
    type: str
    offset: Optional[int] = None
    since_version: int = 0
    deprecated: Optional[int] = None

@dataclass
class Enum:
    name: str
    encoding_type: str
    description: Optional[str] = None
    offset: Optional[int] = None
    since_version: int = 0
    deprecated: Optional[int] = None
    elements: List[ValidValue] = field(default_factory=list)

@dataclass
class ValidValue:
    name: str
    value: str
    description: Optional[str] = None
    since_version: int = 0
    deprecated: Optional[int] = None

@dataclass
class Set:
    name: str
    encoding_type: str
    description: Optional[str] = None
    offset: Optional[int] = None
    since_version: int = 0
    deprecated: Optional[int] = None
    elements: List[Choice] = field(default_factory=list)

@dataclass
class Choice:
    name: str
    value: str
    description: Optional[str] = None
    since_version: int = 0
    deprecated: Optional[int] = None

@dataclass
class Field:
    name: str
    id: int
    type: str
    description: Optional[str] = None
    offset: Optional[int] = 0
    presence: Presence = Presence.REQUIRED
    value_ref: Optional[str] = None
    since_version: int = 0
    deprecated: Optional[int] = None

@dataclass
class Group:
    name: str
    id: int
    description: Optional[str] = None
    dimension_type: str = 'groupSizeEncoding'
    elements: List[Union[Field, Group, Data]] = field(default_factory=list)

@dataclass
class Data:
    name: str
    id: int
    type: str
    semantic_type: Optional[str] = None
    since_version: int = 0
    deprecated: Optional[int] = None

@dataclass
class Message:
    name: str
    id: int
    description: Optional[str] = None
    block_length: Optional[int] = None
    semantic_type: Optional[str] = None
    since_version: int = 0
    deprecated: Optional[int] = None
    elements: List[Union[Field, Group, Data]] = field(default_factory=list)

@dataclass
class Schema:
    package: str
    id: int
    version: int
    semantic_version: Optional[str] = None
    byte_order: ByteOrder = ByteOrder.LITTLE_ENDIAN
    description: Optional[str] = None
    header_type: str = 'messageHeader'
    types: List[Union[Type, Composite, Enum, Set]] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
