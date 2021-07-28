from os import SCHED_IDLE
from pathlib import Path

class FsonlineEnvironment():
    """
    Uses marker files to detect the current FS-Online development environment,
    which can either be "core" or "instance".

    """

    # Constants
    CORE_MARKER = ".core"
    INSTANCE_MARKER = ".instance"
    SCRIPT_PATH = Path(__file__).parent

    # Environment properties
    name = "core"
    is_instance = False
    core_path = SCRIPT_PATH
    instance_path = None
    tools_path = core_path / "tools"

    def __init__(self) -> None:
        assert (self.SCRIPT_PATH / self.CORE_MARKER).is_file(), \
            u"ERROR: Script root had no %s file marker." % self.CORE_MARKER

        if (self.SCRIPT_PATH.parent / self.INSTANCE_MARKER).is_file():
            self.name = "instance"
            self.is_instance = True
            self.use_instance_paths()

    def use_instance_paths(self):
        self.instance_path = Path(self.SCRIPT_PATH).parent
        self.tools_path = self.instance_path / "fsonline" / "tools"
