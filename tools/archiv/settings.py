# GOAL: We want to mount the symbolic links and the sources of the symbolic links into docker
#       while maintaining the same relative file location outside and inside the docker container
#
# EXAMPLE: core only
# - fsonline
#   - dev
#     - odoo
#       - addons
#         - addon_a     <<-- a symbolic link relative to it's location: e.g. "../../../src/DADI/addons/addon_a"
#   - src
#     - DADI
#       - addons
#         - addon_a
#     - OCA
#       - OCB
#
# EXAMPLE: instance
# - aiat
#   - dev
#     - odoo
#       - addons
#         - addon_a     <<-- a symbolic link relative to it's location: e.g. "../../../src/DADI/addons/addon_a"
#         - addon_b     <<-- a symbolic link relative to it's location: e.g. "../../../src_inst/AIAT/addons/addon_b"
#   - src       <-- A symbolic link to ./fsonline/src
#   - src_inst
#     - AIAT
#       - addons
#         - addon_b
#   - fsonline
#     - src
#       - DADI
#         - addons
#       - OCA
#         - OCB

from typing import Optional, Set
from pathlib import Path
from pydantic import (
    BaseSettings,
    Field,
    BaseModel,
    DirectoryPath,
    FilePath,
)
from helper import (
    get_core_repo_dir,
    get_instance_repo_dir,
    find_addons,
)

class CoreEnv(BaseSettings):
    """Core FS-Online environment

    ATTENTION: All relative paths in *.env files are considered relative to the *.env file location !
    """

    # ENVIRONMENT SETTINGS
    environment: Optional[str] = Field(default='DEV', env="ENVIRONMENT")

    core_odoo_src: Path = Path("src/OCA/OCB")
    core_addon_src: Set[Path] = set()

    # COMPUTED SETTINGS
    core_repo_dir: DirectoryPath
    instance_repo_dir: DirectoryPath
    odoo_addon_dirs: Set[DirectoryPath]

    def __init__(self):
        self.core_repo_dir = get_core_repo_dir()
        self.instance_repo_dir: get_instance_repo_dir()
        self.addon_dirs: Set[DirectoryPath]

    class Config:
        env_file: FilePath = Path("core.env")



class AppSettings(BaseModel):

    env_settings: CoreEnv = CoreEnv()

    def __init__(self):
        if self.env_settings.environment



# -------


class InstanceEnv(CoreEnv):
    """Optionally override CoreEnv environment settings with instance settings"""

    instance_addon_src: Set[Path] = set()

    class Config:
        env_file: FilePath = Path("instance.env")


class ApplicationEnv(InstanceEnv):
    """ Compute settings for the invoke tasks and the application """

    CORE_DIR: DirectoryPath
    INSTANCE_DIR: DirectoryPath
    ODOO_ADDON_DIRS: Set[DirectoryPath]

    def get_core_dir()
        Path(__file__).parent

    class Config:
        allow_mutation = False


class DevEnv(ApplicationEnv):
    """Development environment"""

    class Config:
        env_prefix: str = "DEV_"


class StgEnv(ApplicationEnv):
    """Staging environment."""

    class Config:
        env_prefix: str = "STG_"


class PrdEnv(ApplicationEnv):
    """Production environment."""

    class Config:
        env_prefix: str = "PRD_"


class FsonlineEnvironment:
    """Returns a config environment depending on the ENVIRONMENT variable."""

    def __init__(self, environment: Optional[str]):
        self.environment = environment

    def __call__(self):
        if self.environment == "DEV":
            return DevEnv()

        elif self.environment == "STG":
            return StgEnv()

        elif self.environment == "PRD":
            return PrdEnv()




def get_env():
    return FsonlineEnvironment(CoreEnv().ENVIRONMENT)


if __name__ == "__main__":
    print(get_env())
