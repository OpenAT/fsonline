# https://medium.com/swlh/cool-things-you-can-do-with-pydantic-fc1c948fbde0#2e89
#
# ATTENTION: pydantic has no computed fields - if you need to compute attribs (fields) based on other fields you
#            do this in the __init__ function (dont forget to call super). This will work as long as you do not
#            plan to freeze the data by "allow_mutation = False". If you need locked Data you should compute the
#            input data first and than just use a pydantic class object to validate and store the computed data.
import pprint
from functools import lru_cache
from typing import Optional, Set, Literal, List
from pathlib import Path
import tempfile
from pydantic import (
    BaseSettings,
    Field,
    BaseModel,
    DirectoryPath,
    FilePath,
    validator,
)
from .globals import ALLOWED_ENVIRONMENTS
from .helper import (
    find_addons,
    merge_env_files,
)


class Conventions(BaseModel):
    """ All static conventions like file_names, folder_names, relative_locations should be represented here. """
    script_file: FilePath = Path(__file__)
    script_folder: DirectoryPath = Path(__file__).parent

    odoo_manifest_name: str = "__manifest__.py"

    dev_dir_name: Path = Path('dev')
    stg_dir_name: Path = Path('stg')
    prd_dir_name: Path = Path('prd')

    # core
    core_env_name: str = "core.env"
    core_env_file: FilePath = script_folder.parent / core_env_name
    core_dir: DirectoryPath = core_env_file.parent

    # instance
    inst_env_name: str = "inst.env"
    inst_env_file: Optional[FilePath] = (core_dir.parent / inst_env_name) if (
            core_dir.parent / inst_env_name).is_file() else None
    inst_dir: Optional[DirectoryPath] = inst_env_file.parent if inst_env_file else None

    # basics
    repo_dir: DirectoryPath = inst_dir or core_dir

    dev_dir: Path = repo_dir / dev_dir_name
    stg_dir: Path = repo_dir / stg_dir_name
    prd_dir: Path = repo_dir / prd_dir_name

    dev_fson_tgt_dir = dev_dir / 'fsonline'

    @validator('core_dir', 'inst_dir', always=True)
    def v_core_dir_inst_dir(cls, v):
        if v and not (v / '.git').is_dir():
            raise ValueError(f"'{v}' has no .git folder inside!")
        return v

    @validator('repo_dir', always=True)
    def v_repo_dir(cls, v, values):
        if not v.is_absolute():
            raise ValueError(f"'{v}' must be absolute!")
        if v == Path("/"):
            raise ValueError(f"'{v}' can not be root '/'!")
        return v

    class Config:
        validate_assignment = True


@lru_cache()
def conventions() -> Conventions:
    return Conventions()


BASE_ENV_FILES = tempfile.NamedTemporaryFile(mode='w+')


class BaseEnv(BaseSettings):
    """ just load the wanted environment from os.environ or use the default dev environment
        ATTENTION: Never Load / use BaseEnv or
    """
    # TODO: Maybe we should remove the default to make sure the environment was consciously set?
    env: ALLOWED_ENVIRONMENTS = Field(default='DEV', env="FSONLINE_ENVIRONMENT")

    # Merge the env files and update the tmp file before initializing the object
    def __init__(self, **data) -> None:
        try:
            # Get the environment either from the kwargs or use the same value as in class attrib 'env'
            env_file_data = merge_env_files(target_env=None,
                                            env_files=[conventions().core_env_file, conventions().inst_env_file]
                                            ).getvalue()
            BASE_ENV_FILES.write(env_file_data)
            BASE_ENV_FILES.seek(0)
            super(BaseEnv, self).__init__(**data)
        except Exception as e:
            raise e
        finally:
            BASE_ENV_FILES.seek(0)
            BASE_ENV_FILES.truncate()

    class Config:
        env_file = BASE_ENV_FILES.name
        validate_assignment = True


def base_env(**kwargs) -> BaseEnv:
    return BaseEnv(**kwargs)


ENV_FILES = tempfile.NamedTemporaryFile(mode='w+')


class CoreEnv(BaseSettings):
    """ core settings """
    # special settings
    env: ALLOWED_ENVIRONMENTS
    env_file_data: Optional[str] = Field(env=None)
    cov: Conventions = Field(default=conventions(), env=None)

    # merged conventions settings for the core
    core_dir: DirectoryPath = Field(default=conventions().core_dir, env=None)

    # ENVIRONMENT SETTINGS
    core_odoo_src: Path
    core_addon_src: List[Path] = list()

    # COMPUTED SETTINGS
    core_odoo_dir: Optional[DirectoryPath] = None
    core_addon_dirs: Optional[List[DirectoryPath]] = Field(env=None)

    @validator('core_odoo_dir', always=True)
    def v_core_odoo_dir(cls, v, values):
        """ Compute and validate 'core_odoo_dir' """
        v: Path = values['core_dir'] / values['core_odoo_src']
        if not v.is_dir():
            raise ValueError(f"core_odoo_dir {v} is missing or not a directory")
        if not (v / 'odoo' / 'addons' / 'base').is_dir():
            raise ValueError(f"odoo seems not to be in the core_odoo_dir {v}")
        return v

    @validator('core_addon_dirs', always=True)
    def v_core_addon_dirs(cls, v, values):
        """ Compute and validate 'core_addon_dirs' """
        core_addon_src = values['core_addon_src']
        if core_addon_src:
            v = find_addons(core_addon_src, start_dir=values['core_dir'], manifest=values['cov'].odoo_manifest_name)
        return v

    def __init__(self, **data):
        # merged core and instance environment files *.env > *.env.[dev] > *.env.local
        try:
            # Get the environment either from the kwargs or from base_env()
            data['env'] = base_env(env=data['env']).env if data.get('env', None) else base_env().env
            env_file_data = merge_env_files(target_env=data['env'],
                                            env_files=[conventions().core_env_file, conventions().inst_env_file]
                                            ).getvalue()
            ENV_FILES.write(env_file_data)
            ENV_FILES.seek(0)

            super(CoreEnv, self).__init__(**data)
            self.env_file_data = env_file_data
        except Exception as e:
            raise e
        finally:
            ENV_FILES.seek(0)
            ENV_FILES.truncate()

    class Config:
        validate_assignment = True
        # ATTENTION: The configs seems to be merged for all inherited classes and the first class in the tree will
        #            set the env_file (contrary to what i would have guessed - the last class wins ...)
        env_file = ENV_FILES.name


class InstanceEnv(CoreEnv):
    """ Additional instance settings and overrides """

    # base settings
    inst_dir: Optional[DirectoryPath] = Field(default=conventions().inst_dir, env=None)

    # ENVIRONMENT SETTINGS
    inst_addon_src: Optional[List[Path]]

    # COMPUTED SETTINGS
    inst_addon_dirs: Optional[List[DirectoryPath]] = Field(env=None)
    
    @validator('inst_addon_dirs', always=True)
    def v_inst_addon_dirs(cls, v, values):
        """ Compute and validate 'inst_addon_dirs' """
        inst_addon_src = values['inst_addon_src']
        if inst_addon_src:
            v = find_addons(inst_addon_src, start_dir=values['inst_dir'], manifest=values['cov'].odoo_manifest_name)
        return v


class FsonlineEnv(InstanceEnv):

    # merged conventions settings
    repo_dir: DirectoryPath = Field(default=conventions().repo_dir, env=None)

    dev_dir: Path = Field(default=conventions().dev_dir, env=None)
    stg_dir: Path = Field(default=conventions().stg_dir, env=None)
    prd_dir: Path = Field(default=conventions().prd_dir, env=None)

    dev_fson_tgt_dir: Path = Field(default=conventions().dev_fson_tgt_dir, env=None)

    class Config:
        allow_mutation = True


def fsonline_env(**kwargs) -> FsonlineEnv:
    env = FsonlineEnv(**kwargs)
    return env

