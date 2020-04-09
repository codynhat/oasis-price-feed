# oasis-price-feed

This repository contains a standalone service for publishing Oasis prices over Websockets.


## Rationale

This service facilitates distribution of real-time Oasis prices to keeper bots from the `market-maker-keeper`
<https://github.com/makerdao/market-maker-keeper> repository. 

## Installation

This project uses *Python 3.6.6* and requires *virtualenv* to be installed.

In order to clone the project and install required third-party packages please execute:
```
git clone https://github.com/codynhat/oasis-price-feed.git
cd oasis-price-feed
git submodule update --init --recursive
./install.sh
```


## Running

```
usage: oasis-price-feed [-h] [--rpc-host RPC_HOST] [--rpc-port RPC_PORT]
                        [--rpc-timeout RPC_TIMEOUT]
                        [--http-address HTTP_ADDRESS] [--http-port HTTP_PORT]
                        [--base-exchange-address BASE_EXCHANGE_ADDRESS]
                        [--base-token-symbol BASE_TOKEN_SYMBOL]
                        [--base-token-address BASE_TOKEN_ADDRESS]
                        --base-token-decimals BASE_TOKEN_DECIMALS
                        --quote-token-symbol QUOTE_TOKEN_SYMBOL
                        --quote-token-address QUOTE_TOKEN_ADDRESS
                        --quote-token-decimals QUOTE_TOKEN_DECIMALS
                        [--report-time REPORT_TIME] [--ro-account RO_ACCOUNT]
                        [--rw-account RW_ACCOUNT]

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
  --rpc-timeout RPC_TIMEOUT
                        JSON-RPC timeout (in seconds, default: 10)
  --http-address HTTP_ADDRESS
                        Address of the Oasis Price Feed
  --http-port HTTP_PORT
                        Port of the Oasis Price Feed
  --base-exchange-address BASE_EXCHANGE_ADDRESS
                        Address of the Oasis Exchange
  --base-token-symbol BASE_TOKEN_SYMBOL
                        Token symbol
  --base-token-address BASE_TOKEN_ADDRESS
                        Token address
  --base-token-decimals BASE_TOKEN_DECIMALS
                        Base Token decimals
  --quote-token-symbol QUOTE_TOKEN_SYMBOL
                        Quote Token symbol
  --quote-token-address QUOTE_TOKEN_ADDRESS
                        Quote Token address
  --quote-token-decimals QUOTE_TOKEN_DECIMALS
                        Quote Token decimals
  --report-time REPORT_TIME
                        Time interval to report price in seconds
  --ro-account RO_ACCOUNT
                        Credentials of the read-only user (format:
                        username:password)
  --rw-account RW_ACCOUNT
                        Credentials of the read-write user (format:
                        username:password)

```

## API

The primary and only entity this service operates on is _feed_. Each feed is effectively a stream
of timestamped records. Timestamps never go back and it is always guaranteed that
new records will be added 'after' the existing ones. This simplification makes feed streams
consumption much easier for clients.

Each record is represented throughout the service as a JSON structure with two fields: `timestamp`
and `data`. The first one is a UNIX epoch timestamp represented as a number (either integer or floating-point).
The latter can be basically anything. Sample record may look as follows:
```json
{
    "data": {
        "price": 173.03457395327663
    },
    "timestamp": 1571747588
}
```

All endpoints require and support only HTTP Basic authentication. Only one type of credentials
is supported at the moment: (`--ro-account`) gives read-only access to
the feeds.


### `ws://<service-location>/price/<feed-name>/socket`

Opens a new socket subscription to a feed. Each new subscriber will immediately receive the last record
from the feed, and will be promptly sent any new records posted by producer(s). Subscribers
can assume that timestamps of records received over the WebSocket will always increase.

This is a receive-only WebSocket. Any messages sent by consumers to the service will be ignored.

