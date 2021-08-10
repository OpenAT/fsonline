import io
from glob import glob
from pathlib import Path
from typing import Literal, List, Dict, Optional
from pydantic import DirectoryPath
from collections import OrderedDict
from functools import wraps
import time
import os
from .globals import ALLOWED_ENVIRONMENTS
import logging

logger = logging.getLogger(__name__)


def merge_env_files(target_env: Optional[ALLOWED_ENVIRONMENTS], env_files: List[Path]) -> io.StringIO:
    merged_files = io.StringIO()

    file_list = []
    for file in env_files:
        if not isinstance(file, Path):
            continue
        file_list.append(file)
        file_list.append(file.with_name(file.name + '.local'))
        if target_env:
            file_list.append(file.with_name(file.name + '.' + target_env.lower()))
            file_list.append(file.with_name(file.name + '.' + target_env.lower() + '.local'))

    for f in file_list:
        if not f.is_file():
            continue
        merged_files.write(f.read_text())

    merged_files.seek(0)
    return merged_files


def find_addons(search_paths: List[Path], start_dir: Path = None, manifest="__manifest__.py") -> List[DirectoryPath]:
    """ Returns a set of addon paths

    :param start_dir:
    :param list of Path search_paths:
        List or set of paths to addons or to folders with multiple addons.
        Globbing is supported: To add all addons at the first level in a path use "/path/to/folder/with/addons/*"
        Note: Addons are only searched at the first level of the found paths.

    :param str manifest:
        Name of the manifest files to identify an odoo-addon-folder

    :return: dict[str, Path]:
        Dict with addon name as key and the absolute addon path as value
    """
    assert search_paths, "No search_paths given!"

    # Absolute search_paths
    if start_dir:
        assert start_dir.is_absolute(), "start_dir must be absolute"
        assert start_dir.is_dir(), "start_dir must be an existing directory"
        absolute_search_paths: List[Path] = [(p if p.is_absolute() else start_dir / p) for p in search_paths]
    else:
        assert all(p.is_absolute for p in search_paths), "All search paths must be absolute if no start_dir is set!"
        absolute_search_paths = search_paths

    # Resolve any wildcards (globbing) in the absolute_search_paths to its individual files
    addon_dirs: List[Path] = []
    for abs_s_path in absolute_search_paths:
        for f in glob(str(abs_s_path)):
            f = Path(f)
            if f.is_dir():
                addon_dirs.append(f)

    # Search all the found files for directories containing the manifest file
    addons: OrderedDict[str, DirectoryPath] = OrderedDict()
    for addon_dir in addon_dirs:
        if (addon_dir / manifest).is_file():
            addon_name = addon_dir.name
            if addon_name in addons:
                assert addons[addon_name] == addon_dir, (
                    f"Addon '{addon_name}' set twice at different locations: '{addon_dir}' and '{addons[addon_name]}'")
            addons[addon_name] = addon_dir

    return list(addons.values())


# def symlink_files_relative(src_folder, tgt_folder):
#     """ Symlink all files from the source folder to the target folder with relative paths.
#
#     :param Path src_folder:
#     :param Path tgt_folder:
#     :return:
#     """
#     for source in src_folder.iterdir():
#         if source.is_file():
#             target = tgt_folder / source.name
#             relative_source = Path(os.path.relpath(source, start=target.parent))
#             target.symlink_to(relative_source)


def symlink_rel(source: Path, target: Path, src_relative_to: Path, dry=False):
    if src_relative_to:
        rel_source = Path(os.path.relpath(source, src_relative_to))
    else:
        rel_source = source

    logger.debug(f"Create symlink at '{target}' from '{rel_source}'")
    if not dry:
        target.symlink_to(rel_source)


def log_time(func):
    """This decorator prints the execution time for the decorated function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info("{} ran in {}s".format(func.__name__, round(end - start, 2)))
        return result

    return wrapper
