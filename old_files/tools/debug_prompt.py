import os
import sys
from rys.role_utils import construct_system_prompt

base_dir = os.getcwd()
prompt = construct_system_prompt(base_dir, "coder", ["shell_exec"], True, None)
print(prompt)
