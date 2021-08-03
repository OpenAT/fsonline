from pathlib import Path
from invoke.util import yaml


class FsonlineEnvironment():
    """
    Uses marker files to detect the current FS-Online development environment,
    which can either be "core" or "instance". Generates various paths and settings,
    and validates configurations.

    """

    # Constants
    CORE_MARKER = ".core"
    INSTANCE_MARKER = ".instance"
    SCRIPT_PATH = Path(__file__).parent

    # Environment properties
    name = "core"
    is_instance = False
    
    # Core
    core_path = SCRIPT_PATH
    core_addons_path = core_path / "src" / "addons"
    
    # Tools & Build
    tools_path = core_path / "tools"
    build_path = core_path / "build"
    build_config_file = build_path / "build.yml"
    build_config = None
    odoo_config = None
    odoo_source = None
    odoo_target = None
    extra_addons_sources = None
    addons_target = None

    # Instance
    instance_path = None
    instance_addons_path = None

    def __init__(self) -> None:
        """ Create a new FS-Online environment. """

        self.validate_core_marker()
        self.setup_build()
        self.setup_instance()

    def validate_core_marker(self):
        assert (self.SCRIPT_PATH / self.CORE_MARKER).is_file(), \
            "ERROR: Script root had no %s file marker." % self.CORE_MARKER
        return True

    def setup_build(self):
        """ Prepares and validates all build specific properties. """

        self.build_config = yaml.safe_load(
            self.build_config_file.read_text())
        
        self.odoo_config = self.build_config["odoo"]
        self.validate_odoo_config(self.odoo_config)
        self.setup_odoo_paths()

    def setup_odoo_paths(self):
        """ Prepares and validates various Odoo specific path properties. """

        check_build_config_hint = "Check build configuration at {}".format(self.build_config_file)

        self.odoo_source = self.core_path / self.odoo_config["odoo_src"]
        self.validate_path(
            self.odoo_source,
            "Odoo source not found at",
            check_build_config_hint)

        self.odoo_target = self.core_path / self.odoo_config["odoo_tgt"]
        self.validate_path(
            self.odoo_target,
            "Odoo target not found at",
            check_build_config_hint)

        self.addons_target = self.core_path / self.odoo_config["addons_tgt"]
        self.validate_path(
            self.addons_target,
            "Addons target not found at",
            check_build_config_hint)

        self.extra_addons_sources = [self.core_path / src for src in self.odoo_config["addons_src"]]
        for addon_source in self.extra_addons_sources:
            self.validate_path_pattern(
                addon_source,
                "Extra addons source not found at",
                check_build_config_hint)

    def setup_instance(self):
        """ Prepares and validates all instance specific properties. """

        if not (self.SCRIPT_PATH.parent / self.INSTANCE_MARKER).is_file():
            return

        self.name = "instance"
        self.is_instance = True

        self.instance_path = Path(self.SCRIPT_PATH).parent
        self.instance_addons_path = self.instance_path / "addons"
        self.tools_path = self.instance_path / "fsonline" / "tools"

    @staticmethod
    def validate_path(path, fail_message, hint):
        """ Validates a given path and uses fail_messsage and hint on failure. """
        assert path.is_dir(), "{} {}{}".format(fail_message, path, "\n{}".format(hint) if hint else None)

    @staticmethod
    def validate_path_pattern(path, fail_message, hint):
        """ Removes the pattern parts from a path and checks if its a directory. """

        while "*" in path.name:
            path = path.parent
    
        FsonlineEnvironment.validate_path(path, fail_message, hint)

    @staticmethod
    def validate_odoo_config(odoo_cfg):
        odoo_cfg_keys_to_check = (
            "odoo_src",
            "odoo_tgt",
            "addons_src",
            "addons_tgt")

        paths_to_check = []
        for key in odoo_cfg_keys_to_check:
            val = odoo_cfg[key]
            if isinstance(val, str):
                paths_to_check.append(val)
            elif isinstance(val, list):
                paths_to_check += val
            else:
                raise TypeError("val must be of type string or list! {}".format(val))

        for path in paths_to_check:
            assert not path.startswith('/'), "Config path is not relative {}".format(path)
            assert len(path) >= 3, "Config path is too short {}".format(path)

        assert any(p.startswith('build/') for p in (odoo_cfg["odoo_tgt"], odoo_cfg["addons_tgt"])), (
            "The build targets must start with 'build/' !")

        return True
