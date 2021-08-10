import os
from pathlib import Path
from tools.env_settings import conventions, fsonline_env


def test_environment_overrides():
    os.environ.clear()
    # Default value for env
    settings = fsonline_env()
    assert settings.env == 'DEV'

    # From kwargs
    os.environ.clear()
    settings = fsonline_env(env='STG')
    assert settings.env == 'STG'

    # From file
    os.environ.clear()
    core_override_file = Path(str(conventions().core_env_file) + '.local')
    assert not core_override_file.exists(), "Local override File exists %s" % core_override_file
    if not core_override_file.exists():
        with open(core_override_file, mode="w") as of:
            try:
                of.write('FSONLINE_ENVIRONMENT="PRD"\nCORE_ODOO_SRC="tools/tests"')
                of.seek(0)
                settings = fsonline_env()
                assert settings.env == 'PRD'
                assert str(settings.core_odoo_src) == 'tools/tests'
            except Exception as e:
                raise e
            finally:
                of.close()
                if core_override_file.exists():
                    os.remove(core_override_file)

    # From os environment
    os.environ.clear()
    os.environ["FSONLINE_ENVIRONMENT"] = 'STG'
    settings = fsonline_env()
    assert settings.env == 'STG'
