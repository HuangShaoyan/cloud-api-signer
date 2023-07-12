# -*- coding: utf-8 -*-

from datetime import datetime
from unittest.mock import Mock

import pytest

from cloud_api_signer.volc import AkSk, ApiInfo, HttpHeaders, _make_oredered_headers, make_auth


@pytest.fixture(autouse=True)
def fake_utcnow(mocker):
    mocked = mocker.patch('cloud_api_signer.volc.datetime')
    # 20201230T081805Z
    mocked.utcnow = Mock(return_value=datetime(2020, 12, 30, 8, 18, 5))


def test_sign_demo_ok():
    # 使用火山引擎文档中提供的测试数据，校验签名算法的实现是否符合预期
    # https://www.volcengine.com/docs/6369/67270

    fake_aksk = AkSk(
        ak='AKLTMjI2ODVlYzI3ZGY1NGU4ZjhjYWRjMTlmNTM5OTZkYzE',
        sk='TnpCak5XWXpZV1U0WkRaaE5ERmxaR0ZpTmpjeVkyUXlZek0wTWpJMU1qWQ==',
    )

    api_info = ApiInfo(
        region='cn-north-1',
        service='iam',
        http_request_method='GET',
        host='iam.volcengineapi.com',
        path='/',
    )

    actual = make_auth(
        aksk=fake_aksk,
        api_info=api_info,
        params={  # 刻意打乱顺序，验证排序效果
            'Action': 'ListUsers',
            'Version': '2018-01-01',
            'Limit': 10,
            'Offset': 0,
        },
        content_type='application/x-www-form-urlencoded; charset=utf-8',
    )

    expect = dict(
        canonical_query_string='Action=ListUsers&Limit=10&Offset=0&Version=2018-01-01',
        canonical_headers='''content-type:application/x-www-form-urlencoded; charset=utf-8
host:iam.volcengineapi.com
x-content-sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
x-date:20201230T081805Z
''',  # 注意，结尾处有一个 \n，不能省略
        signed_headers='content-type;host;x-content-sha256;x-date',
        canonical_request='''GET
/
Action=ListUsers&Limit=10&Offset=0&Version=2018-01-01
content-type:application/x-www-form-urlencoded; charset=utf-8
host:iam.volcengineapi.com
x-content-sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
x-date:20201230T081805Z

content-type;host;x-content-sha256;x-date
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855''',
        credential_scope='20201230/cn-north-1/iam/request',
        string_to_sign='''HMAC-SHA256
20201230T081805Z
20201230/cn-north-1/iam/request
3a4d4dee07c3308a52da01bc12d7a83c3705bfa543f51648f46de880bb2a7447''',
        sign_result={
            'Authorization': (
                'HMAC-SHA256 '
                'Credential=AKLTMjI2ODVlYzI3ZGY1NGU4ZjhjYWRjMTlmNTM5OTZkYzE/20201230/cn-north-1/iam/request, '
                'SignedHeaders=content-type;host;x-content-sha256;x-date, '
                'Signature=28eeabbbd726b87002e0fe58ad8c1c768e619b06e2646f35b6ad7ed029a6d8a7'
            ),  # 这是一个单行文本
            'X-Date': '20201230T081805Z',
            'X-Content-Sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
            'Host': 'iam.volcengineapi.com',
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
        },
    )

    # 转换为 dict 进行比较，更有利借助 icdiff，快速定位有差异的字段
    assert expect == actual.dict()


# 针对容易出错的工具函数，对各种边界条件进行测试


class TestMakeOrderedHeaders:

    def test_empty(self):
        actual = _make_oredered_headers({})
        assert [] == actual

    def test_key_must_lower_case(self):
        headers: HttpHeaders = {
            'Bar': 'Abc',  # value 不会被改动，只有 key 会被转换为小写
            'Foo': '1',
        }
        actual = _make_oredered_headers(headers)
        assert [
            ('bar', 'Abc'),
            ('foo', '1'),
        ] == actual

    def test_key_must_ordered_after_lowercase(self):
        headers = {
            'foo9': '4',
            'foo10': '3',
            'Bar2': '2',  # 如果排序前未先转换为小写，则 Bar2 会排在 bar1 之前
            'bar1': '1',
        }
        actual = _make_oredered_headers(headers)
        assert [
            ('bar1', '1'),
            ('bar2', '2'),
            ('foo10', '3'),
            ('foo9', '4'),
        ] == actual
