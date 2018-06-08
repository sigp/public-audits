/*
 * VariableReturnData.sol
 *
 * These contracts aim to test variable return data sizes.
 */
pragma solidity ^0.4.19;


contract VariableReturnData {
    uint[5] public array;
	uint public callCount;

    function VariableReturnData()
        public
    {
        // fill the array with some junk
        array = [
            ~uint(0),
            2,
            ~uint(0),
            4,
            ~uint(0)
        ];
    }

    function returnArray()
        public
        returns (uint[5] _array)
    {
        callCount++;
		return array;
    }
	
	// this exists to allow functionality with the proxy
	function setMessageSender(address addr) 
		public
		pure
	{
		addr;
	}
}

contract WantsVariableReturnData {
    uint[5] public myArray;
    VariableReturnData public source;

    function WantsVariableReturnData(VariableReturnData _source)
        public
    {
        source = _source;
    }

    function getData()
        public
    {
        myArray = source.returnArray();
    }
}
