import pytest


"""
Calculate the function signature given a string containing the function name and argument types.
"""
@pytest.fixture
def calc_func_sig(w3):
    def function_sig(function_descriptor):
        return w3.sha3(text=function_descriptor)[0:4]
    return function_sig


"""
Calculate the function signature (in bytes) given the function name and an abi
"""
@pytest.fixture
def get_func_sig(w3, calc_func_sig):
    def function_sig(function_name, abi):
        string = function_name + "("
        inputs = next((d["inputs"] for (i, d) in enumerate(abi) if d["name"] == function_name), None)
        string += ",".join(i["type"] for i in inputs)
        string += ")"
        return calc_func_sig(string)
    return function_sig