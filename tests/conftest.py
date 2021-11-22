import pytest


@pytest.fixture(autouse=True, scope='session')
def create_catalog():
    import jschon

    jschon.create_catalog('2020-12')
