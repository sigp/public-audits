# Fantom Token Review 

This directory contains the testing suite used in the security review. In order
to run the tests the requisite node modules need to be installed. This can be
achieved via:

```
$ npm install
```

A ganache-like client (`testrpc` and `geth --dev` are alternative options) need to be running, i.e 

```
$ ganache-cli
```

The tests can then be executed via 

```
truffle test
```
