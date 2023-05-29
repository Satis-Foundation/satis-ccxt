#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import satis
import time

ex = satis.satisex({
    'privateKey': 'YOUR_PRIVKEY_WITHOUT_0x',
    # Without 0x
})

# fetch_time()
ex_time = ex.fetch_time()
print("Exchange time:",ex_time)
print("Exchange time:",time.asctime(time.localtime(ex_time)))
print()


# fetch_markets()

load_market_res = ex.fetch_markets()
print("Total product pair no.:",len(load_market_res))

product_list = []
for product in load_market_res:
    product_list.append(product['symbol'])
print("Product pair list:",product_list)
print()


# fetch_accounts()

accounts_res = ex.fetch_accounts()
account_currency_id_list = []
for i in accounts_res:
    account_currency_id_list.append(i['id'])
print("Account currency ID:",account_currency_id_list)
print()


# fetch_order_book()

for product in product_list:
    order_book_res = ex.fetch_order_book(product)
    print("Bid limit for",order_book_res['symbol'],"is",order_book_res['bids'])
print()


# fetch_currencies()

currencies_res = ex.fetch_currencies()
currency_list = list(currencies_res.keys())
print("Currencies available on SATIS are",currency_list)
for currency in currency_list:
    print(currency,"min limit is",currencies_res[currency]['limits']['amount']['min'])
print()


# fetch_ticker()

for product in product_list:
    ticker_res = ex.fetch_ticker(product)
    print("24hr volume for",product,"is",ticker_res['info']['volume_24h'])
    print("Mark price for",product,"is",ticker_res['info']['mark_price'])
print()


# # fetch_ohlcv()

# timeframe_list = ['1m','5m','15m','1h','6h','1d']
# for timeframe in timeframe_list:
#     for product in product_list:
#         ohlcv_res = ex.fetch_ohlcv(product,timeframe=timeframe)
#         print(product,"OHLCV plotting resolution for",timeframe,"is",len(ohlcv_res))
# print()


# fetch_balance()

balance_res = ex.fetch_balance()
for info in balance_res['info']:
    print("Hold value for",info['currency'],"is",info['hold'])
print("USDT hold is",float(balance_res['USDT']['total'])-float(balance_res['USDT']['free']))
print("USDC hold is",float(balance_res['USDC']['total'])-float(balance_res['USDC']['free']))
print()


# Create buy limit order

open_buy_limit_order_res = ex.create_limit_buy_order("ETH/USDT", 10, 2000)
print("Limit order for buy:", open_buy_limit_order_res)
order_id = open_buy_limit_order_res['id']
print("Limit order ID:",order_id)

close_limit_order_res = ex.cancel_order(order_id)
print("Close order response:", close_limit_order_res)

order_record = ex.fetch_orders()
print("Order record:", order_record)
