import pathlib
import yaml

from .sqlite_db import SQLiteDB


class MetroDB(SQLiteDB):
    def __init__(self, key, folder=pathlib.Path('.'), extension='db', enums_to_register=[]):
        SQLiteDB.__init__(self, folder / f'{key}.{extension}')
        self.folder = folder
        self.key = key

        for custom_enum_class in enums_to_register:
            self.register_custom_enum(custom_enum_class)

    def load_yaml(self, structure_filepath=None, structure_key=None):
        if structure_filepath is None:
            if structure_key is None:
                structure_key = self.key

            structure_filepath = self.folder / f'{structure_key}.yaml'
        elif structure_key:
            raise RuntimeError('Cannot specify structure_filepath AND structure_key')

        db_structure = yaml.safe_load(open(structure_filepath))
        self.tables = db_structure['tables']
        self.field_types = db_structure['types']
        self.default_type = db_structure.get('default_type', self.default_type)

    def update_database_structure(self):
        if not self.tables:
            self.load_yaml()
        SQLiteDB.update_database_structure(self)

    def __enter__(self):
        self.update_database_structure()
        return self

    def __exit__(self, *args, **kwargs):
        self.close()
