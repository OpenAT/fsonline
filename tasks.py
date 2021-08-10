import logging
import os
from pathlib import Path

from invoke import Collection, Executor
from tools.tasks import git, dev, odoo, docker

from tools.env_settings import fsonline_env


# Logging setup
# -------------
logger = logging.getLogger(__name__)
log_handler = logging.StreamHandler()
log_formatter = logging.Formatter("%(name)s %(levelname)s: %(message)s")
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)
LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})

# Get the loglevel from the environment
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
logger.info(f"Logging initialized in {Path(__file__)}")


# INVOKE
# ------
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ATTENTION: We can not use type annotation for @task decorated functions because
#            https://github.com/pyinvoke/invoke/pull/373 is not merged yet :(
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def invoke_execute(context, command_name, **kwargs):
    """
    Helper function to make invoke-tasks execution within python easier until
    https://github.com/pyinvoke/invoke/issues/170 is resolved

    # Example call inside a task: 'c.invoke_execute(c, 'dev.init_submodules', env=env)'
    """
    results = Executor(namespace, config=context.config).execute((command_name, kwargs))
    target_task = context.root_namespace[command_name]
    return results[target_task]


namespace = Collection()
namespace.add_collection(dev)
namespace.add_collection(git)
namespace.add_collection(odoo)
namespace.add_collection(docker)
namespace.configure({
    'root_namespace': namespace,
    'invoke_execute': invoke_execute,
    'fsonline_env_settings': fsonline_env(),
})
