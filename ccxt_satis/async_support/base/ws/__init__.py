# -*- coding: utf-8 -*-

from ccxt_satis.base import errors

# -----------------------------------------------------------------------------

from ccxt_satis.base import decimal_to_precision

from ccxt_satis import BaseError                  # noqa: F401
from ccxt_satis import ExchangeError              # noqa: F401
from ccxt_satis import NotSupported               # noqa: F401
from ccxt_satis import AuthenticationError        # noqa: F401
from ccxt_satis import PermissionDenied           # noqa: F401
from ccxt_satis import AccountSuspended           # noqa: F401
from ccxt_satis import InvalidNonce               # noqa: F401
from ccxt_satis import InsufficientFunds          # noqa: F401
from ccxt_satis import InvalidOrder               # noqa: F401
from ccxt_satis import OrderNotFound              # noqa: F401
from ccxt_satis import OrderNotCached             # noqa: F401
from ccxt_satis import DuplicateOrderId           # noqa: F401
from ccxt_satis import CancelPending              # noqa: F401
from ccxt_satis import NetworkError               # noqa: F401
from ccxt_satis import DDoSProtection             # noqa: F401
from ccxt_satis import RateLimitExceeded          # noqa: F401
from ccxt_satis import RequestTimeout             # noqa: F401
from ccxt_satis import ExchangeNotAvailable       # noqa: F401
from ccxt_satis import OnMaintenance              # noqa: F401
from ccxt_satis import InvalidAddress             # noqa: F401
from ccxt_satis import AddressPending             # noqa: F401
from ccxt_satis import ArgumentsRequired          # noqa: F401
from ccxt_satis import BadRequest                 # noqa: F401
from ccxt_satis import BadResponse                # noqa: F401
from ccxt_satis import NullResponse               # noqa: F401
from ccxt_satis import OrderImmediatelyFillable   # noqa: F401
from ccxt_satis import OrderNotFillable           # noqa: F401


__all__ = decimal_to_precision.__all__ + errors.__all__  # noqa: F405
