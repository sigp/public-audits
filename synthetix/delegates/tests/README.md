# Havven Review v7

The node modules need to be installed,

```
$ npm install
```

If you want to build the contracts use `npx truffle compile`, or simply `make`.

and a ganache-like client needs to be running, i.e

```
$ ganache-cli -l 10000000 -k istanbul
```

The tests can then be executed via

```
truffle test
```
