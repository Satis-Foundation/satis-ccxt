from ccxt_satis.base.errors import ArgumentsRequired
from ccxt_satis.base.errors import AuthenticationError
from ccxt_satis.base.errors import BadSymbol
from ccxt_satis.base.errors import ExchangeError
from ccxt_satis.base.errors import ExchangeNotAvailable
from ccxt_satis.base.errors import InvalidOrder
from ccxt_satis.base.errors import NetworkError
from ccxt_satis.base.exchange import Exchange
from ccxt_satis.base.precise import Precise


class satisex(Exchange): 
    def describe(self):
        return self.deep_extend(super(satisex, self).describe(), {
            'id': 'sat', 
            'name': 'SatisEX', 
            'countries': ['SC'],  # Seychelles 
            'rateLimit': 30,  # 30 requests per second
            'timeout': 30000,  # 30 sec
            'version': 'v1',  
            'userAgent': self.userAgents['chrome'],
            'has': {
                'CORS': False,
                'cancelAllOrders': True,
                'cancelOrder': True,
                'createOrder': True,
                'editLeverage': True,
                'editMarginAdd': True,
                'editMarginRemove': True,
                'editRiskLimit': True,
                'fetchBalance': True,
                'fetchClosedOrders': True,
                'fetchCurrencies': True,
                'fetchDepositAddress': False,  
                'fetchDeposits': False,
                'fetchLedger': True,
                'fetchMarkets': True,
                'fetchMyTrades': True,
                'fetchOHLCV': True,
                'fetchOpenOrders': True,
                'fetchOrder': True,
                'fetchOrders': True,
                'fetchOrderBook': True,
                'fetchPosition': True,
                'fetchTicker': True,
                'fetchTickers': False,
                'fetchTime': True,
                'fetchTrades': True,
                'fetchTradingFees': False,
                'fetchTransactions': False,
                'fetchWithdrawals': False,
                'setCrossMarginMode': False,
                'withdraw': False,
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
                'api': 'http://3.15.216.104',
                'doc': 'https://sandbox-api-doc.sat.is/#testnet-endpoint',
            },
            'requiredCredentials': {
                'apiKey': False,
                'secret': False,
                'privateKey': True,
            },
            'api': {
                'public': {
                    'get': [
                        'currencies',
                        'products',
                        'products/{product_id}/book',
                        'products/{product_id}/ticker',
                        'products/{product_id}/trades',
                        'products/{product_id}/candles',
                        'time',
                    ],
                },
                'private': {
                    'get': [
                        'accounts',
                        'accounts/{account_id}',
                        'accounts/{account_id}/ledger',
                        'fees',
                        'fills',
                        'orders',
                        'orders/{order_id}',
                        'positions/{product_id}',
                        'users/deposits',
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
                    'taker':  self.parse_number('0.0007'),
                },
            },
        })

    def to_wei_by_code(self, amount, code):
        precision = self.currencies[code]['precision']
        return amount

    def from_wei_by_code(self, amount, code):
        precision = self.currencies[code]['precision']
        return amount

    def get_market_params(self, symbol, key, params={}):
        market = None
        marketId = None
        if symbol in self.markets:
            market = self.market(symbol)
            marketId = market['id']
        else:
            marketId = self.safe_string(params, key, symbol)
        return [market, marketId]

    def check_symbol_request(self, symbol, params={}):
        self.load_markets()

        if symbol is None:
            raise ArgumentsRequired(
                self.id + ' method requires a symbol parameter')
        elif symbol not in self.markets:
            raise BadSymbol(self.id + ' does not have market symbol ' + symbol)
        else:
            market, marketId = self.get_market_params(
                symbol, 'market_name', params)
            return market, marketId

    def fetch_time(self, params={}):
        response = self.publicGetTime(params)
#         {
#             "iso": "2023-02-19T19:17:37.793106+00:00",
#             "epoch": 1676834257.793106
#         }
        return self.safe_timestamp(response, 'epoch')

    def fetch_accounts(self, params={}):
        self.load_markets()
        response = self.privateGetAccounts()

        # [
        #     {
        #         "id": 412,
        #         "currency": "usdt",
        #         "balance": 90000000,
        #         "free": 90000000,
        #         "hold": 0,
        #         "update_time": "2023-02-19T18:18:57.727862+00:00",
        #         "global_asset": 0,
        #         "local_asset": {
        #             "zksync": "30000000",
        #             "polygon": "30000000",
        #             "arbitrum": "30000000"
        #         },
        #         "mobile_asset": {
        #             "zksync": "0",
        #             "polygon": "0",
        #             "arbitrum": "0"
        #         }
        #     },
        # ]

        result = []
        for i in range(0, len(response)):
            account = response[i]
            currencyId = self.safe_string(account, 'currency')
            code = self.safe_currency_code(currencyId)
            result.append({
                'info': account,
                'id': self.safe_string(account, 'id'),
                'code': code,
            })
        return result

    def fetch_deposit_address(self, code, params={}):
        self.load_markets()

        response = self.private_get_users_deposits()
        # [
        #     {
        #         "address": "tb1q90z8xs3dq7exl8r3svmmtrc38ver2jlpatqknx",
        #         "asset": "btc",
        #         "svg": "svg file"
        #     },
        #     {
        #         "address": "tb1qx0ksh3gyyr7hsu9egg59s7ydcw9p8mdnj5t6e0",a
        #         "asset": "eth",
        #         "svg":  "svg file"
        #     }
        # ]

        currencyID = self.currency(code)['id']
        result = self.filter_by(response, 'asset', currencyID)[0]

        address = self.safe_string(result, 'address')
        address
        return {
            'currency': code,
            'address': address,
            'tag': None,
            'info': response,
        }

    def fetch_order_book(self, symbol, limit=None, params={}):
        self.load_markets()
        market, marketId = self.get_market_params(
            symbol, 'market_name', params)

        request = {
            'product_id': marketId,
            'level': 2,
        }
        response = self.publicGetProductsProductIdBook(
            self.extend(request, params))
        # {
        #     "asks": [
        #         [
        #             "4000.6", # price: float
        #             10,      # size: int
        #             1        # no. of orders: int
        #         ],
        #         ...
        #     ],
        #     "bids": [
        #         [
        #             "40000.2", # price
        #             2,       # size
        #             2        # no. of orders
        #         ],
        #         ...
        #     ]
        # }

        if limit and isinstance(limit, int):
            order_book = {}
            for side in ('bids', 'asks'):
                temp_book = self.safe_value(response, side, [])
                order_book[side] = temp_book[:limit]
        else:
            order_book = response
        return self.parse_order_book(order_book, symbol)

    def parse_order_book(self, orderbook, symbol, timestamp=None, bids_key='bids', asks_key='asks', price_key=0,
                         amount_key=1):
        return {
            'symbol': symbol,
            'bids': self.sort_by(self.parse_bids_asks(orderbook[bids_key], price_key, amount_key) if (
                bids_key in orderbook) and isinstance(
                orderbook[bids_key], list) else [], 0, True),
            'asks': self.sort_by(self.parse_bids_asks(orderbook[asks_key], price_key, amount_key) if (
                asks_key in orderbook) and isinstance(
                orderbook[asks_key], list) else [], 0),
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp) if timestamp is not None else None,
            'nonce': None,
        }

    def fetch_markets(self, params={}):
        response = self.public_get_products()
        # [
        #     {
        #         "base_currency": "btc",
        #         "base_max_size": 10000000,
        #         "base_min_size": 1,
        #         "display_name": "btc-usd",
        #         "funding_rate": "0.0",
        #         "id": "btc_usd",
        #         "init_margin": "0.01",
        #         "is_inverse": true,
        #         "is_quanto": false,
        #         "maint_margin": "0.005",
        #         "max_price": "1000000.0",
        #         "multiplier": -1,
        #         "next_funding_time": "2021-07-09T06:00:00.000000+00:00",
        #         "predicted_funding_rate": "0",
        #         "quote_currency": "usd",
        #         "quote_increment": "0.1",
        #         "risk_base_size": 20000000000,
        #         "risk_step_size": 5000000000,
        #         "settle_currency": "btc",
        #         "status": "online",
        #         "status_message": "",
        #         "trading_disabled": false
        #     },
        # ]
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
            limits_price_min = self.safe_float(market, 'quote_increment')
            limits_price_max = self.safe_float(market, 'max_price')
            inverse = market['is_inverse']
            fees = self.fees

            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'baseId': baseId,
                'quoteId': quoteId,
                'active': active,
                'type': 'swap',
                'spot':     False,
                'margin':   True,
                'future':   False,
                'swap':     True,
                'option':   False,
                'contract': True,
                'settle':   quote,
                'settleId': quoteId,
                'contractSize': 1,
                'linear': not inverse,
                'inverse':  inverse,
                'expiryDatetime': None,
                'strike': None,
                'optionType': None,
                'taker': fees['trading']['taker'],
                'maker': fees['trading']['maker'],
                'percentage': True,
                'tierBased': False,
                'precision': {
                    'amount': 0,
                    'price': 1,
                },
                'limits': {
                    'amount': {
                        'min': 1,
                        'max': None,
                    },
                    'price': {
                        'min': limits_price_min,
                        'max': limits_price_max,
                    },
                    'cost': {
                        'min': None,
                        'max': None,
                    },
                },
                'info': market,
            })
        return result

    def fetch_currencies(self, params={}):
        response = self.publicGetCurrencies(params)
        # [
        #     {
        #         "id": "btc",
        #         "min_size": "0.00000001",
        #         "name": "Bitcoin"
        #     },
        #     {
        #         "id": "eth",
        #         "min_size": "0.000000001",
        #         "name": "Ether"
        #     }
        # ]
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
                'precision': len(min_size) - 2,
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

    def fetch_ticker(self, symbol, params={}):
        self.load_markets()
        market, marketId = self.get_market_params(
            symbol, 'market_name', params)

        request = {
            'product_id': marketId,
        }
        response = self.publicGetProductsProductIdTicker(
            self.extend(request, params))
        # {
        #     "best_ask": "41000",
        #     "best_bid": "40000",
        #     "high_24h": "37181.9",
        #     "last_size": 26,
        #     "low_24h": "29557.1",
        #     "mark_price": "33953.7373",
        #     "open_24h": "31304.9",
        #     "price": "31150.3",
        #     "product_id": "btc_usd",
        #     "side": "sell",
        #     "time": "2021-07-09T21:14:26.000849+00:00",
        #     "trade_id": 29765,
        #     "volume_24h": 17851
        # }
        return self.parse_ticker(response, market)

    def parse_ticker(self, ticker, market=None):
        timestamp = self.parse8601(self.safe_string(ticker, 'time'))
        bid = self.safe_number(ticker, 'best_bid')
        ask = self.safe_number(ticker, 'best_ask')
        last = self.safe_number(ticker, 'price')
        open = self.safe_number(ticker, 'open_24h')

        marketId = self.safe_string(ticker, 'product_id')
        symbol = self.safe_symbol(marketId)

        if last and open:
            change = last - open
            percentage = change / open * 100
            average = (last + open) / 2
        else:
            change = None
            percentage = None
            average = None

        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': self.safe_number(ticker, 'high_24h'),
            'low': self.safe_number(ticker, 'low_24h'),
            'bid': bid,
            'bidVolume': None,
            'ask': ask,
            'askVolume': None,
            'vwap': None,
            'open': open,
            'close': last,
            'last': last,
            'previousClose': None,
            'change': change,  # last - open
            'percentage': percentage,  # change/open*100
            'average': average,  # (last + open)/2
            'baseVolume': self.safe_number(ticker, 'volume_24h'),
            'quoteVolume': None,
            'info': ticker,
        }

    def fetch_ohlcv(self, symbol, timeframe='1m', since=None, limit=None, params={}):
        self.load_markets()
        market, marketId = self.check_symbol_request(symbol, params)

        defaultLimit = 1500
        maxLimit = 1500
        limit = defaultLimit if (limit is None) else min(limit, maxLimit)
        request = {
            'product_id': marketId,
            'granularity': self.timeframes[timeframe],
        }
        duration = self.timeframes[timeframe]
        if since is not None:
            request['start'] = self.iso8601(since)
            if since > 0:
                end = self.sum(since, limit * duration * 1000)
                now = self.milliseconds()
                request['end'] = self.iso8601(min(now, end))
        else:
            now = self.milliseconds()
            request['end'] = self.iso8601(now)
            start = self.sum(now, -limit * duration * 1000)
            request['start'] = self.iso8601(start)
        response = self.publicGetProductsProductIdCandles(
            self.extend(request, params))
        # [
        #     [
        #         1625835780, # time
        #         31051.1,    # low
        #         32181.9,    # high
        #         31304.9,    # open
        #         31511.7,    # close
        #         981         # volume
        #     ],
        #     ...
        # ]
        return self.parse_ohlcvs(response, market, timeframe, since, limit)

    def parse_ohlcv(self, ohlcv, market=None):
        return [
            self.safe_integer(ohlcv, 0) * 1000,
            self.safe_number(ohlcv, 3),
            self.safe_number(ohlcv, 2),
            self.safe_number(ohlcv, 1),
            self.safe_number(ohlcv, 4),
            self.safe_number(ohlcv, 5),
        ]

    def fetch_balance(self, params={}):
        self.load_markets()

        response = self.privateGetAccounts(params)
        # [
        #     {
        #         "id": 412,
        #         "currency": "usdt",
        #         "balance": 90000000,
        #         "free": 90000000,
        #         "hold": 0,
        #         "update_time": "2023-02-19T18:18:57.727862+00:00",
        #         "global_asset": 0,
        #         "local_asset": {
        #             "zksync": "30000000",
        #             "polygon": "30000000",
        #             "arbitrum": "30000000"
        #         },
        #         "mobile_asset": {
        #             "zksync": "0",
        #             "arbitrum": "0",
        #             "polygon": "0"
        #         }
        #     },
        # ]
        return self.parse_balance_response(response)

    def parse_balance_response(self, response):
        result = {'info': response}
        for i in range(0, len(response)):
            balance = response[i]

            currencyId = self.safe_string(balance, 'currency')
            code = self.safe_currency_code(currencyId)
            account = self.account()
            free = self.safe_number(balance, 'free')
            free = self.number_to_string(free)
            total = self.safe_number(balance, 'balance')
            total = self.number_to_string(total)
            account['free'] = free
            account['total'] = total
            result[code] = account
        return result

    def fetch_ledger(self, code=None, since=None, limit=None, params={}):
        if code is None:
            raise ArgumentsRequired(
                self.id + ' method requires a code parameter')

        self.load_markets()
        currency = None
        if code is not None:
            currency = self.currency(code)

        request = self.prepare_account_request_with_currency_code(
            code, limit, params)
        if since is not None:
            request['start'] = self.iso8601(since)

        # Trading ledger:
        # {
        #     "amount": -269,
        #     "created_at": "2021-07-09T08:45:36.496050+00:00",
        #     "details": {
        #         "order_id": "07c250a1-e092-11eb-8007-e6aa351fe500",
        #         "product_id": "eth_usd",
        #         "trade_id": 4175
        #     },
        #     "id": 15,
        #     "type": "profits"
        # }
        #
        # Deposite ledger:
        # {
        #     "amount": 30000000000,
        #     "created_at": "2021-07-09T08:45:27.195538+00:00",
        #     "details": null,
        #     "id": 14,
        #     "type": "deposits"
        # }
        # Funding
        # {
        #     'amount': '4010',
        #     'created_at': '2021-07-10T08:00:30.550791+00:00',
        #     'details': {
        #         'order_id': 'Fundings',
        #         'trade_id': '22606298',
        #         'product_id': 'eth_usd'
        #     },
        #     'id': '2112',
        #     'type': 'profits',
        # }
        response = self.privateGetAccountsAccountIdLedger(request)
        accountId = self.safe_string_2(request, 'account_id', 'accountId')
        return self.parse_ledger(response, currency, since, limit, accountId=accountId)

    def parse_ledger_entry(self, item, currency=None, accountId=None):
        amount = self.safe_number(item, 'amount')
        direction = None
        if amount < 0:
            direction = 'out'
            amount = -amount
        else:
            direction = 'in'

        amount = self.from_wei_by_code(amount, currency['code'])

        timestamp = self.parse8601(self.safe_value(item, 'created_at'))
        id = self.safe_string(item, 'id')
        details = self.safe_value(item, 'details')
        orderId = self.safe_string(details, 'order_id')
        referenceId = self.safe_string(details, 'trade_id')
        type = self.safe_string(item, 'type')
        if type == 'profits':
            if orderId == 'Fundings':
                type = 'fundings'
            else:
                type = 'trade'

        return {
            'info': item,
            'id': id,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'direction': direction,
            'account': accountId,
            'referenceId': referenceId,
            'referenceAccount': None,
            'type': type,
            'currency': currency['code'],
            'amount': amount,
            'before': None,
            'after': None,
            'status': 'ok',
            'fee': None,
        }

    def parse_ledger(self, data, currency=None, since=None, limit=None, accountId=None, params={}):
        array = self.to_array(data)
        result = []
        for item in array:
            entry = self.parse_ledger_entry(item, currency, accountId)
            if isinstance(entry, list):
                print([self.extend(i, params) for i in entry])
                result += [self.extend(i, params) for i in entry]
            else:
                result.append(self.extend(entry, params))
        result = self.sort_by(result, 'timestamp')
        code = currency['code'] if currency else None
        tail = since is None
        return result

    def fetch_trades(self, symbol, since=None, limit=None, params={}):
        self.load_markets()
        market, marketId = self.check_symbol_request(symbol, params)

        request = {
            'product_id': marketId,
        }

        if limit is not None:
            request['limit'] = limit

        if since is not None:
            request['start'] = self.iso8601(since)

        trades = self.publicGetProductsProductIdTrades(
            self.extend(request, params))
        # [
        #     {
        #         "price": "31150.3",
        #         "side": "sell",
        #         "size": 26,
        #         "time": "2021-07-09T21:14:26.000849+00:00",
        #         "trade_id": 29765
        #     },
        #     ...
        # ]
        return self.parse_trades(trades, None, since, limit, params={'symbol': symbol})

    def fetch_my_trades(self, symbol=None, since=None, limit=None, params={}):
        self.load_markets()
        market, marketId = self.get_market_params(
            symbol, 'market_name', params)

        request = {}
        if marketId is not None:
            request['market'] = marketId
        if since is not None:
            request['start'] = self.iso8601(since)

        trades = self.privateGetFills(self.extend(request, params))
        # [
        #     {
        #         "created_at": "2021-07-09T20:39:56.904995+00:00",
        #         "fee": 61,
        #         "liquidity": "T",
        #         "order_id": "d28daf47-e0f5-11eb-80df-e6aa351fe500",
        #         "price": "31667.6",
        #         "product_id": "btc_usd",
        #         "settled": true,
        #         "side": "sell",
        #         "size": 28,
        #         "trade_id": 21901
        #     },
        #     ...
        # ]
        return self.parse_trades(trades, market, since, limit)

    def parse_trade(self, trade, market=None):
        id = self.safe_string(trade, 'trade_id')

        marketId = self.safe_string(trade, 'product_id')
        symbol = None
        if marketId in self.markets_by_id:
            market = self.markets_by_id[marketId]
            symbol = market['symbol']
        elif market is not None:
            symbol = market['symbol']

        orderId = self.safe_string(trade, 'order_id')
        timestamp = self.parse8601(
            self.safe_string_2(trade, 'created_at', 'time'))

        amount_str = self.safe_string(trade, 'size')
        price_str = self.safe_string(trade, 'price')
        amount = self.parse_number(amount_str)
        price = self.parse_number(price_str)
        side = self.safe_string(trade, 'side')

        result = {
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'id': id,
            'order': orderId,
            'type': None,
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

        if 'fee' in trade:
            code = self.market(symbol)['base']
            fee = None
            feeCost = self.safe_number(trade, 'fee')
            if feeCost is not None:
                feeCost = self.from_wei_by_code(feeCost, code)
                fee = {
                    'cost': feeCost,
                    'currency': code,
                    'rate': None,
                }

            cost = Precise.string_div(amount_str, price_str)
            cost = Precise.string_abs(cost)
            cost = self.currency_to_precision(code, cost)
            cost = self.parse_number(cost)
            result['fee'] = fee
            result['cost'] = cost

        return result

    def find_account_id(self, code):
        self.load_markets()
        self.load_accounts()
        for i in range(0, len(self.accounts)):
            account = self.accounts[i]
            if account['code'] == code:
                return account['id']
        return None

    def prepare_account_request(self, limit=None, params={}):
        accountId = self.safe_string_2(params, 'account_id', 'accountId')
        if accountId is None:
            raise ArgumentsRequired(
                self.id + ' method requires an account_id(or accountId) parameter')
        request = {
            'account_id': accountId,
        }
        if limit is not None:
            request['limit'] = limit
        return request

    def prepare_account_request_with_currency_code(self, code=None, limit=None, params={}):
        accountId = self.safe_string_2(params, 'account_id', 'accountId')
        if accountId is None:
            if code is None:
                raise ArgumentsRequired(
                    self.id + ' method requires an account_id(or accountId) parameter OR a currency code argument')
            accountId = self.find_account_id(code)
            if accountId is None:
                raise ExchangeError(
                    self.id + ' could not find account id for ' + code)
        request = {
            'account_id': accountId,
        }
        if limit is not None:
            request['limit'] = limit
        return request

    def parse_order_status(self, status, reason=None):
        statuses = {
            'pending': 'open',
            'received': 'open',
            'open': 'open',
            'done': 'closed' if not reason else 'canceled',  # filled or canceled
        }
        return self.safe_string(statuses, status, status)

    def parse_order(self, order):
        self.load_markets()

        id = self.safe_string(order, 'id')
        timestamp = self.parse8601(self.safe_string(order, 'created_at'))
        status = self.parse_order_status(self.safe_string(
            order, 'status'), self.safe_string(order, 'reason'))

        amount = self.safe_number(order, 'size')
        filled = self.safe_number(order, 'filled_size')
        remaining = max(amount - filled, 0)

        marketId = self.safe_string(order, 'product_id')
        symbol = self.safe_symbol(marketId)
        code = self.market(symbol)['base']

        side = self.safe_string(order, 'side')
        type = self.safe_string(order, 'type')

        price = self.safe_number(order, 'price')
        timeInForce = self.safe_string(order, 'time_in_force')
        if timeInForce:
            timeInForce = timeInForce.upper()
        stop = self.safe_string(order, 'stop')
        stopPrice = self.safe_number(order, 'stop_price')
        postOnly = self.safe_value(order, 'post_only')

        executed_value = self.safe_integer(order, 'executed_value', 0)

        return {
            'id': id,
            'clientOrderId': None,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'lastTradeTimestamp': None,
            'symbol': symbol,
            'type': type,
            'timeInForce': timeInForce,
            'postOnly': postOnly,
            'side': side,
            'price': price,
            'stop': stop,
            'stopPrice': stopPrice,
            'amount': amount,
            'cost': executed_value,
            'average': None,
            'filled': filled,
            'remaining': remaining,
            'status': status,
            'fee': None,
            'trades': None,
            'info': order,
        }

    def create_order(self, symbol, type, side, amount, price=None, params={}):
        self.load_markets()
        market, marketId = self.check_symbol_request(symbol, params)

        request = {
            'product_id': marketId,
            'side': side,  # "buy" or "sell"
            # 'price': 30000,  # send None for market orders
            'type': type,  # "limit", "market", "stop", "trailingStop", or "takeProfit"
            'size': int(self.amount_to_precision(symbol, amount)),
            # 'reduce_only': False,  # optional, default is False
            # "time_in_force": 'gtc', # optional, 'gtc', 'ioc', 'fok'
            # 'post_only': False,  # optional, default is False, limit orders only
            # 'stop': None # optional, "entry", "loss"
            # 'stop_price': None, #required if stop is not None
        }
        # Request:
        # {
        #     "product_id": 'btc_usd',
        #     "side": 'buy'/'sell',
        #     "size": integer,
        #     "type": 'limit'/'market',
        #     "price": None/float,
        #     "stop": 'entry'/'loss'/None,
        #     "stop_price": None/float,
        #     "time_in_force": 'gtc'/'ioc'/'fok',
        #     "post_only": bool,
        #     "reduce_only": bool
        #     "stp": "dc"/"cn"/"co"/"cb",
        #                                     #         "dc": decrease and cancel
        #                                     #         "cn": cancel new
        #                                     #         "co": cancel old
        #                                     #         "cb": cancel both
        # }
        # Return:
        # {
        #     "created_at": "2021-07-09T21:59:35.714065+00:00",
        #     "executed_value": 0,
        #     "filled_size": 0,
        #     "id": "f2f23286-e100-11eb-8808-e6aa351fe500",
        #     "post_only": false,
        #     "price": "30000",
        #     "product_id": "btc_usd",
        #     "reduce_only": false,
        #     "settled": true,
        #     "side": "buy",
        #     "size": 1,
        #     "status": "pending",
        #     "stp": "dc",
        #     "time_in_force": "gtc",
        #     "type": "limit"
        # }

        if type == 'limit':
            request['price'] = float(self.price_to_precision(symbol, price))
        elif type == 'market':
            request['price'] = None
        else:
            raise InvalidOrder(
                self.id + ' createOrder() does not support order type ' + type + ', only limit, market orders are supported')

        if self.safe_string(params, 'stop'):
            stop_type = self.safe_string(params, 'stop')
            if stop_type not in ['entry', 'loss']:
                raise InvalidOrder(
                    self.id + ' createOrder() requires stop must be either "entry" or "loss"')
            stopPrice = self.safe_number(params, 'stop_price')
            if stopPrice is None:
                raise ArgumentsRequired(
                    self.id + ' createOrder() requires a stop_price parameter for stop type orders')
            else:
                request['stop'] = stop_type
                request['stop_price'] = float(
                    self.price_to_precision(symbol, stopPrice))

        if self.safe_string(params, 'time_in_force'):
            time_in_force = self.safe_string(params, 'time_in_force')
            if time_in_force not in ['gtc', 'ioc', 'fok']:
                raise InvalidOrder(
                    self.id + ' createOrder() does not support time in force ' + time_in_force + ', only gtc, ioc, fok are supported')
            else:
                request['time_in_force'] = time_in_force

        response = self.privatePostOrders(self.extend(request, params))
        return self.parse_order(response)

    def fetch_order(self, id, symbol=None, params={}):
        request = {
            'order_id': id,
        }
        response = self.privateGetOrdersOrderId(self.extend(request, params))
        return self.parse_order(response)

    def fetch_orders(self, symbol=None, since=None, limit=None, status=None, params={}):
        self.load_markets()
        market, marketId = self.get_market_params(
            symbol, 'market_name', params)

        request = {}

        if symbol is not None:
            request['product_id'] = marketId

        if status is not None:
            request['status'] = status

        if limit is not None:
            request['limit'] = self.iso8601(since)

        if since is not None:
            request['start'] = self.iso8601(since)

        response = self.privateGetOrders(self.extend(request, params))

        result = []
        for i in range(len(response)):
            order = response[i]
            result.append(self.parse_order(order))
        return result

    def fetch_open_orders(self, symbol=None, since=None, limit=None, params={}):
        return self.fetch_orders(symbol, since, limit, status='open')

    def fetch_closed_orders(self, symbol=None, since=None, limit=None, params={}):
        return self.fetch_orders(symbol, since, limit, status='done')

    def cancel_order(self, id, params={}):
        order_id = str(id)
        request = {
            'order_id': order_id,
        }

        response = self.privateDeleteOrdersOrderId(
            self.extend(request, params))
        # display the canceled order id
        # [
        #     'f2f23286-e100-11eb-8808-e6aa351fe500'
        # ]
        if order_id not in response:
            raise NetworkError(
                self.id + ' could not cancel order with id ' + order_id)
        return "canceled order with id " + order_id

    def cancel_all_orders(self, symbol=None, params={}):
        self.load_markets()
        market, marketId = self.get_market_params(
            symbol, 'market_name', params)

        request = {
            'product_id': marketId,
        }
        response = self.private_delete_orders(self.extend(request, params))
        # display all canceled order ids
        # [
        #      'dcaa8fc3-e100-11eb-8807-e6aa351fe500',
        #      'fd565881-e0fb-11eb-8805-e6aa351fe500',
        #      'f3251109-e0fb-11eb-8804-e6aa351fe500'
        # ]
        return response

    def fetch_position(self, symbol=None, params={}):
        self.load_markets()
        market, marketId = self.check_symbol_request(symbol, params)

        request = {
            'product_id': marketId,
        }
        response = self.privateGetPositionsProductId(
            self.extend(request, params))

        return self.parse_position(response, market)

    def edit_leverage(self, symbol, leverage, params={}):
        self.load_markets()
        market, marketId = self.check_symbol_request(symbol, params)

        if not isinstance(leverage, int):
            raise ArgumentsRequired(self.id + ' leverage should be interger')

        request = {
            'product_id': marketId,
            "leverage": leverage
        }
        response = self.privatePostPositionsIsolate(
            self.extend(request, params))

        return self.parse_position(response, market)

    def set_cross_margin_mode(self, symbol, params={}):
        self.load_markets()
        market, marketId = self.check_symbol_request(symbol, params)

        request = {
            'product_id': marketId,
        }
        response = self.privatePostPositionsCross(self.extend(request, params))

        return self.parse_position(response, market)

    def edit_margin(self, symbol, margin, params={}):
        self.load_markets()
        market, marketId = self.check_symbol_request(symbol, params)
        code = market['base']

        margin = self.currency_to_precision(code, margin)
        margin = self.to_wei_by_code(margin, code)
        margin = int(margin)

        request = {
            'product_id': marketId,
            'margin': margin,
        }
        response = self.privatePostPositionsMargin(
            self.extend(request, params))

        return self.parse_position(response, market)

    def edit_margin_add(self, symbol, margin_add, params={}):
        return self.edit_margin(symbol, margin_add)

    def edit_margin_remove(self, symbol, margin_remove, params={}):
        return self.edit_margin(symbol, -margin_remove)

    def edit_risk_limit(self, symbol, risk_limit, params={}):
        self.load_markets()
        market, marketId = self.check_symbol_request(symbol, params)
        code = market['base']

        risk_limit = self.currency_to_precision(code, risk_limit)
        risk_limit = self.to_wei_by_code(risk_limit, code)
        risk_limit = int(risk_limit)

        request = {
            'product_id': marketId,
            'limit': risk_limit,
        }
        response = self.privatePostPositionsRisk(self.extend(request, params))

        return self.parse_position(response, market)

    def parse_position(self, position, market=None):
        # {
        #     "account": 4166,
        #     "avg_entry_price": "33182.7719",
        #     "bankrupt_price": "1000000.0000",
        #     "break_even_price": "0.0000",
        #     "commission": "0.0007",
        #     "cross_margin": false,
        #     "currency": "btc",
        #     "current_comm": 0,
        #     "current_cost": 0,
        #     "current_size": -286,
        #     "deleverage_percentile": 0,
        #     "exec_buy_cost": 0,
        #     "exec_buy_size": 24,
        #     "exec_comm": 0,
        #     "exec_cost": 0,
        #     "exec_sell_cost": 0,
        #     "exec_sell_size": 310,
        #     "exec_size": 334,
        #     "init_margin_req": "0.09",
        #     "is_open": true,
        #     "last_price": "31667.6000",
        #     "last_value": 88418,
        #     "leverage": 2,
        #     "liquidation_price": "1000000.0000",
        #     "maint_margin_req": "0.085",
        #     "margin_call_price": "1000000.0000",
        #     "mark_price": "33931.4841",
        #     "mark_value": 842875,
        #     "open_order_buy_cost": 0,
        #     "open_order_buy_premium": 0,
        #     "open_order_buy_size": 24,
        #     "open_order_sell_cost": 0,
        #     "open_order_sell_premium": 0,
        #     "open_order_sell_size": 0,
        #     "opening_comm": 0,
        #     "opening_cost": 0,
        #     "opening_size": 24,
        #     "opening_timestamp": "2021-07-09T13:04:07.058248+00:00",
        #     "pos_maint": 73260,
        #     "pos_margin": 100432154,
        #     "prev_close_price": "32764.8",
        #     "prev_realized_pnl": 0,
        #     "prev_unrealized_pnl": 0,
        #     "product_id": "btc_usd",
        #     "quote_currency": "usd",
        #     "realised_cost": 0,
        #     "realised_pnl": -3320,
        #     "rebalanced_pnl": 0,
        #     "risk_limit": 100000000000,
        #     "timestamp": "2021-07-09T22:02:59.426562+00:00",
        #     "underlying": "BTC",
        #     "unrealised_cost": 0,
        #     "unrealised_pnl": -19018
        # }
        marketId = self.safe_string(position, 'product_id')
        symbol = self.safe_symbol(marketId)
        code = self.markets[symbol]['quote']

        timestamp = self.parse8601(self.safe_string(position, 'timestamp'))
        isolated = not self.safe_value(position, 'cross_margin')

        contracts_str = self.safe_string(position, 'current_size')
        price_str = self.safe_string(position, 'avg_entry_price')
        contracts = self.parse_number(contracts_str)
        price = self.parse_number(price_str)

        if contracts > 0:
            notional = Precise.string_div(contracts_str, price_str)
            notional = Precise.string_abs(notional)
            notional = self.currency_to_precision(code, notional)
            notional = self.parse_number(notional)
        else:
            notional = 0
        markPrice = self.safe_number(position, 'mark_price')
        side = None
        if contracts < 0:
            side = 'short'
        else:
            side = 'long'

        leverage = self.safe_number(position, 'leverage')
        margin = self.safe_number(position, 'pos_margin')
        margin = self.from_wei_by_code(margin, code)
        maintMargin = self.safe_number(position, 'pos_maint')
        maintMargin = self.from_wei_by_code(maintMargin, code)

        initMarginReq = self.safe_number(position, 'init_margin_req')
        maintenanceMarginPercentage = self.safe_number(
            position, 'maint_margin_req')
        unrealizedPnl = self.safe_number(position, 'realised_pnl')
        unrealizedPnl = self.from_wei_by_code(unrealizedPnl, code)

        liquidationPrice = self.safe_number(position, 'liquidation_price')

        status = self.safe_value(position, 'is_open')
        if status == True:
            status == 'open'
        elif status == False:
            status = 'closed'

        return {
            'info': position,
            'id': None,
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'isolated': isolated,
            'hedged': False,
            'side': side,
            'contracts': contracts,
            'price': price,
            'markPrice': markPrice,
            'notional': notional,
            'leverage': leverage,
            'collateral': margin,
            'initialMargin': margin,
            'maintenanceMargin': maintMargin,
            'initialMarginPercentage': initMarginReq,
            'maintenanceMarginPercentage': maintenanceMarginPercentage,
            'unrealizedPnl': unrealizedPnl,
            'liquidationPrice': liquidationPrice,
            'status': 'open',
        }

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        fullPath = '/api/' + self.implode_params(path, params)
        query = self.omit(params, self.extract_params(path))
        if method == 'GET':
            if query:
                fullPath += '?' + self.urlencode(query)
        url = self.urls['api'] + fullPath
        if api == 'private':
            self.check_required_credentials()

            nonce = str(self.nonce())
            payload = ''
            if method != 'GET':
                if query:
                    body = self.json(query)
                    payload = body
            auth = nonce + method + fullPath + payload
            message = self.hash(self.encode(
                "\x19Ethereum Signed Message:\n" + str(len(auth)) + auth), 'keccak')
            signature = self.ecdsa(
                message, self.privateKey, algorithm="secp256k1")
            signature = '0x' + signature['r'] + \
                signature['s'] + hex(int(signature['v']+27))[2:]
            headers = {
                'ACCESS-SIGN': signature,
                'ACCESS-TIMESTAMP': nonce,
                'Content-Type': 'application/json',
            }
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def handle_errors(self, code, reason, url, method, headers, body, response, requestHeaders, requestBody):
        if code == 403:
            raise ExchangeNotAvailable(
                self.id + " is unavailable in your location.")

        if response is None:
            return  # fallback to default error handler

        if code == 401:
            raise AuthenticationError(self.id + "  " + body)
        elif code != 200:
            raise ExchangeError(
                self.id + ' failed due to a malformed response: ' + body)
