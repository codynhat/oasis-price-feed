# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2019 grandizzy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import tornado
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado import gen
import logging
import time
import threading
import collections
from pymaker.model import Token

from oasis_price_feed.auth import AuthenticationMixin, auth_required
from oasis_price_feed.config import Config

from tornado import concurrent


class FeedSocketHandler(tornado.websocket.WebSocketHandler, AuthenticationMixin):

    def initialize(self, otc, base_token: Token, quote_token: Token, config: Config):
        self.otc = otc
        self.base_token = base_token
        self.quote_token = quote_token
        self.config = config
        self.feed_name = f"{config.base_symbol}-{config.quote_symbol}"

        self.price = None

        self.executor = concurrent.futures.ThreadPoolExecutor(1)

        def calculate_price():
            while True:
                try:
                    logging.debug("Fetching prices from Oasis")

                    best_buy_id = self.otc._contract.functions.getBestOffer(base_token.address.address, quote_token.address.address).call()
                    best_sell_id = self.otc._contract.functions.getBestOffer(quote_token.address.address, base_token.address.address).call()

                    best_buy_order = self.otc.get_order(best_buy_id)
                    best_sell_order = self.otc.get_order(best_sell_id)

                    best_buy_price = float(self.quote_token.normalize_amount(best_buy_order.pay_amount) / self.base_token.normalize_amount(best_buy_order.buy_amount))
                    best_sell_price = float(self.quote_token.normalize_amount(best_sell_order.buy_amount) / self.base_token.normalize_amount(best_sell_order.pay_amount))

                    self.price = best_buy_price + ((best_sell_price -  best_buy_price) / 2)

                    logging.info(f"new price {self.price} calculated, sleep for {self.config.report_time} seconds")
                    time.sleep(self.config.report_time)
                except:
                    logging.error("Cannot calculate price, sleep for {self.config.report_time} seconds")
                    self.price = None
                    time.sleep(self.config.report_time)

        self.executor.submit(calculate_price)


    @tornado.web.asynchronous
    @auth_required(write=False)
    def get(self, *args, **kwargs):
        return super(FeedSocketHandler, self).get(*args, **kwargs)

    @gen.coroutine
    def open(self):
        self.id = Counter.next()
        self.set_nodelay(True)

        self.callback = tornado.ioloop.PeriodicCallback(self.send_price, self.config.report_time * 1000)
        self.callback.start()

    def send_price(self):
        logging.info(f"{self._prefix()} Sending price'")

        self.write_message({
            "timestamp": int(time.time()),
            "data": {
                "price": self.price
            }
        })

    def on_message(self, message):
        logging.warning(f"{self._prefix()} Unexpected message '{message}' received, ignoring")

    def on_close(self):
        logging.info(f"{self._prefix()} Socket with {self.request.remote_ip} closed")
        self.callback.stop()

    def _prefix(self):
        return f"[{self.feed_name}] [WebSocket #{self.id:06d}]"


class Counter:
    lock = threading.Lock()
    value = 0

    @classmethod
    def next(cls):
        with cls.lock:
            cls.value += 1
            return cls.value
