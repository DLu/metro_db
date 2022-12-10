import pathlib
import yaml

from .sqlite_db import SQLiteDB


class MetroDB(SQLiteDB):
    """SQLiteDB that uses a yaml file to specify the database structure"""

    def __init__(self, key, folder=pathlib.Path('.'), extension='db', enums_to_register=[]):
        """Constructor

        Args:
            key (str): Name of the database. Used in constructing the filename
            folder (pathlib.Path): Folder for the database file, and maybe the yaml
            extension (str): The filename suffix for the database file
            enums_to_register (list): A list of enums to register
        """
        SQLiteDB.__init__(self, folder / f'{key}.{extension}')
        self.folder = folder
        self.key = key

        for custom_enum_class in enums_to_register:
            self.register_custom_enum(custom_enum_class)

    def load_yaml(self, structure_filepath=None, structure_key=None):
        """Manually load the yaml file.

        By default, if the database file is path/name.db, the yaml file is path/name.yaml

        However, you can also specify the full path with structure_filepath or change the name
        by specifying structure_key (so that the yaml will instead be path/structure_key.yaml)

        Args:
            structure_filepath (pathlib.Path): Optional full path to the yaml file
            structure_key (str): Optional stem for the yaml file
        """
        if structure_filepath is None:
            if structure_key is None:
                structure_key = self.key

            structure_filepath = self.folder / f'{structure_key}.yaml'
        elif structure_key:
            raise RuntimeError('Cannot specify structure_filepath AND structure_key')

        db_structure = yaml.safe_load(open(structure_filepath))
        self.tables = db_structure['tables']
        self.field_types = db_structure.get('types', db_structure.get('field_types', {}))
        self.default_type = db_structure.get('default_type', self.default_type)
        self.primary_keys = db_structure.get('primary_keys', self.primary_keys)

    def update_database_structure(self):
        """Create or update the structure of all tables.

        Loads the yaml automatically if it has not been done already."""
        if not self.tables:
            self.load_yaml()
        SQLiteDB.update_database_structure(self)

    def __enter__(self):
        self.update_database_structure()
        return self

    def __exit__(self, *args, **kwargs):
        self.close()
