pragma solidity ^0.4.24;

interface CWallet {
    function recoverGas(uint256 _version, address[] _keys) external;
}

contract CheckGasUse {
    CWallet public wallet;

    constructor (address wal) public {
        wallet = CWallet(wal);
    }

    function useGas(address[] accs) public {
        assembly {
            sstore(2, 0x23)
            sstore(3, 0x23)
            sstore(4, 0x23)
            sstore(5, 0x23)
            sstore(6, 0x23)
        }

        wallet.recoverGas(1, accs);
    }
}
