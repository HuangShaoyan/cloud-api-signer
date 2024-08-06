from typing import List
from urllib.parse import quote

from cloud_api_signer.models import HttpParams


def make_canonical_query_string_bce(params: HttpParams) -> str:
    param_list: List[str] = []
    # 百度云的规则是：按照 key=value 排序
    # https://cloud.baidu.com/doc/Reference/s/hjwvz1y4f
    for k, v in params.items():
        new_k = quote(k, safe='')
        new_v = '' if v is None else quote(str(v), safe='')
        param_list.append(f'{new_k}={new_v}')
    return '&'.join(sorted(param_list))


def make_canonical_query_string_volc(params: HttpParams) -> str:
    param_list: List[str] = []
    # 火山云的规则是：按照 key 排序
    # quote 的 safe 字符，不包括默认的'/'，因此需要显式设置
    # https://www.volcengine.com/docs/6369/67269
    for k in sorted(params.keys()):
        new_k = quote(k, safe='')
        new_v = '' if params[k] is None else quote(str(params[k]), safe='')
        param_list.append(f'{new_k}={new_v}')
    return '&'.join(param_list)
