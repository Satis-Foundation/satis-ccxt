# -*- coding: utf-8 -*-

"""CCXT: CryptoCurrency eXchange Trading Library (Async)"""

# ----------------------------------------------------------------------------

__version__ = '3.1.54'

# ----------------------------------------------------------------------------

from ccxt_satis.async_support.base.exchange import Exchange  # noqa: F401

# CCXT Pro exchanges (now this is mainly used for importing exchanges in WS tests)

from ccxt_satis.pro.satis import satis

exchanges = [
    'satis',
]
