"""FS-Online Buildout Tasks.

These tasks are to be executed with https://www.pyinvoke.org/ in Python 3.6+
and are related to the maintenance of this project.
"""
import os
from glob import glob
from pathlib import Path
import shutil
from invoke import task
from invoke.util import yaml
from functools import wraps
import time

# We don't know yet, if we're in an instance or core repo,
# so try importing from the other, if the first fails
try:
    from .fsonline_environment import FsonlineEnvironment
except:
    from fsonline_environment import FsonlineEnvironment

FSO_ENV = FsonlineEnvironment()

# Configure Logging
# -----------------
import logging

logger = logging.getLogger("fsonline")
log_handler = logging.StreamHandler()
log_formatter = logging.Formatter("%(name)s %(levelname)s: %(message)s")
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)

LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
_log_level = os.environ.get("LOG_LEVEL", "")
if _log_level.isdigit():
    _log_level = int(_log_level)
elif _log_level in LOG_LEVELS:
    _log_level = getattr(logging, _log_level)
else:
    if _log_level:
        logger.warning("Wrong value in $LOG_LEVEL, falling back to INFO")
    _log_level = logging.INFO
logger.setLevel(_log_level)


# Exceptions
# ----------
class AddonsConfigError(Exception):
    def __init__(self, message, *args):
        super(AddonsConfigError, self).__init__(message, *args)
        self.message = message


class OdooSourceError(Exception):
    def __init__(self, message, *args):
        super(OdooSourceError, self).__init__(message, *args)
        self.message = message


# Helper
# ------
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


def validate_odoo_build_file_paths(odoo_build_file):
    """ Validate the paths in the odoo build file

        - ensure all paths are relative
        - ensure no paths point to "/"
    """
    # TODO: Upgrade this with pathlib commands ;)
    odoo_build_yml = yaml.safe_load(odoo_build_file.read_text())
    odoo_cfg = odoo_build_yml["odoo"]

    odoo_cfg_keys_to_check = ("odoo_src", "odoo_tgt", "addons_src", "addons_tgt")

    paths_to_check = []
    for key in odoo_cfg_keys_to_check:
        val = odoo_cfg[key]
        if isinstance(val, str):
            paths_to_check.append(val)
        elif isinstance(val, list):
            paths_to_check += val
        else:
            raise TypeError(u"val must be of type string or list! {}".format(val))

    for path in paths_to_check:
        assert not path.startswith('/'), "Config path is not relative {}".format(path)
        assert len(path) >= 3, "Config path is too short {}".format(path)

    assert any(p.startswith('build/') for p in (odoo_cfg["odoo_tgt"], odoo_cfg["addons_tgt"])), (
        u"The build targets must start with 'build/' !")

    return True


def find_addons(search_paths, manifest="__manifest__.py"):
    """ Returns a set of addon paths

    :param list of Path search_paths:
        List or set of paths to addons or to folders with multiple addons.
        Globbing is supported: To add all addons at the first level in a path use "/path/to/folder/with/addons/*"
        Note: Addons are only searched at the first level of the found paths.

    :param str manifest:
        Name of the manifest files to identify an odoo-addon-folder

    :return: dict[str, Path]:
        Dict with addon name as key and the absolute addon path as value
    """
    assert isinstance(search_paths, (list, set)), u"search_paths must be of type list or set"
    search_paths = set(search_paths)

    addons = dict()

    for search_path in search_paths:
        addon_paths = [Path(p) for p in glob(str(search_path))]
        if not addon_paths:
            raise AddonsConfigError(u"Could not find any addons or paths in addon-search-path '{}'".format(search_path))
        for addon_path in addon_paths:
            if not addon_path.is_dir():
                continue
            manifest_location = addon_path / manifest
            if manifest_location.is_file():
                addon_name = addon_path.name
                if addon_name in addons:
                    raise AddonsConfigError(
                        u"Addon {} found twice at '{}' and '{}'".format(addon_name, addon_path, addons[addon_name])
                    )
                addons[addon_name] = addon_path

    return addons


def symlink_files_relative(src_folder, tgt_folder):
    """ Symlink all files from the source folder to the target folder with relative paths.

    :param Path src_folder:
    :param Path tgt_folder:
    :return:
    """
    for source in src_folder.iterdir():
        if source.is_file():
            target = tgt_folder / source.name
            relative_source = Path(os.path.relpath(source, start=target.parent))
            target.symlink_to(relative_source)


# Global Variables
# ----------------
# https://realpython.com/python-pathlib/

TASK_ROOT = FSO_ENV.core_path.absolute()
PROJECT_ROOT = TASK_ROOT

if FSO_ENV.is_instance:
    PROJECT_ROOT = FSO_ENV.instance_path.absolute()

BUILD_FILE = TASK_ROOT / "build" / "build.yml"
validate_odoo_build_file_paths(BUILD_FILE)

CFG = yaml.safe_load(BUILD_FILE.read_text())
CFG_ODOO = CFG["odoo"]

ODOO_SRC = TASK_ROOT / CFG_ODOO["odoo_src"]
ODOO_TGT = TASK_ROOT / CFG_ODOO["odoo_tgt"]
ADDONS_TGT = TASK_ROOT / CFG_ODOO["addons_tgt"]


# Tasks
# -----
@task
def build_odoo(c, copy_files=False):
    """ Build the odoo source files

    This will copy the odoo and addons source files from the submodules to the build folder
    """
    # Check that the odoo src path exists
    if not ODOO_SRC.is_dir():
        raise OdooSourceError(u"Odoo source not found at {}".format(ODOO_SRC))

    # odoo and odoo-addons locations
    odoo_odoo_src = ODOO_SRC / 'odoo'
    odoo_odoo_addons_src = ODOO_SRC / "odoo" / "addons"
    odoo_addons_src = ODOO_SRC / "addons"

    # addon search paths
    odoo_odoo_addons_search_path = [odoo_odoo_addons_src / "*"]
    odoo_addons_search_path = [odoo_addons_src / "*"]
    extra_addons_search_paths = [TASK_ROOT / p for p in CFG_ODOO["addons_src"]]

    # Clear the build locations
    build_paths = (ODOO_TGT, ADDONS_TGT)
    for build_path in build_paths:
        build_path_root = TASK_ROOT / "build"
        assert build_path_root in build_path.parents, "Build path {} must be in {}".format(build_path, build_path_root)
        if os.path.isdir(build_path):
            shutil.rmtree(build_path)

    # Copy files and folders
    if copy_files:
        shutil.copytree(odoo_odoo_src, ODOO_TGT, symlinks=True)
        addon_folders = find_addons(odoo_addons_search_path + extra_addons_search_paths)
        for addon, addon_src_path in addon_folders.items():
            addon_tgt_path = ADDONS_TGT / addon
            shutil.copytree(addon_src_path, addon_tgt_path, symlinks=True)

    # Symlink files and folder
    else:
        ODOO_TGT.mkdir()
        ADDONS_TGT.mkdir()
        symlink_files_relative(odoo_odoo_src, ODOO_TGT)
        symlink_files_relative(odoo_odoo_addons_src, ADDONS_TGT)
        for source in odoo_odoo_src.iterdir():
            if source.is_dir() and source.name != 'addons':
                target = ODOO_TGT / source.name
                rel_src = Path(os.path.relpath(source, start=target.parent))
                target.symlink_to(rel_src)
        addon_folders = find_addons(odoo_odoo_addons_search_path + odoo_addons_search_path + extra_addons_search_paths)
        for addon_name, addon_src_path in addon_folders.items():
            addon_target = ADDONS_TGT / addon_name
            relative_source = Path(os.path.relpath(addon_src_path, start=addon_target.parent))
            addon_target.symlink_to(relative_source)

def print_bullet(s):
    print("  * %s" % s)

def print_command(s):
    print("      RUN: %s" % s)

def print_create_addon_help():
    print("""
Usage: invoke create-addon <parameters>

  --name <name>     The directory name of the addonn
  --core            Create a core addon instead of an instance addon
  --minimal         Create a minimalist addon.

Testing:

  --preview         Do a dry run for testing.
""")

@task
def create_addon(c, name=None, preview=False, core=False, minimal=False):
    """ Create a new Odoo 14 addon """

    if not name:
        print_create_addon_help()
        return

    source = (FSO_ENV.tools_path /
             "copier-templates" /
             "odoo_module").absolute()
    destination = (FSO_ENV.core_path /
                  "src" /
                  "addons" /
                  name).absolute()

    # Force core addon, if we're not in an instance repo
    if not FSO_ENV.is_instance:
        print("You are not in an instance repository, creating a core module.")
        core = True

    if not core:
        destination = (FSO_ENV.instance_path /
                      "addons" /
                      name).absolute()

    print("Creating new %s addon \"%s\"..." % (FSO_ENV.name, name))

    args = ""

    if minimal:
        args = args + \
            " -d models=False" + \
            " -d models=False" + \
            " -d views=False" + \
            " -d security=False" + \
            " -d data=False" + \
            " -d i18n=False" + \
            " -d controllers=False" + \
            " -d static=False" + \
            " -d demo=False" + \
            " -d unittest=False"

    print_bullet("Copier: %s --> %s" % (source, destination))

    if preview:
        print_command("copier %s %s %s" % (source, destination, args))
    else:
        c.run("copier %s %s %s" % (source, destination, args))
