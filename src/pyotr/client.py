from pathlib import Path
from types import ModuleType
from typing import Optional, Type, Union, Callable, Any

import httpx.api
from openapi_core import create_spec
from openapi_core.schema.servers.models import Server
from openapi_core.schema.specs.models import Spec
from openapi_core.shortcuts import ResponseValidator
from openapi_core.validation.response.datatypes import OpenAPIResponse
from stringcase import snakecase

from pyotr.utils import Requestable, get_spec_from_file
from pyotr.validation.requests import ClientOpenAPIRequest
from pyotr.validation.responses import ClientOpenAPIResponse


class Client:
    def __init__(
        self,
        spec: Union[Spec, dict],
        *,
        server_url: Optional[str] = None,
        client: Union[ModuleType, Requestable] = httpx.api,
        request_class: Type[ClientOpenAPIRequest] = ClientOpenAPIRequest,
        response_factory: Callable[[Any], OpenAPIResponse] = ClientOpenAPIResponse,
    ):
        if not isinstance(spec, Spec):
            spec = create_spec(spec)
        self.spec = spec
        self.client = client
        self.request_class = request_class
        self.response_factory = response_factory

        if server_url is None:
            server_url = self.spec.servers[0].url
        else:
            server_url = server_url.rstrip("/")
            for server in self.spec.servers:
                if server_url == server.url:
                    break
            else:
                self.spec.servers.append(Server(server_url))
        self.server_url = server_url
        self.validator = ResponseValidator(self.spec)

        for path_spec in spec.paths.values():
            for op_spec in path_spec.operations.values():
                setattr(
                    self, snakecase(op_spec.operation_id), self._get_operation(op_spec).__get__(self),
                )

    @staticmethod
    def _get_operation(op_spec):
        # TODO: extract args and kwargs from operation parameters
        def operation(
            self, *args, body_: Optional[Union[dict, list]] = None, headers_: Optional[dict] = None, **kwargs,
        ):
            request = self.request_class(self.server_url, op_spec)
            request.prepare(*args, data_=body_, headers_=headers_, **kwargs)
            api_response = self.client.request(
                method=request.method, url=request.url, data=request.body, headers=request.headers
            )
            api_response.raise_for_status()
            response = self.response_factory(api_response)
            self.validator.validate(request, response).raise_for_errors()
            return response

        operation.__doc__ = op_spec.summary or op_spec.operation_id
        if op_spec.description:
            operation.__doc__ += f"\n\n{op_spec.description}"
        return operation

    @classmethod
    def from_file(cls, path: Union[Path, str], **kwargs):
        """ Creates an instance of the class by loading the spec from a local file.
        """
        spec = get_spec_from_file(path)
        return cls(spec, **kwargs)
