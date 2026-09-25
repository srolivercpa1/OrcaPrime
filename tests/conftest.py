"""Release destroyed Tk interpreters on the main test thread.

Some API tests start worker threads. Without collection between tests, reference
cycles from earlier GUI windows can be collected by those workers; Tcl requires
its interpreter and image resources to be finalized on their owning thread.
"""
import gc
import pytest


@pytest.fixture(autouse=True)
def collect_gui_resources_on_owner_thread():
    gc.collect()
    yield
    gc.collect()
