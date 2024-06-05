from datetime import datetime
from unittest.mock import Mock

import pytest

from cloud_api_signer.bce import ApiInfo, make_auth
from cloud_api_signer.volc import AkSk


@pytest.fixture(autouse=True)
def fake_utcnow(mocker):
    mocked = mocker.patch('cloud_api_signer.bce.datetime')
    # 2015-04-27T08:23:49Z
    mocked.utcnow = Mock(return_value=datetime(2015, 4, 27, 8, 23, 49))


def test_sign_demo_ok():
    # 参考：https://cloud.baidu.com/doc/Reference/s/wjwvz1xt2
    # 这个用例和上述链接的示例，使用相同的输入，得到相同的输出
    # 可借助 https://cloud.baidu.com/signature/index.html 计算出中间结果加以验证

    fake_aksk = AkSk(
        ak='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        sk='bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
    )

    actual = make_auth(
        aksk=fake_aksk,
        api_info=ApiInfo(
            host='bj.bcebos.com',
            path='/v1/test/myfolder/readme.txt',
            http_request_method='PUT',
        ),
        params={
            'partNumber': 9,
            'uploadId': 'a44cc9bab11cbd156984767aad637851',
        },
    )

    # 转换为 dict 进行比较，更有利借助 icdiff，快速定位有差异的字段
    expect = {
        'canonical_request': """PUT
/v1/test/myfolder/readme.txt
partNumber=9&uploadId=a44cc9bab11cbd156984767aad637851
host:bj.bcebos.com
x-bce-date:2015-04-27T08%3A23%3A49Z""",
        'auth_string_prefix': 'bce-auth-v1/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/2015-04-27T08:23:49Z/1800',
        'signing_key': '1d5ce5f464064cbee060330d973218821825ac6952368a482a592e6615aef479',
        'signature': '1b8de5a23a56eef657c69f94c621e7acd227d049a4ba577f537d5e5cebf0cf32',
        'sign_result': {
            'Authorization': (
                'bce-auth-v1/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/2015-04-27T08:23:49Z/1800'
                '/host;x-bce-date'
                '/1b8de5a23a56eef657c69f94c621e7acd227d049a4ba577f537d5e5cebf0cf32'
            ),  # 这是一个单行文本
            'host': 'bj.bcebos.com',
            'x-bce-date': '2015-04-27T08:23:49Z',
        },
    }

    assert expect == actual.model_dump()
