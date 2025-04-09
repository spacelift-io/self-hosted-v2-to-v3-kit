from abc import ABC

from converters.migration_context import MigrationContext


class Terraformer(ABC):
    def __init__(self, file_path: str, migration_context: MigrationContext):
        self.file_path = file_path
        self.migration_context = migration_context

    def process(self, resource_name: str, to: str):
        with open(self.file_path, "a") as f:
            f.write("import {\n")
            f.write(f"  to = {resource_name}\n")
            f.write(f'  id = "{to}"\n')
            f.write("}\n\n")
