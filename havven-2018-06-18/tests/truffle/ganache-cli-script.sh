#! /bin/sh

if [ -z $(which ganache-cli) ] 
then
  BINARY=testrpc
else
  BINARY=ganache-cli
fi

$BINARY \
	--accounts 50
	--defaultBalanceEther 1000000000000000000000
