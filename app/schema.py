from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Union, Optional

class Presence(Enum):
    REQUIRED = 'required'
    OPTIONAL = 'optional'
    CONSTANT = 'constant'

@dataclass
class PrimitiveType:
    name: str
    size: int
    value_min: str
    value_max: str
    value_null: str

AnyType = Union[PrimitiveType]

class SchemaBase(object):
    def __init__(self) -> None:
        self.types = [
            PrimitiveType(name='char', size=1, value_min='CHAR_VALUE_MIN', value_max='CHAR_VALUE_MAX',
                          value_null='CHAR_VALUE_NULL'),
            PrimitiveType(name='int8', size=1, value_min='INT8_VALUE_MIN', value_max='INT8_VALUE_MAX',
                          value_null='INT8_VALUE_NULL'),
            PrimitiveType(name='int16', size=2, value_min='INT16_VALUE_MIN', value_max='INT16_VALUE_MAX',
                          value_null='INT16_VALUE_NULL'),
            PrimitiveType(name='int32', size=4, value_min='INT32_VALUE_MIN', value_max='INT32_VALUE_MAX',
                          value_null='INT32_VALUE_NULL'),
            PrimitiveType(name='int64', size=8, value_min='INT64_VALUE_MIN', value_max='INT64_VALUE_MAX',
                          value_null='INT64_VALUE_NULL'),
            PrimitiveType(name='uint8', size=1, value_min='UINT8_VALUE_MIN', value_max='UINT8_VALUE_MAX',
                          value_null='UINT8_VALUE_NULL'),
            PrimitiveType(name='uint16', size=2, value_min='UINT16_VALUE_MIN', value_max='UINT16_VALUE_MAX',
                          value_null='UINT16_VALUE_NULL'),
            PrimitiveType(name='uint32', size=4, value_min='UINT32_VALUE_MIN', value_max='UINT32_VALUE_MAX',
                          value_null='UINT32_VALUE_NULL'),
            PrimitiveType(name='uint64', size=8, value_min='UINT64_VALUE_MIN', value_max='UINT64_VALUE_MAX',
                          value_null='UINT64_VALUE_NULL'),
            PrimitiveType(name='float', size=4, value_min='FLOAT_VALUE_MIN', value_max='FLOAT_VALUE_MAX',
                          value_null='FLOAT_VALUE_NULL'),
            PrimitiveType(name='double', size=8, value_min='DOUBLE_VALUE_MIN', value_max='DOUBLE_VALUE_MAX',
                          value_null='DOUBLE_VALUE_NULL')
        ]

    def find_type(self, name: str) -> Optional[AnyType]:
        for type in self.types:
            if type.name == name:
                return type
        return None

    def get_type(self, name: str) -> AnyType:
        type = self.find_type(name)
        if type is None:
            raise Exception('type "{name}" not found')
        return type

    def add_type(self, type: AnyType) -> None:
        if self.find_type(type.name) is not None:
            raise Exception('type "{type.name}" already exists')
        self.types.append(type)


class Schema(SchemaBase):
    def __init__(self, root) -> None:
        super().__init__()
        self._root = root
