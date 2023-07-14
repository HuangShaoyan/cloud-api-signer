# -*- coding: utf-8 -*-
""" 火山引擎 API 的签名实现

https://www.volcengine.com/docs/6369/67269

"""

import hashlib
import hmac
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel
from typing_extensions import Final

from cloud_api_signer import utils
from cloud_api_signer.models import AkSk, HttpHeaders, HttpMethod, HttpParams

# 变量命名与官方文档保持一致，便于理解和校对

# 官方文档约定：算法固定为 HMAC-SHA256
ALGORITHM: Final = 'HMAC-SHA256'


class AuthResult(BaseModel):
    """ 存放签名计算的结果和重要的中间值，以便验证 """

    # 包含 Authorization 和其他签名过程中自动生成的 header。可以作为 http 请求的 headers 参数
    # 对于火山引擎，它包含5个 header：Authorization X-Date X-Content-Sha256 Host Content-Type
    sign_result: Dict[str, str]

    # 下面的值是中间结果，用于验证
    canonical_query_string: str
    canonical_headers: str
    signed_headers: str
    canonical_request: str
    credential_scope: str
    string_to_sign: str


class ApiInfo(BaseModel):
    region: str
    service: str
    host: str
    path: str = '/'  # 火山的 API 路径，几乎都是 '/'
    http_request_method: HttpMethod


def make_auth(
    aksk: AkSk,
    api_info: ApiInfo,
    params: HttpParams,
    content_type: str,
    body_str: Optional[str] = None,
) -> AuthResult:
    """ 实现签名算法，返回签名结果 """
    canonical_uri = api_info.path
    canonical_query_string = utils.make_canonical_query_string(params)

    x_date, x_date_short = _to_x_date()
    x_content_sha256 = _hash_sha256(body_str or '')

    headers_to_sign: HttpHeaders = {
        'X-Date': x_date,
        'X-Content-Sha256': x_content_sha256,
        'Host': api_info.host,
        'Content-Type': content_type,
    }
    ordered_headers = _make_oredered_headers(headers_to_sign)
    signed_headers = ';'.join([k for k, _ in ordered_headers])
    # 每一个 canonical_header 都要以 \n 结尾，包括最后一个
    canonical_headers = ''.join([f'{k}:{v}\n' for k, v in ordered_headers])
    canonical_request = '\n'.join(
        [
            api_info.http_request_method,
            canonical_uri,
            canonical_query_string,
            canonical_headers,
            signed_headers,
            x_content_sha256,
        ]
    )

    credential_scope = f'{x_date_short}/{api_info.region}/{api_info.service}/request'
    string_to_sign = _make_string_to_sign(x_date, credential_scope, canonical_request)
    signature = _make_signature(aksk, x_date_short, api_info, string_to_sign)

    return AuthResult(
        canonical_query_string=canonical_query_string,
        canonical_headers=canonical_headers,
        signed_headers=signed_headers,
        canonical_request=canonical_request,
        credential_scope=credential_scope,
        string_to_sign=string_to_sign,
        sign_result={
            'Authorization': (
                f'{ALGORITHM} Credential={aksk.ak}/{credential_scope}, '
                f'SignedHeaders={signed_headers}, Signature={signature}'
            ),
            **headers_to_sign,
        },
    )


def _to_x_date() -> Tuple[str, str]:
    # 火山引擎的 x-data 格式是 ISO8601
    # 如：20201230T081805Z
    t = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    return t, t[:8]


def _make_oredered_headers(headers: HttpHeaders) -> List[Tuple[str, str]]:
    lowercase_headers = [(k.strip().lower(), v.strip()) for k, v in headers.items()]
    return sorted(lowercase_headers, key=lambda x: x[0])


def _make_string_to_sign(x_date: str, credential_scope: str, canonical_request: str) -> str:
    request_date = x_date
    hashed_canonical_request = _hash_sha256(canonical_request)
    return '\n'.join([ALGORITHM, request_date, credential_scope, hashed_canonical_request])


def _make_signature(aksk: AkSk, x_date_short: str, api_info: ApiInfo, string_to_sign: str) -> str:
    """ 从 sk 派生出 signing key，然后签名得到 signature """
    k_date = _hmac_sha256(aksk.sk.encode('utf-8'), x_date_short)
    k_region = _hmac_sha256(k_date, api_info.region)
    k_service = _hmac_sha256(k_region, api_info.service)
    k_signing = _hmac_sha256(k_service, 'request')
    return _hmac_sha256(k_signing, string_to_sign).hex()


def _hmac_sha256(key: bytes, content: str) -> bytes:
    """ hmac sha256 算法 """
    return hmac.new(key, content.encode('utf-8'), hashlib.sha256).digest()


def _hash_sha256(content: str) -> str:
    """ sha256 算法 """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
