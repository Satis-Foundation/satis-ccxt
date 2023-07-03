# -*- coding: utf-8 -*-


import ccxt_satis.async_support
from ccxt_satis.async_support.base.ws.cache import ArrayCache, ArrayCacheBySymbolById, ArrayCacheByTimestamp
from ccxt_satis.async_support.base.ws.client import Client
from typing import Optional
from typing import List
from ccxt_satis.base.errors import RateLimitExceeded
from ccxt_satis.base.errors import ArgumentsRequired
from ccxt_satis.base.precise import Precise


class satis(ccxt_satis.async_support.satis):

    def describe(self):
        return self.deep_extend(super(satis, self).describe(), {
            'has': {
                'ws': True,
                'watchBalance': True,
                'watchMyTrades': True,
                'watchOHLCV': True,
                'watchOrderBook': True,
                'watchOrders': True,
                'watchTicker': True,
                'watchTickers': False,
                'watchTrades': True,
                'watchPosition': True,
            },
            'urls': {
                'api': {
                    'ws': 'wss://api.sat.is/ws',
                },
            },
            'options': {
                'tradesLimit': 1000,
                'OHLCVLimit': 1000,
            },
            'exceptions': {
                'ws': {
                    'exact': {
                    },
                    'broad': {
                        'Rate limit exceeded': RateLimitExceeded,
                    },
                },
            },
        })

    async def watch_ticker(self, symbol: str, params={}):
        await self.load_markets()
        market = self.market(symbol)
        messageHash = 'ticker:' + market['id']
        url = self.urls['api']['ws']
        request = {
            'type': 'subscribe',
            'channels': [
                {
                    'name': 'ticker',
                    'product_ids': [market['id']],
                }
            ],
        }
        return await self.watch(url, messageHash, self.extend(request, params), messageHash)

    def handle_ticker(self, client: Client, message):
        marketId = self.safe_string(message, 'product_id')
        market = self.safe_market(marketId)
        symbol = market['symbol']
        messageHash = 'ticker:' + market['id']

        ticker = self.parse_ticker(message, market)
        self.tickers[symbol] = ticker
        client.resolve(ticker, messageHash)
        return message

    async def watch_balance(self, params={}):
        await self.load_markets()
        auth = self.authenticate()

        messageHash = 'balance'
        url = self.urls['api']['ws']

        marketIds = []
        market_list = self.to_array(self.markets)
        currency_list = self.to_array(self.currencies)
        for i in range(0, len(currency_list)):
            product_list = self.to_array((self.filter_by_array(market_list, 'quote', [currency_list[i]['code']])))
            if len(product_list) > 0:
                marketIds.append(product_list[0]['id'])
        request = {
            'type': 'subscribe',
            'channels': [
                {
                    'name': 'accounts',
                    'product_ids': marketIds,
                }
            ],
        }
        request = self.extend(request, auth)
        return await self.watch(url, messageHash, self.extend(request, params), messageHash)

    def handle_balance(self, client: Client, message):
        balance = self.parse_balance([message])
        self.balance = self.deep_extend(self.balance, balance)
        messageHash = 'balance'
        client.resolve(self.balance, messageHash)

    def handle_trades(self, client: Client, message):
        marketId = self.safe_string(message, 'product_id')
        market = self.safe_market(marketId)
        symbol = market['symbol']
        tradesArray = self.safe_value(self.trades, symbol)
        if tradesArray is None:
            limit = self.safe_integer(self.options, 'tradesLimit', 1000)
            tradesArray = ArrayCache(limit)

        trades_msg = self.safe_value(message, 'trades', [])
        for i in range(0, len(trades_msg)):
            result = {
                'price': self.safe_value(trades_msg[i], 0),
                'size': self.safe_value(trades_msg[i], 1),
                'time': self.safe_value(trades_msg[i], 2),
            }
            trade = self.parse_trade(result, market)
            tradesArray.append(trade)

        messageHash = 'trade:' + market['id']
        self.trades[symbol] = tradesArray
        client.resolve(tradesArray, messageHash)

    async def watch_trades(self, symbol: str, since: Optional[int] = None, limit: Optional[int] = None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        symbol = market['symbol']
        messageHash = 'trade:' + market['id']
        url = self.urls['api']['ws']
        request = {
            'type': 'subscribe',
            'channels': [
                {
                    'name': 'trades',
                    'product_ids': [market['id']],
                }
            ],
        }
        trades = await self.watch(url, messageHash, self.extend(request, params), messageHash)
        if self.newUpdates:
            limit = trades.getLimit(symbol, limit)
        return self.filter_by_since_limit(trades, since, limit, 'timestamp', True)

    def authenticate(self):
        self.check_required_credentials()

        auth = "hey satis"
        hash = self.hash(self.encode(
            "\x19Ethereum Signed Message:\n" + str(len(auth)) + auth), 'keccak')
        signature = self.ecdsa(
            hash[-64:], self.privateKey[-64:], algorithm="secp256k1")
        signature = '0x' + signature['r'] + \
            signature['s'] + hex(int(signature['v'] + 27))[2:]
        return {
            'signature': signature,
        }

    async def watch_orders(self, symbol: Optional[str] = None, since: Optional[int] = None, limit: Optional[int] = None, params={}):
        await self.load_markets()
        auth = self.authenticate()

        url = self.urls['api']['ws']

        if symbol is None:
            raise ArgumentsRequired(self.id + ' watchMyTrades() requires a symbol argument')
        market = self.market(symbol)
        messageHash = 'orders:' + market['id']

        request = {
            'type': 'subscribe',
            'channels': [
                {
                    'name': 'users',
                    'product_ids': [market['id']],
                }
            ],
        }
        request = self.extend(request, auth)

        if self.orders is None:
            limit = self.safe_integer(self.options, 'ordersLimit', 1000)
            self.orders = ArrayCacheBySymbolById(limit)

        open_orders = await self.fetch_orders(market['id'])
        stored = self.orders
        for i in range(0, len(open_orders)):
            openOrder = self.safe_value(open_orders, i)
            stored.append(openOrder)
        orders = await self.watch(url, messageHash, request, messageHash)

        if self.newUpdates:
            limit = orders.getLimit(symbol, limit)
        return self.filter_by_symbol_since_limit(orders, symbol, since, limit)

    def handle_order_match(self, client: Client, message):
        marketId = self.safe_string(message, 'product_id')
        market = self.safe_market(marketId)
        messageHash = 'orders:' + market['id']

        if self.orders is None:
            limit = self.safe_integer(self.options, 'ordersLimit', 1000)
            self.orders = ArrayCacheBySymbolById(limit)

        stored = self.orders
        ordersInSymbol = self.safe_value(stored.hashmap, market['symbol'], {})

        maker_order_id = self.safe_string(message, "maker_order_id")
        taker_order_id = self.safe_string(message, "taker_order_id")
        if self.in_array(maker_order_id, ordersInSymbol):
            previousOrder = self.safe_value(ordersInSymbol, maker_order_id)
        elif self.in_array(taker_order_id, ordersInSymbol):
            previousOrder = self.safe_value(ordersInSymbol, taker_order_id)

        order_info = self.safe_value(previousOrder, 'info')
        last_trade_id = self.safe_integer(order_info, 'last_trade_id', 0)
        trade_id = self.safe_integer(message, 'trade_id', 0)

        status = self.safe_string(order_info, 'status')
        if status != 'done' and int(trade_id) > int(last_trade_id):
            add_size = self.safe_string(message, 'size')
            add_executed_value = Precise.string_mul(self.safe_string(message, 'price'), add_size)
            order_info['filled_size'] = Precise.string_add(self.safe_string(order_info, 'filled_size'), add_size)
            order_info['executed_value'] = Precise.string_add(self.safe_string(order_info, 'executed_value'), add_executed_value)
            order_info['last_trade_id'] = trade_id
            order = self.parse_order(order_info)
            stored.append(order)
            client.resolve(self.orders, messageHash)
        self.handle_my_trades(client, message)

    def handle_order_update(self, client: Client, message):
        marketId = self.safe_string(message, 'product_id')
        market = self.safe_market(marketId)
        messageHash = 'orders:' + market['id']

        if self.orders is None:
            limit = self.safe_integer(self.options, 'ordersLimit', 1000)
            self.orders = ArrayCacheBySymbolById(limit)

        currentOrder = message
        stored = self.orders
        orderId = self.safe_string(currentOrder, 'orderID')
        previousOrder = self.safe_value(stored.hashmap, orderId)
        rawOrder = currentOrder
        if previousOrder is not None:
            rawOrder = self.extend(previousOrder['info'], currentOrder)
        order = self.parse_order(rawOrder)
        stored.append(order)
        client.resolve(self.orders, messageHash)

    async def watch_my_trades(self, symbol: Optional[str] = None, since: Optional[int] = None, limit: Optional[int] = None, params={}):
        await self.load_markets()
        auth = self.authenticate()

        url = self.urls['api']['ws']

        if symbol is None:
            raise ArgumentsRequired(self.id + ' watchMyTrades() requires a symbol argument')
        market = self.market(symbol)
        messageHash = 'my_trade:' + market['id']

        request = {
            'type': 'subscribe',
            'channels': [
                {
                    'name': 'users',
                    'product_ids': [market['id']],
                }
            ],
        }
        request = self.extend(request, auth)

        trades = await self.watch(url, messageHash, request, messageHash)
        if self.newUpdates:
            limit = trades.getLimit(symbol, limit)
        return self.filter_by_symbol_since_limit(trades, symbol, since, limit, True)

    def handle_my_trades(self, client: Client, message):
        marketId = self.safe_string(message, 'product_id')
        market = self.safe_market(marketId)
        messageHash = 'my_trade:' + market['id']

        cachedOrders = self.orders
        if cachedOrders is not None:
            orders = self.safe_value(cachedOrders.hashmap, market['symbol'], {})
            maker_order_id = self.safe_string(message, "maker_order_id")
            taker_order_id = self.safe_string(message, "taker_order_id")
            order = {}
            if self.in_array(maker_order_id, orders):
                order = self.safe_value(orders, maker_order_id)
                message['liquidity'] = 'M'
            elif self.in_array(taker_order_id, orders):
                order = self.safe_value(orders, taker_order_id)
                message['liquidity'] = 'T'
            if order is not None:
                message['fee'] = self.safe_value(order, 'fee')
                message['side'] = self.safe_value(order, 'side')
                message['order_id'] = self.safe_string(order, 'id')
                message['type'] = self.safe_value(order, 'type')
        trade = self.parse_trade(message)

        if self.myTrades is None:
            limit = self.safe_integer(self.options, 'tradesLimit', 1000)
            self.myTrades = ArrayCacheBySymbolById(limit)
        stored = self.myTrades
        stored.append(trade)

        client.resolve(stored, messageHash)

    async def watch_order_book(self, symbol: str, limit: Optional[int] = None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        messageHash = 'level2:' + market['id']
        url = self.urls['api']['ws']
        request = {
            'type': 'subscribe',
            'channels': [
                {
                    'name': 'level2',
                    'product_ids': [market['id']]
                }
            ]
        }
        orderbook = await self.watch(url, messageHash, self.deep_extend(request, params), messageHash)
        return orderbook.limit()

    async def watch_ohlcv(self, symbol: str, timeframe='1m', since: Optional[int] = None, limit: Optional[int] = None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        symbol = market['symbol']
        interval = self.safe_string(self.timeframes, timeframe, timeframe)
        messageHash = 'candles:' + market['id'] + '_' + interval
        url = self.urls['api']['ws']
        request = {
            'type': 'subscribe',
            'channels': [
                {
                    'name': 'candles',
                    'product_ids': [market['id']]
                }
            ]
        }
        ohlcv = await self.watch(url, messageHash, self.extend(request, params), messageHash)
        if self.newUpdates:
            limit = ohlcv.getLimit(symbol, limit)
        return self.filter_by_since_limit(ohlcv, since, limit, 0, True)

    def handle_ohlcv(self, client: Client, message):
        candles = self.safe_value(message, 'candles', )
        timeframes = list(candles.keys())
        marketId = self.safe_string(message, 'product_id')
        symbol = self.safe_symbol(marketId)

        for i in range(0, len(timeframes)):
            timeframe = timeframes[i]
            candle = self.safe_value(candles, timeframe, {})

            parsed = [
                self.safe_integer(candle, 'time') * 1000,
                self.safe_float(candle, 'open'),
                self.safe_float(candle, 'high'),
                self.safe_float(candle, 'low'),
                self.safe_float(candle, 'close'),
                self.safe_float(candle, 'volume'),
            ]

            self.ohlcvs[symbol] = self.safe_value(self.ohlcvs, symbol, {})
            stored = self.safe_value(self.ohlcvs[symbol], timeframe)
            if stored is None:
                limit = self.safe_integer(self.options, 'OHLCVLimit', 1000)
                stored = ArrayCacheByTimestamp(limit)
                self.ohlcvs[symbol][timeframe] = stored
            stored.append(parsed)
            interval = self.safe_string(self.timeframes, timeframe, timeframe)

            messageHash = 'candles:' + marketId + '_' + interval
            client.resolve(stored, messageHash)

    def handle_order_book(self, client: Client, message):
        msg_type = self.safe_string(message, 'type')
        marketId = self.safe_value(message, 'product_id')
        market = self.safe_market(marketId)
        symbol = market['symbol']

        # if it's an initial snapshot
        if msg_type == 'snapshot':
            orderbook = self.order_book(self.parse_order_book(message, symbol))
            self.orderbooks[symbol] = orderbook

            messageHash = 'level2:' + marketId
            client.resolve(orderbook, messageHash)
        else:
            changes = self.safe_value(message, 'changes', [])
            orderbook = self.orderbooks[symbol]

            for i in range(0, len(changes)):
                change = changes[i]
                if self.safe_value(change, 0) == 'buy':
                    bookside = orderbook['bids']
                else:
                    bookside = orderbook['asks']

                price = self.safe_float(change, 1)
                size = self.safe_float(change, 2)
                bookside.store(price, size)

            messageHash = 'level2:' + marketId
            client.resolve(orderbook, messageHash)
            datetime = self.safe_string(message, 'time')
            orderbook['timestamp'] = self.parse8601(datetime)
            orderbook['datetime'] = datetime

    async def watch_position(self, symbol: str, params={}):
        await self.load_markets()
        auth = self.authenticate()
        market = self.market(symbol)
        messageHash = 'positions:' + market['id']
        url = self.urls['api']['ws']
        request = {
            'type': 'subscribe',
            'channels': [
                {
                    'name': 'positions',
                    'product_ids': [market['id']],
                }
            ],
        }
        request = self.extend(request, auth)
        return await self.watch(url, messageHash, self.extend(request, params), messageHash)

    def handle_position(self, client: Client, message):
        position = self.parse_position(message)

        marketId = self.safe_value(message, 'product_id')
        market = self.safe_market(marketId)
        symbol = market['symbol']

        self.positions[symbol] = position
        messageHash = 'positions:' + market['id']
        client.resolve(self.positions, messageHash)
        return message

    def handle_system_status(self, client: Client, message):
        return message

    def handle_subscription_status(self, client: Client, message):
        return message

    def handle_message(self, client: Client, message):
        msg_type = self.safe_string(message, 'type')

        methods = {
            'update': self.handle_order_book,
            'snapshot': self.handle_order_book,
            'ticker': self.handle_ticker,
            'trades': self.handle_trades,
            'candles': self.handle_ohlcv,
            'received': self.handle_order_update,
            'open': self.handle_order_update,
            'done': self.handle_order_update,
            'match': self.handle_order_match,
            'account': self.handle_balance,
            'position': self.handle_position,
        }
        method = self.safe_value(methods, msg_type)
        if method is None:
            return message
        return method(client, message)
