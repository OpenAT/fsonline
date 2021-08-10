import pytest
from typing import List
from pydantic import BaseModel


class Names(BaseModel):
    values: List[str]


def test_values_is_not_part_of_the_input_data():
    with pytest.raises(TypeError):                  # 1
        Names(values=['name1', 'name2', 'name3'])   # 1