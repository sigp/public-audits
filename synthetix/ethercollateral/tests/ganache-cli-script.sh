#! /bin/sh

if [ -n "$(command -v ganache-cli)" ]; then
  BINARY=ganache-cli
elif [ -n "$(command -v npx)" ]; then
  BINARY="npx ganache-cli"
else
  BINARY=testrpc
fi

$BINARY \
	--accounts 50 \
	--defaultBalanceEther 100000000000 \
    --gasLimit 10000000 \
    --hardfork istanbul # \
    #--time '2019-03-01T00:00+00:00'
