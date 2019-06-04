#! /bin/sh

if [ -z $(which ganache-cli) ] 
then
  BINARY=testrpc
else
  BINARY=ganache-cli
fi

$BINARY \
	--accounts 50 \
	--defaultBalanceEther 100000000000 \
    --unlock "0xB6E5bF2995E9DFe57bcd46f2EE50209c62242708"
