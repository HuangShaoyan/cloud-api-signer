from cloud_api_signer.models import HttpParams
from cloud_api_signer.utils import (
    make_canonical_query_string_bce,
    make_canonical_query_string_volc,
)


class TestMakeCanonicalQueryString:
    def test_empty_param(self):
        actual = make_canonical_query_string_bce({})
        assert '' == actual

    def test_order_by_keyvalue(self):
        """按照 "key=value" 的字典序进行排序"""
        params: HttpParams = {
            'text1': 'a',
            'text9': 'b',
            'text10': 'c',
        }
        actual = make_canonical_query_string_bce(params)
        expect = 'text10=c&text1=a&text9=b'
        assert expect == actual

    def test_url_encode(self):
        """参数名称和值，都要进行 url 编码"""
        params: HttpParams = {
            'Foo=100': '1&2',
            'bar/a': 'abc/def',
        }
        actual = make_canonical_query_string_bce(params)
        assert 'Foo%3D100=1%262&bar%2Fa=abc%2Fdef' == actual

    def test_special_value(self):
        """值为空、空字符串、0的场景"""
        params: HttpParams = {
            'Foo': None,  # 转换为空字符串
            'Bar': '',  # 保持空字符串
            'Page': 0,  # 转换为字符串"0"，而不是空字符串
        }
        actual = make_canonical_query_string_bce(params)
        assert 'Bar=&Foo=&Page=0' == actual

    def test_bce_demo(self):
        # 参照百度智能云文档的示例，确保实现符合文档预期
        # https://cloud.baidu.com/doc/Reference/s/njwvz1yfu#3-canonicalquerystring
        params: HttpParams = {
            'text': None,
            'text1': '测试',
            'text10': 'test',
        }
        actual = make_canonical_query_string_bce(params)
        expect = 'text10=test&text1=%E6%B5%8B%E8%AF%95&text='
        assert expect == actual


class TestMakeCanonicalQueryStringVolc:
    def test_empty_param(self):
        actual = make_canonical_query_string_volc({})
        assert '' == actual

    def test_order_by_key(self):
        """按照参数名的字典序进行排序"""
        params: HttpParams = {
            'text1': 'a',
            'text9': 'b',
            'text10': 'c',
        }
        actual = make_canonical_query_string_volc(params)
        expect = 'text1=a&text10=c&text9=b'
        assert expect == actual

    def test_url_encode(self):
        """参数名称和值，都要进行 url 编码"""
        params: HttpParams = {
            'Foo=100': '1&2',
            'bar/a': 'abc/def',
        }
        actual = make_canonical_query_string_volc(params)
        assert 'Foo%3D100=1%262&bar%2Fa=abc%2Fdef' == actual

    def test_special_value(self):
        """值为空、空字符串、0的场景"""
        params: HttpParams = {
            'Foo': None,  # 转换为空字符串
            'Bar': '',  # 保持空字符串
            'Page': 0,  # 转换为字符串"0"，而不是空字符串
        }
        actual = make_canonical_query_string_volc(params)
        assert 'Bar=&Foo=&Page=0' == actual
