# -*- coding: utf-8 -*-

import string

from cloud_api_signer.models import HttpParams
from cloud_api_signer.utils import make_canonical_query_string, uri_encode, uri_encode_except_slash


def test_uri_encode():
    assert string.digits == uri_encode(string.digits)
    assert string.ascii_letters == uri_encode(string.ascii_letters)
    assert ('%21%22%23%24%25%26%27%28%29%2A%2B%2C-.'
            '%2F%3A%3B%3C%3D%3E%3F%40%5B%5C%5D%5E_%60%7B%7C%7D~') == uri_encode(string.punctuation)
    assert '%20%09%0A%0D%0B%0C' == uri_encode(string.whitespace)


def test_uri_encode_except_slash():
    assert string.digits == uri_encode_except_slash(string.digits)
    assert string.ascii_letters == uri_encode_except_slash(string.ascii_letters)
    assert ('%21%22%23%24%25%26%27%28%29%2A%2B%2C-.'
            '/%3A%3B%3C%3D%3E%3F%40%5B%5C%5D%5E_%60%7B%7C%7D~') == uri_encode_except_slash(string.punctuation)
    assert '%20%09%0A%0D%0B%0C' == uri_encode_except_slash(string.whitespace)


class TestMakeCanonicalQueryString:

    def test_empty_param(self):
        actual = make_canonical_query_string({})
        assert '' == actual

    def test_order(self):
        """ 按照参数名的字典序进行排序 """
        params: HttpParams = {
            'Foo': 1,
            'Bar': 'abc',
        }
        actual = make_canonical_query_string(params)
        assert 'Bar=abc&Foo=1' == actual

    def test_url_encode(self):
        """ 参数名称和值，都要进行 url 编码 """
        params: HttpParams = {
            'Foo=100': '1&2',
            'bar/a': 'abc/def',
        }
        actual = make_canonical_query_string(params)
        assert 'Foo%3D100=1%262&bar%2Fa=abc%2Fdef' == actual

    def test_special_value(self):
        """ 值为空、空字符串、0的场景 """
        params: HttpParams = {
            'Foo': None,  # 转换为空字符串
            'Bar': '',  # 保持空字符串
            'Page': 0,  # 转换为字符串"0"，而不是空字符串
        }
        actual = make_canonical_query_string(params)
        assert 'Bar=&Foo=&Page=0' == actual

    def test_bce_demo(self):
        # 参照百度智能云文档的示例，确保实现符合文档预期
        # https://cloud.baidu.com/doc/Reference/s/njwvz1yfu#3-canonicalquerystring
        params: HttpParams = {
            'text': None,
            'text1': '测试',
            'text10': 'test',
        }
        actual = make_canonical_query_string(params)
        expect = 'text10=test&text1=%E6%B5%8B%E8%AF%95&text='
        assert expect == actual
