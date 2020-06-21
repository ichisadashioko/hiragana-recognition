import os
import io
import json
from typing import List, Dict


def universal_dump(obj, fp):
    # use tab to reduce file size
    json.dump(obj, fp, ensure_ascii=False, indent='\t')


class LabelFile:
    def __init__(self, source: str, content: str, labels: list):
        self.source = source
        self.content = content
        self.labels = labels

    def __repr__(self):
        return repr(self.__dict__)

    @staticmethod
    def parse_obj(obj: dict):
        if not isinstance(obj, dict):
            raise Exception(f'{obj} is not a dict!')

        sample = LabelFile('', '', [])
        args = {}

        for key in sample.__dict__:
            if key not in obj:
                obj_str = repr(obj)
                if len(obj_str) > 80:
                    obj_str = obj_str[:40] + '...' + obj_str[-40:]

                raise Exception(f'{obj_str} does not contain key {repr(key)}!')

            args[key] = obj[key]

        return LabelFile(**args)


class DatasetMetadata:
    """
    Serializable class for storing the dataset metadata.

    ...

    Attributes
    ----------
    source : str
        the file's name that was used to generate the labels
    content : str
        the file's content for ability to reproduce the labels
    labels : list
        the list of chars from the file (whitespace removed)
    records : list
        the list of dataset records stored in TFRecord with the same
        order without image data. The record is a dict with format:
        {'hash': '<32-md5>', 'char': 'あ', font: 'HGKyokashotai_Medium'}
    invalid_records : list
        list of record's hash marked as invalid after inspection
    blank_combinations : list
        list of {'char': ?, 'font': ?} that produces blank image during
        rendering. Maybe be requested to render for inspection
    unsupported_combinations : list
        list of {'char': ?, 'font': ?} that is reported that 'char' is
        not supported in 'font'
    """

    def __init__(
        self,
        source: str,
        content: str,
        labels: list,
        records: List[Dict[str, str]] = [],
        invalid_records: List[str] = [],
        blank_combinations: List[Dict[str, str]] = [],
        unsupported_combinations: List[Dict[str, str]] = [],
        invalid_fonts: List[str] = [],
        completed_labels: List[str] = [],
    ):
        self.source = source
        self.content = content
        self.labels = labels
        self.records = records  # (id, char, font)
        self.invalid_records = invalid_records  # (id) from records
        self.blank_combinations = blank_combinations  # (char, font)
        self.unsupported_combinations = unsupported_combinations
        self.invalid_fonts = invalid_fonts
        self.completed_labels = completed_labels

    @staticmethod
    def parse_obj(obj: dict):
        if not isinstance(obj, dict):
            raise Exception(f'{obj} is not a dict!')

        sample = DatasetMetadata(
            source='',
            content='',
            labels=[],
        )

        required_keys = set(['source', 'content', 'labels', 'records'])
        all_keys = set(sample.__dict__.keys())
        optional_keys = all_keys - required_keys

        args = {}

        for key in required_keys:
            if key not in obj:
                obj_str = repr(obj)
                if len(obj_str) > 80:
                    obj_str = obj_str[:40] + '...' + obj_str[-40:]

                raise Exception(f'{obj_str} does not contain key {repr(key)}!')

            args[key] = obj[key]

        for key in optional_keys:
            if key in obj:
                args[key] = obj[key]

        return DatasetMetadata(**args)


# New data serialization format (because other formats are terrible)
# JSON - cannot be appended on the fly
# YAML - specification is too large
# TFRecord/protobuf - I cannot find where is the specification. They
# just tell me how great the technology is and there are only samples on
# using TFRecord with TensorFlow and it is terribly slow. I want to be
# able to use pure Python without TensorFlow. In addition, the whole
# TensorFlow graph thing makes it imposible to debug. I think they
# JIT compile my code for using with CUDA or native DLLs.
# I'm not gonna live with those specification limitations!

# It's not going to be human readable because we need to store binary
# data.

# - Format: data length in bytes and followed by the data
# - There will be only list and records will be stacked one after other
# - To present a dictionary: Write the key and then the value, key and
# value are treated as 2 records in list. It's user's job to most of
# the parsing and converting to required data type.
# - If the data length is 0 but there is still data left then they are
# treated as metadata. You will need to ship your parsing and converting
# code for the blob.

# number of bytes to store the record length is 4 bytes (32 bits)
class XFormat:
    INT_SIZE = 4
    BYTE_ORDER = 'little'
    EXTENSION = '.xformat'
    ENCODING = 'utf-8'

    DATA_TYPE_BYTES = 0
    DATA_TYPE_INT = 1
    DATA_TYPE_UTF8_STRING = 2
    DATA_TYPE_LIST = 3
    DATA_TYPE_DICT = 4

    @classmethod
    def serialize_string(cls, s: str) -> bytes:
        record_data = s.encode(encoding=cls.ENCODING)
        return record_data

    @classmethod
    def deserialize_string(cls, bs: bytes) -> str:
        return bs.decode(encoding=cls.ENCODING)

    @classmethod
    def serialize_int(cls, n: int) -> bytes:
        record_data = n.to_bytes(
            length=cls.INT_SIZE,
            byteorder=cls.BYTE_ORDER,
            signed=True,
        )

        return record_data

    @classmethod
    def deserialize_int(cls, bs: bytes) -> int:
        return int.from_bytes(bs, byteorder=cls.BYTE_ORDER, signed=True)

    @classmethod
    def serialize_obj(cls, obj) -> (bytes, bytes):
        obj_type = type(obj)
        if obj_type == int:
            return bytes([cls.DATA_TYPE_INT]), cls.serialize_int(obj)
        elif obj_type == str:
            return bytes([cls.DATA_TYPE_UTF8_STRING]), cls.serialize_string(obj)
        elif obj_type == bytes:
            return bytes([cls.DATA_TYPE_BYTES]), obj
        elif obj_type == list:
            buffer = io.BytesIO()

            for value in obj:
                datatype, encoded_value = cls.serialize_obj(value)
                buffer.write(datatype)
                buffer.write(cls.serialize_int(len(encoded_value)))
                buffer.write(encoded_value)

            return bytes([cls.DATA_TYPE_LIST]), buffer.getvalue()
        elif obj_type == dict:
            buffer = io.BytesIO()

            for key in obj:
                datatype, encoded_key = cls.serialize_obj(key)
                buffer.write(datatype)
                buffer.write(cls.serialize_int(len(encoded_key)))
                buffer.write(encoded_key)

                datatype, encoded_value = cls.serialize_obj(obj[key])
                buffer.write(datatype)
                buffer.write(cls.serialize_int(len(encoded_value)))
                buffer.write(encoded_value)

            return bytes([cls.DATA_TYPE_DICT]), buffer.getvalue()
        else:
            raise Exception(f'Unsupported type {obj_type}!')
            return 0

    @classmethod
    def deserialze_obj(cls, bs: bytes, datatype: int):
        if datatype == cls.DATA_TYPE_BYTES:
            return bs
        elif datatype == cls.DATA_TYPE_INT:
            return cls.deserialize_int(bs)
        elif datatype == cls.DATA_TYPE_UTF8_STRING:
            return cls.deserialize_string(bs)
        elif datatype == cls.DATA_TYPE_LIST:
            retval = []
            buffer = io.BytesIO(bs)
            pos = 0
            bs_len = len(bs)

            while pos < bs_len:
                value_datatype = bs[pos]
                pos += 1

                if(pos + cls.INT_SIZE) > bs_len:
                    raise Exception(f'Broken serialized data!')
                value_byte_count = cls.deserialize_int(bs[pos:pos+cls.INT_SIZE])  # noqa
                pos += cls.INT_SIZE

                if(pos + value_byte_count) > bs_len:
                    raise Exception(f'Broken serialized data!')
                value = cls.deserialze_obj(bs[pos:pos+value_byte_count], value_datatype)  # noqa
                retval.append(value)
                pos += value_byte_count

            return retval
        elif datatype == cls.DATA_TYPE_DICT:
            retval = {}
            buffer = io.BytesIO(bs)
            pos = 0
            bs_len = len(bs)

            while pos < bs_len:
                key_datatype = bs[pos]
                pos += 1

                if (pos + cls.INT_SIZE) > bs_len:
                    raise Exception(f'Broken serialized data!')
                key_byte_count = cls.deserialize_int(bs[pos:pos+cls.INT_SIZE])
                pos += cls.INT_SIZE

                if(pos + key_byte_count) > bs_len:
                    raise Exception(f'Broken serialized data!')
                key = cls.deserialze_obj(bs[pos:pos+key_byte_count], key_datatype)  # noqa
                pos += key_byte_count

                value_datatype = bs[pos]
                pos += 1

                if(pos + cls.INT_SIZE) > bs_len:
                    raise Exception(f'Broken serialized data!')
                value_byte_count = cls.deserialize_int(bs[pos:pos+cls.INT_SIZE])  # noqa
                pos += cls.INT_SIZE

                if(pos + value_byte_count) > bs_len:
                    raise Exception(f'Broken serialized data!')
                value = cls.deserialze_obj(bs[pos:pos+value_byte_count], value_datatype)  # noqa
                pos += value_byte_count

                retval[key] = value

            return retval
        else:
            raise Exception(f'Unsupported data type {datatype}!')
