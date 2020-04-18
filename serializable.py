
class LabelFile:
    def __init__(self, source: str, content: str, labels: list):
        self.source = source
        self.content = content
        self.labels = labels

    @staticmethod
    def parse_obj(obj: dict):
        if not isinstance(obj, dict):
            raise Exception(f'{obj} is not a dict!')

        sample = LabelFile('', '', [])
        args = {}

        for key in sample.__dict__:
            if key not in obj:
                raise Exception(f'{obj} does not contain key {repr(key)}!')
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
        records=[],
        invalid_records=[],
        blank_combinations=[],
        unsupported_combinations=[],
    ):
        self.source = source
        self.content = content
        self.labels = labels
        self.records = records  # (id, char, font)
        self.invalid_records = invalid_records  # (id) from records
        self.blank_combinations = blank_combinations  # (char, font)
        self.unsupported_combinations = unsupported_combinations

    @staticmethod
    def parse_obj(obj: dict):
        if not isinstance(obj, dict):
            raise Exception(f'{obj} is not a dict!')

        sample = DatasetMetadata('', '', [])
        args = {}

        for key in sample.__dict__:
            if key not in obj:
                raise Exception(f'{obj} does not contain key {repr(key)}!')
            args[key] = obj[key]

        # now I feel the need of writing some tests
        return DatasetMetadata(**args)
