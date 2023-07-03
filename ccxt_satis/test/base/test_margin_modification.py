import os
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(root)

# ----------------------------------------------------------------------------

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

# ----------------------------------------------------------------------------
# -*- coding: utf-8 -*-


from ccxt.test.base import test_shared_methods  # noqa E402


def test_margin_modification(exchange, skipped_properties, method, entry):
    format = {
        'info': {},
        'type': 'add',
        'amount': exchange.parse_number('0.1'),
        'total': exchange.parse_number('0.29934828'),
        'code': 'USDT',
        'symbol': 'ADA/USDT:USDT',
        'status': 'ok',
    }
    empty_allowed_for = ['status', 'symbol', 'code', 'total', 'amount']
    test_shared_methods.assert_structure(exchange, skipped_properties, method, entry, format, empty_allowed_for)
    test_shared_methods.assert_currency_code(exchange, skipped_properties, method, entry, entry['code'])
    #
    test_shared_methods.assert_greater_or_equal(exchange, skipped_properties, method, entry, 'amount', '0')
    test_shared_methods.assert_greater_or_equal(exchange, skipped_properties, method, entry, 'total', '0')
    test_shared_methods.assert_in_array(exchange, skipped_properties, method, entry, 'type', ['add', 'reduce', 'set'])
    test_shared_methods.assert_in_array(exchange, skipped_properties, method, entry, 'status', ['ok', 'pending', 'canceled', 'failed'])
    test_shared_methods.assert_symbol(exchange, skipped_properties, method, entry, 'symbol')