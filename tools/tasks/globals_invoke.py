from typing import Literal, TypedDict, Optional
from tools.env_settings import FsonlineEnv
from tools.globals import ALLOWED_ENVIRONMENTS


INVOKE_CONTEXT_TYPE = TypedDict('INVOKE_CONTEXT_TYPE',
                                {'env': ALLOWED_ENVIRONMENTS,
                                 'fso_settings': FsonlineEnv},
                                total=False)
