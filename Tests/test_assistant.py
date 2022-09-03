import pytest
import keyboard
from assistant import *

def test_execute_command():
    asst = Assistant()
    with pytest.raises(sr.UnknownValueError):
        asst.execute_command("search")
