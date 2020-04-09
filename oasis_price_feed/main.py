#
# Copyright (C) 2020 Cody Hatfield
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

import argparse
import logging
import sys
import tornado
from oasis_price_feed.feed import FeedSocketHandler
from oasis_price_feed.config import Config
from web3 import Web3, HTTPProvider

from pymaker.oasis import Order, MatchingMarket
from pymaker import Address
from pymaker.model import Token

class OasisPriceFeed:
    """Oasis Price Feed server."""

    logger = logging.getLogger()

    def __init__(self, args: list, **kwargs):
        parser = argparse.ArgumentParser(prog='oasis-price-feed')

        parser.add_argument("--rpc-host", type=str, default="localhost",
                            help="JSON-RPC host (default: `localhost')")

        parser.add_argument("--rpc-port", type=int, default=8545,
                            help="JSON-RPC port (default: `8545')")

        parser.add_argument("--rpc-timeout", type=int, default=10,
                            help="JSON-RPC timeout (in seconds, default: 10)")

        parser.add_argument("--http-address", type=str, default='',
                            help="Address of the Oasis Price Feed")

        parser.add_argument("--http-port", type=int, default=7777,
                            help="Port of the Oasis Price Feed")

        parser.add_argument("--base-exchange-address", type=str, default=None,
                            help="Address of the Oasis Exchange")

        parser.add_argument("--base-token-symbol", type=str, default='ETH',
                            help="Token symbol")

        parser.add_argument("--base-token-address", type=str, default='',
                            help="Token address")
        
        parser.add_argument("--base-token-decimals", type=int,
                        help="Base Token decimals", required=True)

        parser.add_argument("--quote-token-symbol", type=str, default='',
                        help="Quote Token symbol", required=True)

        parser.add_argument("--quote-token-address", type=str, default='',
                        help="Quote Token address", required=True)

        parser.add_argument("--quote-token-decimals", type=int,
                        help="Quote Token decimals", required=True)

        parser.add_argument("--report-time", type=int, default=60,
                            help="Time interval to report price in seconds")

        parser.add_argument("--ro-account", type=str,
                            help="Credentials of the read-only user (format: username:password)")

        parser.add_argument("--rw-account", type=str,
                            help="Credentials of the read-write user (format: username:password)")

        self.arguments = parser.parse_args(args)

        if self.arguments.rpc_host.startswith("https"):
            endpoint_uri = f"{self.arguments.rpc_host}"
        else:
            endpoint_uri = f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}"

        self.web3 = kwargs['web3'] if 'web3' in kwargs else Web3(HTTPProvider(endpoint_uri=endpoint_uri,
                                                                              request_kwargs={"timeout": self.arguments.rpc_timeout}))

        self.web3.eth.defaultAccount = "0x0000000000000000000000000000000000000000"

        self.otc = MatchingMarket(web3=self.web3,
                                  address=Address(self.arguments.base_exchange_address))
        
        self.base_token = Token(self.arguments.base_token_symbol, Address(self.arguments.base_token_address), self.arguments.base_token_decimals)
        self.quote_token = Token(self.arguments.quote_token_symbol, Address(self.arguments.quote_token_address), self.arguments.quote_token_decimals)

        self.config = Config(
            base_symbol=self.arguments.base_token_symbol,
            quote_symbol=self.arguments.quote_token_symbol,
            report_time=self.arguments.report_time,
            ro_account=self.arguments.ro_account,
            rw_account=self.arguments.rw_account)

        application = tornado.web.Application([
            (f"/price/{self.arguments.base_token_symbol}-{self.arguments.quote_token_symbol}/socket", FeedSocketHandler,
                dict(otc=self.otc,
                     base_token=self.base_token,
                     quote_token=self.quote_token,
                     config=self.config))
        ])
        application.listen(port=self.arguments.http_port,address=self.arguments.http_address)
        logging.info(f"Price feed for {self.arguments.base_token_symbol}-{self.arguments.quote_token_symbol} started "
                     f"on port {self.arguments.http_port}, waiting for websocket clients")
        tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)
    OasisPriceFeed(sys.argv[1:]).main()
