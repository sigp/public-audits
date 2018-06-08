pragma solidity ^0.4.19;


contract Owned {
    address public owner;
    address nominatedOwner;

    function Owned(address _owner)
        public
    {
        owner = _owner;
    }

    function nominateOwner(address _owner)
        external
        onlyOwner
    {
        nominatedOwner = _owner;
        NewOwnerNominated(_owner);
    }

    function _setOwner()
        internal
    {
        OwnerChanged(owner, nominatedOwner);
        owner = nominatedOwner;
        nominatedOwner = address(0);
    }

    function acceptOwnership()
        external
    {
        require(msg.sender == nominatedOwner);
        _setOwner();
    }

    modifier onlyOwner
    {
        require(msg.sender == owner);
        _;
    }

    event NewOwnerNominated(address newOwner);
    event OwnerChanged(address oldOwner, address newOwner);
}


contract OwnerToZero is Owned {

    function OwnerToZero(address _owner)
		Owned(_owner)
        public
    {
		// do nothing
    }

	function doSomethingStupid() 
		public
	{
		_setOwner();
	}
}
