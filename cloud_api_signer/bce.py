# -*- coding: utf-8 -*-
""" 百度智能云 API 的签名实现

https://cloud.baidu.com/doc/Reference/s/njwvz1yfu

"""

import hashlib
import hmac
from datetime import datetime
from typing import Dict, List, Set, Tuple

from pydantic import BaseModel
from typing_extensions import Final

from cloud_api_signer import utils
from cloud_api_signer.models import AkSk, HttpHeaders, HttpMethod, HttpParams

# 签名有效期限，硬编码以简化调用者的代码
EXPIRATION_PERIOD_IN_SECONDS: Final = 1800


class AuthResult(BaseModel):
    """ 存放签名计算的结果和重要的中间值，以便验证 """

    # 包含 Authorization 和其他签名过程中自动生成的 header。可以作为 http 请求的 headers 参数
    # 对于百度智能云，它包含3个 header：Authorization、Host 和 x-bce-date
    sign_result: Dict[str, str]

    # 下面的值是中间结果，用于验证
    canonical_request: str
    auth_string_prefix: str
    signing_key: str
    signature: str


class ApiInfo(BaseModel):
    host: str
    path: str
    http_request_method: HttpMethod


def make_auth(
    aksk: AkSk,
    api_info: ApiInfo,
    params: HttpParams,
) -> AuthResult:
    """ 实现签名算法，返回签名结果 """
    canonical_uri = utils.uri_encode_except_slash(api_info.path)
    canonical_query_string = utils.make_canonical_query_string(params)

    # 文档中将“生成签名的 UTC 时间”称为 timestamp
    # 但它其实是一个 rfc3339 格式的字符串。这里沿用 timestamp 的命名，以便和文档一致
    timestamp = _to_timestamp()

    headers_to_sign = {
        # 百度智能云只强制要求编码 "Host" header
        # 百度智能云提供的签名工具总是使用小写的 host，为了便于校验，这里也使用小写
        'host': api_info.host,
        # 再加上 x-bce-date，更好地防御重放攻击。同时，它也是部分 API 的必选项
        'x-bce-date': timestamp,
        # 其他 header 都是可选的，我们的选择是不将它们纳入签名，简化实现
    }
    canonical_headers, signed_headers = _to_canonical_headers(headers_to_sign)
    canonical_request = '\n'.join(
        [
            api_info.http_request_method,
            canonical_uri,
            canonical_query_string,
            canonical_headers,
        ]
    )

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
            **headers_to_sign,
        },
    )


def _to_canonical_headers(headers: HttpHeaders) -> Tuple[str, str]:
    result: List[str] = []
    signed_headers: Set[str] = set()
    for k, v in headers.items():
        # 百度智能云要求 key 和 value 都要进行 uri 编码
        new_k = utils.uri_encode(k)
        new_v = utils.uri_encode(v.strip())
        result.append(f'{new_k}:{new_v}')
        signed_headers.add(new_k)

    return '\n'.join(sorted(result)), ';'.join(sorted(signed_headers))


def _to_timestamp() -> str:
    # 百度智能云的时间戳，按照 rfc3339 格式，精确到秒
    # 如：2015-04-27T08:23:49Z
    t = datetime.utcnow().isoformat(timespec='seconds')
    return f'{t}Z'
