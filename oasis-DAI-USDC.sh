#!/bin/bash

bin/oasis-price-feed \
    --rpc-host {} \
    --base-exchange-address 0x794e6e91555438aFc3ccF1c5076A74F42133d08D \
    --base-token-symbol DAI \
    --base-token-address 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 \
    --base-token-decimals 18 \
    --quote-token-symbol USDC \
    --quote-token-address 0x6B175474E89094C44Da98b954EedeAC495271d0F \
    --quote-token-decimals 6 \
    --ro-account user:readonly \
    --rw-account user:readwrite
