# -*- coding: utf-8 -*-

from typing import List
from urllib.parse import quote

from cloud_api_signer.models import HttpParams


def uri_encode(s: str):
    # python 3.7 之前，波浪线(~) 不作为保留字符，需要明确指定
    return quote(s, safe='~')


def uri_encode_except_slash(s: str):
    return quote(s, safe='/~')


def make_canonical_query_string(params: HttpParams) -> str:
    param_list: List[str] = []
    for k, v in params.items():
        new_k = uri_encode(k)
        new_v = '' if v is None else uri_encode(str(v))
        param_list.append(f'{new_k}={new_v}')
    return '&'.join(sorted(param_list))
