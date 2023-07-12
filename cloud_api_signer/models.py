# -*- coding: utf-8 -*-
""" 定义通用的 Model """

from typing import Dict, Optional, Union

from pydantic import BaseModel
from typing_extensions import Literal

HttpMethod = Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD']
HttpHeaders = Dict[str, str]
HttpParams = Dict[str, Optional[Union[str, int]]]


class AkSk(BaseModel):
    ak: str
    sk: str
