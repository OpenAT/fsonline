import os
import copy
from pathlib import Path
from invoke import task
from typing import Optional
from tools.globals import ALLOWED_ENVIRONMENTS
from tools.env_settings import FsonlineEnv
from tools.helper import symlink_rel
from tools.tasks.globals_invoke import INVOKE_CONTEXT_TYPE as CTX_TYPE
import logging

logger = logging.getLogger(__name__)

ENV_TYPE = Optional[ALLOWED_ENVIRONMENTS]

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ATTENTION: We can not use type annotation for @task decorated functions because
#            https://github.com/pyinvoke/invoke/pull/373 is not merged yet :(
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


@task
def init_submodules(c, in_path=None):
    """ Initialize all submodules recursively """
    e: FsonlineEnv = c['fsonline_env_settings']
    in_path: Path = in_path or e.repo_dir
    c.run(f"git -C {in_path} submodule update --init --recursive")


@task
def symlink_odoo(c, mode=0o770, clean=True, dry=False):
    """ Symlink odoo and addon sources for development """
    e: FsonlineEnv = c['fsonline_env_settings']

    logger.debug(f"Create dev_dir at '{e.dev_dir}'")
    if not dry:
        e.dev_dir.mkdir(mode=mode, exist_ok=True)

    # TODO
    # logger.info(f"Clean dev_odoo_tgt_dir at '{e.dev_odoo_tgt_dir}'")
    # if not dry and clean:
        # assert e.dev_odoo_tgt_dir in e.repo_dir, f"dev_odoo_tgt_dir {e.dev_odoo_tgt_dir} outside repo_dir {e.repo_dir}"

    logger.debug(f"Create dev_odoo_tgt_dir at '{e.dev_fson_tgt_dir}'")
    if not dry:
        e.dev_fson_tgt_dir.mkdir(mode=mode, exist_ok=True)

    logger.info(f"Symlink from core_odoo_src '{e.core_odoo_src}' to dev_odoo_tgt_dir '{e.dev_fson_tgt_dir}'")

    # Link OCA/OCB/* without OCA/OCB/addons and OCA/OCB/odoo
    fson_tgt_dir = e.dev_fson_tgt_dir
    for f in e.core_odoo_src.iterdir():
        # Exclude the two addon directories in the and the odoo folder
        if f.is_dir() and f.name in ['addons', 'odoo']:
            continue
        tgt = fson_tgt_dir / f.name
        symlink_rel(source=f, target=tgt, src_relative_to=fson_tgt_dir, dry=dry)

    # Link OCA/OCB/odoo/* without OCA/OCB/odoo/addons
    odoo_tgt_dir = e.dev_fson_tgt_dir / 'odoo'
    if not dry:
        odoo_tgt_dir.mkdir(mode=mode, exist_ok=True)
    for f in (e.core_odoo_src / 'odoo').iterdir():
        if f.is_dir() and f.name == 'addons':
            continue
        tgt = odoo_tgt_dir / f.name
        symlink_rel(source=f, target=tgt, src_relative_to=fson_tgt_dir, dry=dry)

    # Create the target dir for all addons fsonline/dev/fsonline/odoo/addons
    all_addons_tgt_dir = odoo_tgt_dir / 'addons'
    if not dry:
        all_addons_tgt_dir.mkdir(mode=mode, exist_ok=True)

    # Link OCA/OCB/odoo/addons
    for f in (e.core_odoo_src / 'odoo' / 'addons').iterdir():
        tgt = all_addons_tgt_dir / f.name
        symlink_rel(source=f, target=tgt, src_relative_to=fson_tgt_dir, dry=dry)

    # Link OCA/OCB/addons
    for f in (e.core_odoo_src / 'addons').iterdir():
        tgt = all_addons_tgt_dir / f.name
        symlink_rel(source=f, target=tgt, src_relative_to=fson_tgt_dir, dry=dry)

    # Link all non-core addons
    other_addons = copy.copy(e.core_addon_dirs)
    if e.inst_addon_dirs:
        other_addons += e.inst_addon_dirs
    for addon_dir in other_addons:
        tgt = all_addons_tgt_dir / addon_dir.name
        symlink_rel(source=addon_dir, target=tgt, src_relative_to=fson_tgt_dir, dry=dry)


@task(pre=[init_submodules, symlink_odoo], default=True)
def init(c, env=''):
    """ Prepare the repository folder for development:
            - initialize submodules recursively
            - symlink odoo in the [dev] folder
    """
