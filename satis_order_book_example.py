#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import nest_asyncio
import time

from ccxt_satis.pro.satis import satis as satis_connector

nest_asyncio.apply()


class Satis(satis_connector):
    def handle_order_book_message(self, client, message, orderbook):
        asks = self.safe_value(message, 'a', [])
        bids = self.safe_value(message, 'b', [])
        # printing high-frequency updates is a resource-heavy task
        # this print statement is here just to demonstrate the work of it
        # replace it with you logic for processing individual updates
        print('Updates:', {
            'asks': asks,
            'bids': bids,
        })
        return super(Satis, self).handle_order_book_message(client, message, orderbook)


async def main():
    exchange = Satis({"privateKey": "0x1234567"})
    symbol = 'BTC/USDC'
    while True:
        try:
            orderbook = await exchange.watchOrderBook(symbol)
            print(orderbook)
            time.sleep(10)
        except Exception as e:
            print(str(e))
            # raise e  # uncomment to break all loops in case of an error in any one of them
            # break  # you can also break just this one loop if it fails
    await exchange.close()


asyncio.run(main())
