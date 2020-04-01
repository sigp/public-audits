const havvenHelpers = require('../synthetixHelpers.js')
const toUnit = havvenHelpers.toUnit;

module.exports  = {
	fake_currency_key_1:  web3.utils.asciiToHex("asdf"),
	fake_currency_key_2:  web3.utils.asciiToHex("blahblahblah"),
	fake_currency_key_3:  web3.utils.asciiToHex("sAUDblahblah"),
	NUSD_CURRENCY_KEY:  web3.utils.asciiToHex("sUSD"),
	XDR_CURRENCY_KEY:  web3.utils.asciiToHex("XDR") + "00",
	SNX_CURRENCY_KEY:  web3.utils.asciiToHex("SNX") + "00",
	NEUR_CURRENCY_KEY:  web3.utils.asciiToHex("sEUR"),
	SOME_SET_OF_RATES:  [toUnit(11), toUnit(12), toUnit(13), toUnit(14), toUnit(15), toUnit(16)],
	TOTAL_SUM_OF_XDR_RATES:  toUnit(51),
	ORACLE_FUTURE_LIMIT:  10 * 60,
	DEFAULT_STALE_RATE_PERIOD:  3 * 60 * 60,
}
