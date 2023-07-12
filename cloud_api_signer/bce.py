# -*- coding: utf-8 -*-
""" 百度智能云 API 的签名实现

https://cloud.baidu.com/doc/Reference/s/njwvz1yfu

"""

import hashlib
import hmac
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from pydantic import BaseModel
from typing_extensions import Final

from cloud_api_signer import utils
from cloud_api_signer.models import AkSk, HttpHeaders, HttpParams

BCE_PREFIX: Final = 'x-bce-'

# 签名有效期限，硬编码以简化调用者的代码
EXPIRATION_PERIOD_IN_SECONDS: Final = 1800


class AuthResult(BaseModel):
    """ 存放签名计算的结果和重要的中间值，以便验证 """

    # 包含 Authorization 和其他必要的 header。可以作为 http 请求的 headers 参数
    # 对于百度智能云，它包含1个 header：Authorization
    sign_result: Dict[str, str]

    # 下面的值是中间结果，用于验证
    canonical_request: str
    auth_string_prefix: str
    signing_key: str
    signature: str


def make_auth(
    aksk: AkSk,
    method: str,
    path: str,
    params: HttpParams,
    headers: HttpHeaders,
    headers_to_sign: Set[str] = None,
) -> AuthResult:
    canonical_uri = utils.uri_encode_except_slash(path)
    canonical_query_string = utils.make_canonical_query_string(params)
    canonical_headers, signed_headers = _to_canonical_headers(headers, headers_to_sign)
    canonical_request = f'{method}\n{canonical_uri}\n{canonical_query_string}\n{canonical_headers}'

    # 文档中将“生成签名的 UTC 时间”称为 timestamp
    # 但它其实是一个 rfc3339 格式的字符串。这里沿用 timestamp 的命名，以便和文档一致
    timestamp = _to_timestamp()

    auth_string_prefix = f'bce-auth-v1/{aksk.ak}/{timestamp}/{EXPIRATION_PERIOD_IN_SECONDS}'

    signing_key = hmac.new(aksk.sk.encode(), auth_string_prefix.encode(), hashlib.sha256).hexdigest()

    signature = hmac.new(signing_key.encode(), canonical_request.encode(), hashlib.sha256).hexdigest()

    return AuthResult(
        canonical_request=canonical_request,
        auth_string_prefix=auth_string_prefix,
        signing_key=signing_key,
        signature=signature,
        sign_result={
            'Authorization': f'{auth_string_prefix}/{signed_headers}/{signature}',
        },
    )


def _to_canonical_headers(headers: HttpHeaders, headers_to_sign: Optional[Set[str]] = None) -> Tuple[str, str]:
    headers = headers or {}

    if headers_to_sign is None or len(headers_to_sign) == 0:
        headers_to_sign = {
            # 百度云只强制要求编码 "host" header
            'host',
        }
    else:
        headers_to_sign = {h.strip().lower() for h in headers_to_sign}

    result: List[str] = []
    signed_headers: Set[str] = set()
    for k, v in headers.items():
        k_lower = k.strip().lower()

        if k_lower.startswith(BCE_PREFIX) or k_lower in headers_to_sign:
            new_k = utils.uri_encode(k_lower)
            new_v = utils.uri_encode(str(v).strip())
            result.append(f'{new_k}:{new_v}')
            signed_headers.add(new_k)

    return '\n'.join(sorted(result)), ';'.join(sorted(signed_headers))


def _to_timestamp() -> str:
    # 百度智能云的时间戳，按照 rfc3339 格式，精确到秒
    # 如：2015-04-27T08:23:49Z
    t = datetime.utcnow().isoformat(timespec='seconds')
    return f'{t}Z'
