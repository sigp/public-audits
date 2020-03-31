pragma solidity 0.4.25;

/**
 * @title Dummy proxy and Synthetix ERC20 contract.
 * @dev Exposes direct control of certain state variables to allow for testing of SupplySchedule.
 */
contract DummySynthetixProxy {
    uint public totalSupply;
    address public target;

    function setTotalSupply(uint _newSupply) external {
        totalSupply = _newSupply;
    }

    function setTarget(address _newTarget) external {
        target = _newTarget;
    }

}
