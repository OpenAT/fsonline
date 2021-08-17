from invoke import task
from tools.env_settings import FsonlineEnv
import logging

logger = logging.getLogger(__name__)


@task
def create_addon(c, name, core=False, minimal=False):
    """ Create a new Odoo addon """

    e: FsonlineEnv = c['fsonline_env_settings']
    if not e.inst_dir:
        core = True

    template_src = e.core_dir / 'tools' / 'copier-templates' / 'odoo_addon'
    target_dir = e.inst_addon_src  # TODO: Test

    if core:
        target_dir = e.core_dir / "src" / "DADI" / name

    if target_dir.exists():
        target_files = [file for file in target_dir.glob("*.*")]
        if target_files:
            logger.error(f"Target addon directory is not empty, aborting. Directory: {target_dir}")
            return

    args = ""

    if minimal:
        args = args + \
            " -d models=False" + \
            " -d views=False" + \
            " -d security=False" + \
            " -d data=False" + \
            " -d i18n=False" + \
            " -d controllers=False" + \
            " -d static=False" + \
            " -d demo=False" + \
            " -d unittest=False"

    shell_command = f"copier \"{template_src}\" \"{target_dir}\" {args}"
    c.run(shell_command, pty=True)

@task
def create_model(c, addon, core=False):
    """ Create a new Odoo model """

    e: FsonlineEnv = c['fsonline_env_settings']
    if not e.inst_dir:
        core = True

    template_src = e.core_dir / 'tools' / 'copier-templates' / 'odoo_model'
    target_dir = e.inst_addon_src  # TODO: Test

    if core:
        target_dir = e.core_dir / "src" / "DADI" / addon

    if not (target_dir / "manifest.py").is_file():
        logger.error(f"Destination had no manifest.py: {target_dir}")
        return

    args = f"-d addon_name={addon}"
    shell_command = f"copier \"{template_src}\" \"{target_dir}\" {args}"
    c.run(shell_command, pty=True)
