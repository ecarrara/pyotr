import pytest
from starlette.testclient import TestClient

from pyotr.client import Client
from pyotr.server import Application


def test_client_calls_endpoint(spec_dict, config):
    app = Application.from_file(config.yaml_spec_file, config.endpoint_base)
    client = Client(spec_dict, client=TestClient(app))
    assert client.dummy_test_endpoint() == {'foo': 'bar'}


def test_client_incorrect_args_raises_error(spec_dict, config):
    app = Application.from_file(config.yaml_spec_file, config.endpoint_base)
    client = Client(spec_dict, client=TestClient(app))
    with pytest.raises(RuntimeError):
        client.dummy_test_endpoint('foo')


def test_incorrect_server_url_raises_error(spec_dict):
    with pytest.raises(RuntimeError):
        Client(spec_dict, server_url='foo.bar')


def test_incorrect_incorrect_endpoint_raises_error(spec_dict):
    client = Client(spec_dict)
    with pytest.raises(AttributeError):
        client.foo_bar()


def test_server_from_file_yaml(config):
    app = Client.from_file(config.yaml_spec_file)
    assert app.spec.info.title == "Test Spec"


def test_server_from_file_json(config):
    app = Client.from_file(config.json_spec_file)
    assert app.spec.info.title == "Test Spec"


def test_server_from_file_raises_exception_if_unknown_type(config):
    with pytest.raises(RuntimeError):
        Client.from_file(config.unknown_spec_file)

