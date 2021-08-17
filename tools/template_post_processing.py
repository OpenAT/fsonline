import re
import sys
import logging
from pathlib import Path
from typing import List, Pattern, AnyStr

logging.basicConfig(
    format="%(name)s %(levelname)s: %(message)s",
    level=logging.INFO)

_logger = logging.getLogger(__name__)


class CopierPostProcessing:
    PYTHON_IGNORE_FILES = [
        "__init__.py",
        "manifest.py"
    ]

    def __init__(self, addon_path: Path) -> None:
        self.addon_path = addon_path

    @staticmethod
    def get_files(target_path: Path, dot_ext: str = "", ignore_files: List[str] = ()) -> List[Path]:
        """ Gets a list of PosixPath for the files in a given path. Matches an optional
        extension and ignores specified files. """

        pattern = f"{ Path('**') / f'*{dot_ext}'}"
        return [
            file.parent / file.name for file in target_path.glob(pattern)
            if file.name.lower() not in ignore_files or []
        ]

    @staticmethod
    def ensure_file_has_lines(filename: Path, lines_to_add: List[str]) -> None:
        """ Ensures the specified file contains all of the specified
        lines. If the file does not exist, it will be created. """

        if not filename.exists():
            filename.touch()

        with open(filename, "r+") as file:
            for line in file:
                if line in lines_to_add:
                    lines_to_add.remove(line)
                    if not lines_to_add:
                        break
            else:
                # Loop exhausted, add remaining lines
                for missing_line in lines_to_add:
                    file.write(missing_line)

    def get_entries(self, stem_only: bool, addon_sub_dir: str, dot_ext: str = "", ignore: List[str] = ()) -> List[str]:
        """ Scans the specified addon sub dir for its files, and returns
        them in a formatted list. """

        file_entries = self.get_files(
            self.addon_path / addon_sub_dir,
            dot_ext=dot_ext,
            ignore_files=ignore)

        if stem_only:
            return [f"{file.stem}" for file in file_entries]
        else:
            return [f"{file.relative_to(file.parent.parent)}" for file in file_entries]

    def process(self) -> None:
        """ Reads the addon structure and adjusts init and manifest files. """

        _logger.info(f"Checking addon: {self.addon_path.absolute()}")

        model_entries = self.get_entries(True, "models", ".py", CopierPostProcessing.PYTHON_IGNORE_FILES)
        view_entries = self.get_entries(False, "views", ".xml")
        security_entries = self.get_entries(False, "security", ".csv")

        self.modify_init_files(model_entries)
        self.modify_manifest(
            view_entries +
            security_entries)

    def modify_init_files(self, models: List[str]) -> None:
        """ Alters addon and modules init files to include models.
        if the models init file does not exist, it will be created. """

        _logger.info(f"Attempting to modify init files for models: {str(models)}")
        addon_init = Path(self.addon_path) / "__init__.py"
        models_init = Path(self.addon_path) / "models" / "__init__.py"

        self.ensure_file_has_lines(models_init, [f"import {model}\n" for model in models])
        self.ensure_file_has_lines(addon_init, ["import models\n"])

    @staticmethod
    def create_expression(tag: str) -> Pattern[AnyStr]:
        """ Creates a RegEx that matches 'tag': [ ... ] """

        return re.compile(fr"(\"{tag}\"|'{tag}')\s*:\s\[\s*(.|\n)*\s*]",
                          re.RegexFlag.I or re.RegexFlag.M)

    def modify_manifest(self, data_files: List[str]) -> None:
        """ Alters the addon manifest to include the specified resources. """

        _logger.info(f"Attempting to modify manifest for data files: {str(data_files)}")
        manifest_file = Path(self.addon_path) / "manifest.py"

        data_files.sort()
        new_data = "'data': [\n\t\t" + \
                   ",\n\t\t".join([f"'{df}'" for df in data_files]) + \
                   "\n\t]"
        new_data = new_data.replace("\t", "    ")

        with open(manifest_file, "r+") as file:
            manifest_content = file.read()
            data_exp = self.create_expression("data")
            manifest_content = data_exp.sub(new_data, manifest_content)
            file.truncate(0)
            file.seek(0)
            file.write(manifest_content)
