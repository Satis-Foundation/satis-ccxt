# -*- coding: utf-8 -*-

from ccxt_satis.async_support.base.exchange import Exchange
from ccxt_satis.abstract.satis import ImplicitAPI
from ccxt_satis.base.types import OrderSide
from ccxt_satis.base.types import OrderType
from typing import Optional
from ccxt_satis.base.errors import BadRequest
from ccxt_satis.base.errors import InvalidOrder
from ccxt_satis.base.errors import OrderNotFound
from ccxt_satis.base.decimal_to_precision import TRUNCATE
from ccxt_satis.base.decimal_to_precision import DECIMAL_PLACES
from ccxt_satis.base.precise import Precise


class satis(Exchange, ImplicitAPI):

    def describe(self):
        return self.deep_extend(super(satis, self).describe(), {
            'id': 'satis',
            'name': 'Sat.is',
            'countries': [],
            'version': 'v2',
            'userAgent': None,
            'rateLimit': 30,
            'pro': True,
            'has': {
                'CORS': True,
                'spot': False,
                'margin': True,
                'swap': True,
                'future': False,
                'option': False,
                # 'addMargin': False,
                'cancelOrder': True,
                # 'cancelOrders': True,
                # 'createLimitBuyOrder': True,
                # 'createLimitSellOrder': True,
                # 'createMarketBuyOrder': True,
                # 'createMarketSellOrder': True,
                'createOrder': True,
                # 'createPostOnlyOrder': True,
                # 'createReduceOnlyOrder': False,
                # 'createStopLimitOrder': True,
                # 'createStopMarketOrder': False,
                # 'createStopOrder': True,
                'fetchAccounts': True,
                'fetchBalance': True,
                'fetchClosedOrders': True,
                'fetchCurrencies': True,
                'setCrossMargin': True,
                'fetchMarkets': True,
                'fetchMyTrades': True,
                'fetchOHLCV': True,
                'fetchOrder': True,
                'fetchOrderBook': True,
                'fetchOrders': True,
                'fetchPosition': False,
                'fetchTicker': True,
                'fetchTickers': False,
                'fetchTime': True,
                'fetchTrades': True,
                'reduceMargin': True,
                'setLeverage': True,
                'setRiskLimit': True,
                # 'withdraw': None,
            },
            'timeframes': {
                '1m': 60,
                '5m': 300,
                '15m': 900,
                '1h': 3600,
                '6h': 21600,
                '1d': 86400,
            },
            'urls': {
                'logo': 'https://static.sat.is/logo/Satis_Logo_white.png',
                'api': {
                    'rest': 'https://api.sat.is/api',
                },
                'doc': 'https://api-doc.sat.is',
            },
            'api': {
                'public': {
                    'get': [
                        'currencies',
                        'products',
                        'products/{product_id}/book',
                        'products/{product_id}/long_short_ratio',
                        'products/{product_id}/open_interest',
                        'products/{product_id}/ticker',
                        'products/{product_id}/trades',
                        'products/{product_id}/candles',
                        'products/{product_id}/stats',
                        'indices',
                        'time',
                    ],
                },
                'private': {
                    'get': [
                        'accounts',
                        'accounts/{account_id}',
                        'accounts/{account_id}/ledger',
                        'accounts/{account_id}/holds',
                        'fees',
                        'fills',
                        'orders',
                        'orders/{order_id}',
                        'positions/{product_id}',
                    ],
                    'post': [
                        'orders',
                        'positions/cross',
                        'positions/isolate',
                        'positions/margin',
                        'positions/risk',
                    ],
                    'delete': [
                        'orders',
                        'orders/{order_id}',
                    ],
                },
            },
            'fees': {
                'trading': {
                    'percentage': True,
                    'maker': self.parse_number('0.0002'),
                    'taker': self.parse_number('0.0007'),
                },
                'precisionMode': DECIMAL_PLACES,
            },
            'requiredCredentials': {
                'privateKey': True,
                'apiKey': False,
                'secret': False,
            }, })

    async def fetch_time(self, params={}):
        response = self.publicGetTime(params)
        return self.safe_timestamp(response, 'epoch')

    async def fetch_currencies(self, params={}):
        response = await self.publicGetCurrencies(params)
        result = {}
        for i in range(0, len(response)):
            currency = response[i]
            id = self.safe_string(currency, 'id')
            name = self.safe_string(currency, 'name')
            min_size = self.safe_string(currency, 'min_size')
            code = self.safe_currency_code(id)
            result[code] = {
                'id': id,
                'code': code,
                'info': currency,
                'name': name,
                'active': True,
                'fee': None,
                'precision': self.precision_from_string(min_size),
                'withdraw': None,
                'deposit': None,
                'networks': None,
                'limits': {
                    'amount': {
                        'min': self.safe_number(currency, 'min_size'),
                        'max': None,
                    },
                    'withdraw': {
                        'min': None,
                        'max': None,
                    },
                },
            }
        return result

    async def fetch_markets(self, params={}):
        response = await self.publicGetProduct(params)
        result = []
        for i in range(0, len(response)):
            market = response[i]
            id = self.safe_string(market, 'id')
            baseId = self.safe_string(market, 'base_currency')
            base = self.safe_currency_code(baseId)
            quoteId = self.safe_string(market, 'quote_currency')
            quote = self.safe_currency_code(quoteId)
            symbol = base + '/' + quote
            active = self.safe_string(market, 'status') == 'online'
            contractSize = self.safe_float(market, 'quote_increment')
            limits_price_min = self.safe_float(market, 'min_price')
            limits_price_max = self.safe_float(market, 'max_price')
            inverse = market['is_inverse']
            fees = self.safeValue(self.fees, 'trading')
            precision_amount = self.precision_from_string(self.safe_string(market, 'base_min_size'))
            precision_price = self.precision_from_string(self.safe_string(market, 'quote_increment'))
            max_amount = self.safe_float(market, 'base_max_size')
            min_amount = self.safe_float(market, 'base_min_size')

            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'baseId': baseId,
                'quoteId': quoteId,
                'active': active,
                'type': 'swap',
                'spot': False,
                'margin': True,
                'future': False,
                'swap': True,
                'option': False,
                'contract': True,
                'settle': quote,
                'settleId': quoteId,
                'contractSize': contractSize,
                'linear': not inverse,
                'inverse': inverse,
                'expiry': None,
                'expiryDatetime': None,
                'strike': None,
                'optionType': None,
                'taker': self.safe_float(fees, 'taker'),
                'maker': self.safe_float(fees, 'maker'),
                'percentage': True,
                'tierBased': False,
                'feeSide': None,  # TODO check
                'precision': {
                    'amount': precision_amount,
                    'price': precision_price,
                },
                'limits': {
                    'amount': {
                        'min': min_amount,
                        'max': max_amount,
                    },
                    'price': {
                        'min': limits_price_min,
                        'max': limits_price_max,
                    },
                    'cost': {
                        'min': None,
                        'max': None,
                    },
                    'leverage': {
                        'min': None,
                        'max': None,
                    }
                },
                'info': market,
            })
        return result

    async def fetch_accounts(self, params={}):
        await self.load_markets()
        response = await self.privateGetAccounts(params)
        return self.parse_accounts(response, params)

    def parse_account(self, account):
        currencyId = self.safe_string(account, 'currency')
        return {
            'id': self.safe_string(account, 'id'),
            'type': "swap",
            'code': self.safe_currency_code(currencyId),
            'name': None,
            'info': account,
        }

    async def fetch_ticker(self, symbol: str, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'product_id': market['id'],
        }
        response = await self.publicGetTicker(self.extend(request, params))
        return self.parse_ticker(response, market)

    def parse_ticker(self, ticker, market=None):

        timestamp = self.parse8601(self.safe_string(ticker, 'time'))
        marketId = self.safe_string(ticker, 'product_id')
        last = self.safe_string(ticker, 'price')
        open = self.safe_string(ticker, 'open_24h')
        change = Precise.string_sub(last, open)
        precentage = Precise.string_div(change, open)
        average = Precise.string_add(open, last)
        average = Precise.string_div(average, '2')

        return self.safe_ticker({
            'symbol': self.safe_symbol(marketId, market),
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': self.safe_string(ticker, 'high_24h'),
            'low': self.safe_string(ticker, 'low_24h'),
            'bid': self.safe_string(ticker, 'best_bid'),
            'bidVolume': None,
            'ask': self.safe_string(ticker, 'best_ask'),
            'askVolume': None,
            'vwap': None,
            'open': open,
            'close': last,
            'last': last,
            'previousClose': None,
            'change': change,
            'percentage': Precise.string_mul(precentage, '100'),
            'average': average,
            'baseVolume': self.safe_string(ticker, 'volume_24h'),
            'quoteVolume': None,
            'info': ticker,
        }, market)

    async def fetch_order_book(self, symbol: str, limit: Optional[int] = None, params={}):
        """
        TODO: test limit
        """
        await self.load_markets()

        market = self.market(symbol)
        request = {
            'product_id': market['id'],
            'level': 2,
        }
        response = await self.publicGetOrderBook(
            self.extend(request, params))

        if limit and isinstance(limit, int):
            order_book = {}
            for side in ('bids', 'asks'):
                temp_book = self.safe_value(response, side, [])
                order_book[side] = temp_book[:limit]
        else:
            order_book = response
        return self.parse_order_book(order_book, symbol)

    async def fetch_ohlcv(self, symbol: str, timeframe='1m', since: Optional[int] = None, limit: Optional[int] = None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        end = str(self.seconds())

        defaultLimit = 1500
        maxLimit = 1500
        limit = defaultLimit if (limit is None) else min(limit, maxLimit)
        request = {
            'product_id': market['id'],
            'granularity': self.safe_string(self.timeframes, timeframe, '60'),
            'end': end,
        }
        if since is not None:
            sinceString = str(since)
            timeframeToSeconds = Precise.string_div(sinceString, '1000')
            request['start'] = self.decimal_to_precision(timeframeToSeconds, TRUNCATE, 0, DECIMAL_PLACES)
        else:
            request['start'] = Precise.string_sub(end, '18000')  # default to 5h in seconds, max 300 candles

        request['start'] = self.iso8601(int(request['start']) * 1000)
        request['end'] = self.iso8601(int(request['end']) * 1000)
        response = await self.publicGetCandles(
            self.extend(request, params))
        for i in range(0, len(response)):
            response[i][0] = self.safe_integer(response[i], 0) * 1000

        return self.parse_ohlcvs(response, market, timeframe, since, limit)

    async def fetch_trades(self, symbol: str, since: Optional[int] = None, limit: Optional[int] = None, params={}):
        await self.load_markets()
        market = self.market(symbol)

        request = {
            'product_id': market['id'],
        }

        if limit is not None:
            request['limit'] = limit

        if since is not None:
            request['start'] = self.iso8601(since)

        trades = await self.publicGetTrades(
            self.extend(request, params))
        return self.parse_trades(trades, None, since, limit, params={'symbol': symbol})

    async def fetch_my_trades(self, symbol: Optional[str] = None, since: Optional[int] = None, limit: Optional[int] = None, params={}):
        await self.load_markets()
        market = None
        if symbol is not None:
            market = self.market(symbol)
        request = {}
        if market is not None:
            request['product_id'] = market['id']
        if limit is not None:
            request['limit'] = limit
        if since is not None:
            request['start'] = self.iso8601(since)
        trades = await self.privateGetFills(self.extend(request, params))
        return self.parse_trades(trades, market, since, limit)

    def parse_trade(self, trade, market=None):
        id = self.safe_string(trade, 'trade_id')

        marketId = self.safe_string(trade, 'product_id')
        symbol = self.safe_symbol(marketId, market)

        orderId = self.safe_string(trade, 'order_id')
        timestamp = self.parse8601(
            self.safe_string_2(trade, 'created_at', 'time'))

        amount = self.safe_float(trade, 'size')
        price = self.safe_float(trade, 'price')
        side = self.safe_string(trade, 'side')
        type = self.safe_string(trade, 'type')

        result = {
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'id': id,
            'order': orderId,
            'type': type,
            'side': side,
            'price': price,
            'amount': amount,
        }

        liquidity = self.safe_string(trade, 'liquidity')
        if 'liquidity' in trade:
            if liquidity == 'T':
                takerOrMaker = 'taker'
            elif liquidity == 'M':
                takerOrMaker = 'maker'
            else:
                takerOrMaker = None
            result['takerOrMaker'] = takerOrMaker
        else:
            result['takerOrMaker'] = None

        if 'fee' in trade:
            symbol = self.market(symbol)
            cost = self.safe_string(trade, 'fee')
            currency = symbol['settle']
            rate = self.safe_string(symbol, result['takerOrMaker'])
            result['fee'] = {
                'cost': cost,
                'currency': currency,
                'rate': rate,
            }
        return self.safe_trade(result, market)

    async def fetch_balance(self, params={}):
        await self.load_markets()
        response = await self.privateGetAccounts(params)
        return self.parse_balance(response)

    def parse_balance(self, response):
        result = {'info': response}
        for i in range(0, len(response)):
            balance = response[i]
            currencyId = self.safe_string(balance, 'currency')
            code = self.safe_currency_code(currencyId)
            account = self.account()
            free = self.safe_number(balance, 'free')
            total = self.safe_number(balance, 'balance')
            account['free'] = free
            account['total'] = total
            result[code] = account
        return self.safe_balance(result)

    async def fetch_order(self, id: str, symbol: Optional[str] = None, params={}):
        request = {
            'order_id': id,
        }
        response = await self.privateGetOrder(self.extend(request, params))
        return self.parse_order(response)

    async def fetch_orders(self, symbol: Optional[str] = None, since: Optional[int] = None, limit=100, params={}):
        await self.load_markets()
        market = None
        if symbol is not None:
            market = self.market(symbol)
        request = {}
        if market is not None:
            request['product_id'] = market['id']
        if limit is not None:
            request['limit'] = limit
        if since is not None:
            request['start'] = self.iso8601(since)
        response = await self.privateGetOrders(self.extend(request, params))
        return self.parse_orders(response, market, since, limit)

    async def fetch_orders_by_status(self, status, symbol: Optional[str] = None, since: Optional[int] = None, limit: Optional[int] = None, params={}):
        await self.load_markets()
        market = None
        if symbol is not None:
            market = self.market(symbol)
        request = {
            'status': status,
        }
        if market is not None:
            request['product_id'] = market['id']
        if limit is not None:
            request['limit'] = limit
        if since is not None:
            request['start'] = self.iso8601(since)
        response = await self.privateGetOrders(self.extend(request, params))
        return self.parse_orders(response, market, since, limit)

    async def fetch_open_orders(self, symbol: Optional[str] = None, since: Optional[int] = None, limit: Optional[int] = None, params={}):
        return self.fetch_orders_by_status('open', symbol, since, limit, params)

    async def fetch_closed_orders(self, symbol: Optional[str] = None, since: Optional[int] = None, limit: Optional[int] = None, params={}):
        return self.fetch_orders_by_status('done', symbol, since, limit, params)

    def parse_order_status(self, status, reason=None):
        if not reason:
            done_status = 'closed'
        elif reason == 'Canceled':
            done_status = 'canceled'
        else:
            done_status = 'rejected'

        statuses = {
            'pending': 'open',
            'received': 'open',
            'open': 'open',
            'done': done_status,
        }
        return self.safe_string(statuses, status, status)

    def parse_order(self, order, market=None):
        marketId = self.safe_string(order, 'product_id')
        symbol = self.safe_symbol(marketId)
        if symbol is not None:
            market = self.market(symbol)

        id = self.safe_string(order, 'id')
        timestamp = self.parse8601(self.safe_string(order, 'created_at'))
        status = self.parse_order_status(self.safe_string(
            order, 'status'), self.safe_string(order, 'reason'))

        amount = self.safe_string(order, 'size')
        filled = self.safe_string(order, 'filled_size')
        remaining = Precise.string_sub(amount, filled)

        side = self.safe_string(order, 'side')
        type = self.safe_string(order, 'type')

        price = self.safe_string(order, 'price')
        timeInForce = self.safe_string(order, 'time_in_force')
        if timeInForce:
            timeInForce = timeInForce.upper()
        postOnly = self.safe_value(order, 'post_only')
        if postOnly:
            timeInForce = 'PO'

        executed_value = self.safe_string(order, 'executed_value', 0)
        average = Precise.string_div(executed_value, filled)

        return self.safe_order({
            'id': id,
            'clientOrderId': None,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'lastTradeTimestamp': None,
            'status': status,
            'symbol': symbol,
            'type': type,
            'timeInForce': timeInForce,
            'side': side,
            'price': price,
            'average': average,
            'amount': amount,
            'filled': filled,
            'remaining': remaining,
            'cost': executed_value,
            'trades': None,
            'fee': None,
            'info': order,
        }, market)

    async def create_order(self, symbol: str, type: OrderType, side: OrderSide, amount, price=None, params={}):
        await self.load_markets()
        market = self.market(symbol)

        request = {
            'product_id': market['id'],
            'side': side,  # "buy" or "sell"
            'type': type,  # "limit", "market", "stop", "trailingStop", or "takeProfit"
            'size': float(self.amount_to_precision(symbol, amount)),
        }
        if type == 'limit':
            request['price'] = float(self.price_to_precision(symbol, price))
        elif type == 'market':
            request['price'] = None
        else:
            raise InvalidOrder(
                self.id + ' createOrder() does not support order type ' + type + ', only limit, market orders are supported')

        timeInForce = self.safe_string(params, 'timeInForce')
        postOnly = True if (timeInForce == 'PO') else self.safe_value_2(params, 'postOnly', 'post_only', False)

        if timeInForce:
            if timeInForce not in ['GTC', 'IOC', 'FOK', 'PO']:
                raise InvalidOrder(
                    self.id + ' createOrder() does not support time in force ' + timeInForce + ', only GTC, IOC, FOK are supported')
            elif timeInForce in ['GTC', 'IOC', 'FOK']:
                request['time_in_force'] = timeInForce.lower()

        if postOnly:
            request['post_only'] = postOnly
        response = await self.privatePostOrder(self.extend(request, params))

        return self.parse_order(response)

    async def cancel_order(self, id: str, symbol: Optional[str] = None, params={}):
        await self.load_markets()
        request = {
            'order_id': id,
        }

        response = await self.privateDeleteOrder(self.extend(request, params))
        if not response:
            raise OrderNotFound(self.id + ' cancelOrder() error: ' + id)
        order = await self.privateGetOrder(request)
        return self.parse_order(order)

    def parse_position(self, position):
        marketId = self.safe_string(position, 'product_id')
        symbol = self.safe_symbol(marketId)
        timestamp = self.parse8601(self.safe_string(position, 'timestamp'))
        isolated = not self.safe_value(position, 'cross_margin')
        contracts = self.safe_string(position, 'current_size')
        if Precise.string_gt(contracts, '0'):
            side = 'long'
        elif Precise.string_lt(contracts, '0'):
            side = 'short'
        else:
            side = None
        entry_price = self.safe_string(position, 'avg_entry_price')
        mark_price = self.safe_string(position, 'mark_price')
        notional = Precise.string_mul(contracts, entry_price)
        leverage = self.safe_string(position, 'leverage')
        collateral = self.safe_string(position, 'pos_margin')
        initialMargin = self.safe_string(position, 'pos_margin')
        maintenanceMargin = self.safe_string(position, 'pos_margin')
        initialMarginPercentage = self.safe_string(position, 'init_margin_req')
        maintenanceMarginPercentage = self.safe_string(position, 'maint_margin_req')
        unrealizedPnl = self.safe_string(position, 'unrealised_pnl')
        liquidationPrice = self.safe_string(position, 'liquidation_price')
        marginMode = 'isolated' if isolated else 'cross'
        percentage = Precise.string_div(unrealizedPnl, initialMargin)
        percentage = Precise.string_mul(percentage, '100')

        return self.safe_position({
            'id': None,
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'isolated': isolated,
            'hedged': None,
            'side': side,
            'contracts': contracts,
            'entry_price': entry_price,
            'mark_price': mark_price,
            'notional': notional,
            'leverage': leverage,
            'collateral': collateral,
            'initialMargin': initialMargin,
            'maintenanceMargin': maintenanceMargin,
            'initialMarginPercentage': initialMarginPercentage,
            'maintenanceMarginPercentage': maintenanceMarginPercentage,
            'unrealizedPnl': unrealizedPnl,
            'liquidationPrice': liquidationPrice,
            'percentage': percentage,
            'marginMode': marginMode,
            'info': position,
        })

    async def fetch_position(self, symbol: str, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'product_id': market['id'],
        }
        response = await self.privateGetPosition(
            self.extend(request, params))
        return self.parse_position(response)

    async def edit_margin(self, symbol: str, amount: str, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'product_id': market['id'],
            'margin': float(self.amount_to_precision(symbol, amount)),
        }
        response = await self.privatePostPositionMargin(
            self.extend(request, params))
        return self.parse_position(response)

    async def add_margin(self, symbol: str, amount: str, params={}):
        return await self.edit_margin(symbol, amount, params)

    async def reduce_margin(self, symbol: str, amount: str, params={}):
        amount = float(amount) * -1
        return await self.edit_margin(symbol, amount, params)

    async def set_leverage(self, symbol: str, leverage: int, params={}):
        await self.load_markets()
        if leverage < 1 or leverage > 100:
            raise BadRequest(self.id + ' leverage should be between 1 and 100')
        if not isinstance(leverage, int):
            raise BadRequest(self.id + ' leverage should be an integer')
        market = self.market(symbol)
        request = {
            'product_id': market['id'],
            'leverage': leverage,
        }
        response = await self.privatePostPositionIsolate(
            self.extend(request, params))
        return self.parse_position(response)
    
    async def set_risk_limit(self, symbol: str, risk_limit: float, params={}):
        await self.load_markets()
        market = self.market(symbol)
        risk_limit = self.currency_to_precision(market['settle'], risk_limit)
        
        request = {
            'product_id': market['id'],
            'limit': float(risk_limit),
        }
        response = await self.privatePostPositionRisk(
            self.extend(request, params))
        return self.parse_position(response)

    async def set_cross_margin(self, symbol: str, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'product_id': market['id'],
        }
        response = await self.privatePostPositionCross(
            self.extend(request, params))
        return self.parse_position(response)

    def sign_message(self, message, params={}):
        hash = self.hash(self.encode(
            "\x19Ethereum Signed Message:\n" + str(len(message)) + message), 'keccak')
        signature = self.ecdsa(
            hash[-64:], self.privateKey[-64:], algorithm="secp256k1")
        signature = '0x' + signature['r'] + \
            signature['s'] + hex(int(signature['v'] + 27))[2:]
        return signature

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        query = '/api/' + self.implode_params(path, params)
        params = self.omit(params, self.extract_params(path))

        if method == 'GET':
            if params:
                query += '?' + self.urlencode(params)

        url = self.urls['api']['rest'] + query
        if api == 'private':
            self.check_required_credentials()

            nonce = str(self.nonce())
            payload = ''
            if method != 'GET':
                if params:
                    body = self.json(params)
                    payload = body

            auth = nonce + method + query + payload
            signature = self.sign_message(auth)
            headers = {
                'ACCESS-SIGN': signature,
                'ACCESS-TIMESTAMP': nonce,
                'Content-Type': 'application/json',
            }
        return {'url': url, 'method': method, 'body': body, 'headers': headers}
