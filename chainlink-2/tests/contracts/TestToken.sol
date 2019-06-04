pragma solidity ^0.4.11;

/**
 * @title SafeMath
 * @dev Math operations with safety checks that revert on error
 */
library SafeMath {

    /**
     * @dev Multiplies two numbers, reverts on overflow.
     */
    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        // Gas optimization: this is cheaper than requiring 'a' not being zero, but the
        // benefit is lost if 'b' is also tested.
        // See: https://github.com/OpenZeppelin/openzeppelin-solidity/pull/522
        if (a == 0) {
            return 0;
        }

        uint256 c = a * b;
        require(c / a == b);

        return c;
    }

    /**
     * @dev Integer division of two numbers truncating the quotient, reverts on division by zero.
     */
    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b > 0); // Solidity only automatically asserts when dividing by 0
        uint256 c = a / b;
        // assert(a == b * c + a % b); // There is no case in which this doesn't hold

        return c;
    }

    /**
     * @dev Subtracts two numbers, reverts on overflow (i.e. if subtrahend is greater than minuend).
     */
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b <= a);
        uint256 c = a - b;

        return c;
    }

    /**
     * @dev Adds two numbers, reverts on overflow.
     */
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a);

        return c;
    }

    /**
     * @dev Divides two numbers and returns the remainder (unsigned integer modulo),
     * reverts when dividing by zero.
     */
    function mod(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b != 0);
        return a % b;
    }
}

contract TestToken {
    using SafeMath for uint256;

    uint public constant totalSupply = 10**27;
    string public constant name = 'Test Token';
    uint8 public constant decimals = 18;
    string public constant symbol = 'TTOK';
    mapping(address => uint256) balances;
    mapping (address => mapping (address => uint256)) allowed;

    constructor ()
        public
        {
            balances[msg.sender] = totalSupply;
        }

    /**
     * @dev transfer token to a specified address with additional data if the recipient is a contract.
     * @param _to The address to transfer to.
     * @param _value The amount to be transferred.
     * @param _data The extra data to be passed to the receiving contract.
     */
    function transferAndCall(address _to, uint _value, bytes _data)
        public
        returns (bool success)
        {
            transfer(_to, _value);
            emit Transfer(msg.sender, _to, _value, _data);
            return true;
        }
    /**
     * @dev transfer token to a specified address.
     * @param _to The address to transfer to.
     * @param _value The amount to be transferred.
     */
    function transfer(address _to, uint256 _value) public returns (bool) {
        balances[msg.sender] = balances[msg.sender].sub(_value);
        balances[_to] = balances[_to].add(_value);
        emit Transfer(msg.sender, _to, _value);
        return true;
    }

    /**
     * @dev Approve the passed address to spend the specified amount of tokens on behalf of msg.sender.
     * @param _spender The address which will spend the funds.
     * @param _value The amount of tokens to be spent.
     */
    function approve(address _spender, uint256 _value)
        public
        validRecipient(_spender)
        returns (bool)
        {
            allowed[msg.sender][_spender] = _value;
            emit Approval(msg.sender, _spender, _value);
            return true;
        }

    function allowance(address _owner, address _spender) public view returns (uint256 remaining) {
        return allowed[_owner][_spender];
    }


    function increaseeApproval (address _spender, uint _addedValue) public
        returns (bool success) {
            allowed[msg.sender][_spender] = allowed[msg.sender][_spender].add(_addedValue);
            emit Approval(msg.sender, _spender, allowed[msg.sender][_spender]);
            return true;
        }

    function decreaseApproval (address _spender, uint _subtractedValue) public
        returns (bool success) {
            uint oldValue = allowed[msg.sender][_spender];
            if (_subtractedValue > oldValue) {
                allowed[msg.sender][_spender] = 0;
            } else {
                allowed[msg.sender][_spender] = oldValue.sub(_subtractedValue);
            }
            emit Approval(msg.sender, _spender, allowed[msg.sender][_spender]);
            return true;
        }

    /**
     * @dev Transfer tokens from one address to another
     * @param _from address The address which you want to send tokens from
     * @param _to address The address which you want to transfer to
     * @param _value uint256 the amount of tokens to be transferred
     */
    function transferFrom(address _from, address _to, uint256 _value)
        public
        validRecipient(_to)
        returns (bool)
        {
            uint256 _allowance = allowed[_from][msg.sender];

            // Check is not needed because sub(_allowance, _value) will already throw if this condition is not met
            // require (_value <= _allowance);

            balances[_from] = balances[_from].sub(_value);
            balances[_to] = balances[_to].add(_value);
            allowed[_from][msg.sender] = _allowance.sub(_value);
            emit Transfer(_from, _to, _value);
            return true;
        }

    function balanceOf(address _owner) public view returns (uint256 balance) {
        return balances[_owner];
    }

    function isContract(address _addr)
        private
        view
        returns (bool hasCode)
        {
            uint length;
            assembly { length := extcodesize(_addr) }
            return length > 0;
        }

    // MODIFIERS

    modifier validRecipient(address _recipient) {
        require(_recipient != address(0) && _recipient != address(this));
        _;
    }

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Transfer(address indexed from, address indexed to, uint256 value, bytes data);
    event Approval(address indexed owner, address indexed spender, uint256 value);

}

