# Copyright 2022 The KServe Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Optional, Union, Dict, List

from fastapi import Request, Response

from kserve.errors import ModelNotReady
from ..dataplane import DataPlane
from ..model_repository_extension import ModelRepositoryExtension


class V1Endpoints:
    """KServe V1 Endpoints
    """

    def __init__(self, dataplane: DataPlane, model_repository_extension: Optional[ModelRepositoryExtension] = None):
        self.model_repository_extension = model_repository_extension
        self.dataplane = dataplane

    async def models(self) -> Dict[str, List[str]]:
        """Get a list of models in the model registry.

        Returns:
            Dict[str, List[str]]: List of model names.
        """
        return {"models": list(self.dataplane.model_registry.get_models().keys())}

    async def model_ready(self, model_name: str) -> Dict[str, Union[str, bool]]:
        """Check if a given model is ready.

        Args:
            model_name (str): Model name.

        Returns:
            Dict[str, Union[str, bool]]: Name of the model and whether it's ready.
        """
        model_ready = self.dataplane.model_ready(model_name)

        if not model_ready:
            raise ModelNotReady(model_name)

        return {"name": model_name, "ready": model_ready}

    async def predict(self, model_name: str, request: Request) -> Union[Response, Dict]:
        """Predict request handler.

        It sends the request to the dataplane where the model will process the request body.

        Args:
            model_name (str): Model name.
            request (Request): Raw request object.

        Returns:
            Dict|Response: Model inference response.
        """
        body = await request.body()
        headers = dict(request.headers.items())
        infer_request, req_attributes = self.dataplane.decode(body=body,
                                                              headers=headers)
        response, response_headers = await self.dataplane.infer(model_name=model_name,
                                                                request=infer_request,
                                                                headers=headers)
        response, response_headers = self.dataplane.encode(model_name=model_name,
                                                           response=response,
                                                           headers=headers, req_attributes=req_attributes)

        if not isinstance(response, dict):
            return Response(content=response, headers=response_headers)
        return response

    async def explain(self, model_name: str, request: Request) -> Union[Response, Dict]:
        """Explain handler.

        Args:
            model_name (str): Model name.
            request (Request): Raw request object.

        Returns:
            Dict: Explainer output.
        """
        body = await request.body()
        headers = dict(request.headers.items())
        infer_request, req_attributes = self.dataplane.decode(body=body,
                                                              headers=headers)
        response, response_headers = await self.dataplane.explain(model_name=model_name,
                                                                  request=infer_request,
                                                                  headers=headers)
        response, response_headers = self.dataplane.encode(model_name=model_name,
                                                           response=response,
                                                           headers=headers, req_attributes=req_attributes)

        if not isinstance(response, dict):
            return Response(content=response, headers=response_headers)
        return response
