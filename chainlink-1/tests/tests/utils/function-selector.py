import pytest


@pytest.fixture
def function_selector(w3):
    def get_selector(signature):
        return w3.sha3(text=signature)[:4].hex()
    return get_selector
