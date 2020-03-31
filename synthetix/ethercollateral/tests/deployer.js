const synthetixHelpers = require('./synthetixHelpers.js')
const toUnit = synthetixHelpers.toUnit
const w3utils = require('web3-utils');

const AddressResolver = artifacts.require('./AddressResolver.sol')
const ExchangeRates = artifacts.require('./ExchangeRates.sol')
const DelegateApprovals = artifacts.require('./DelegateApprovals.sol')
const FeePool = artifacts.require('./FeePool.sol')
const FeePoolEternalStorage = artifacts.require('./FeePoolEternalStorage')
const FeePoolState = artifacts.require('./FeePoolState')
const SynthetixEscrow = artifacts.require('./SynthetixEscrow')
const Synthetix = artifacts.require('./Synthetix.sol')
const Synth = artifacts.require('./Synth.sol')
const MultiCollateralSynth = artifacts.require('./MultiCollateralSynth.sol')
const SafeDecimalMath = artifacts.require('./SafeDecimalMath.sol')
const SynthetixState = artifacts.require('./SynthetixState.sol')
const TokenState = artifacts.require('./TokenState.sol')
const Proxy = artifacts.require('./Proxy')
const SupplySchedule = artifacts.require('./SupplySchedule.sol')
const RewardEscrow = artifacts.require('./RewardEscrow')
const RewardsDistribution = artifacts.require('./RewardsDistribution.sol')
const Depot = artifacts.require('./Depot.sol')
const EtherCollateral = artifacts.require('./EtherCollateral.sol')
const Issuer = artifacts.require('./Issuer.sol')
const ExchangeState = artifacts.require('./ExchangeState.sol')
const Exchanger = artifacts.require('./Exchanger.sol')

const zeroAddress = '0x0000000000000000000000000000000000000000'

const toBytes32 = key => w3utils.rightPad(w3utils.asciiToHex(key), 64);

const currencyKeys = [
  'sUSD',
  'sETH',
].map(toBytes32)

const SYNT_TOTAL_SUPPLY = web3.utils.toWei('1000000');


const currencyRates = currencyKeys.slice(0,1).map(_ => toUnit(1))

const deploySynth = async function (owner, currencyKey, resolver) {
  // Create the Synth, along with its proxy and state.
  const proxy = await Proxy.new(owner)
  const state = await TokenState.new(owner, zeroAddress)
  const synth = await Synth.new(
    proxy.address,
    state.address,
    'Synth USD',
    'sUSD',
    owner,
    currencyKey,
    SYNT_TOTAL_SUPPLY,
    resolver.address,

    { from: owner }
  )
  // Link the Synth, proxy and state with each other.
  await proxy.setTarget(synth.address, { from: owner })
  await synth.setProxy(proxy.address, { from: owner })
  await state.setAssociatedContract(synth.address, { from: owner })
  // Return all params
  return [synth, proxy, state]
}
module.exports.deploySynth = deploySynth

const deployMultiCollateralSynth = async function (owner, currencyKey, resolver) {
  // Create the Synth, along with its proxy and state.
  const proxy = await Proxy.new(owner)
  const state = await TokenState.new(owner, zeroAddress)
  const synth = await MultiCollateralSynth.new(
    proxy.address,
    state.address,
    'Synth ETH',
    'sETH',
    owner,
    currencyKey,
    SYNT_TOTAL_SUPPLY,
    resolver.address,
    toBytes32('EtherCollateral'),

    { from: owner }
  )
  // Link the Synth, proxy and state with each other.
  await proxy.setTarget(synth.address, { from: owner })
  await synth.setProxy(proxy.address, { from: owner })
  await state.setAssociatedContract(synth.address, { from: owner })
  // Return all params
  return [synth, proxy, state]
}
module.exports.deployMultiCollateralSynth = deployMultiCollateralSynth

/*
 * Deploy a brand new Synthetix system for testing.
 */
const deployTestRig = async function (accounts) {
  // define our accounts
  const owner = accounts[1]
  const oracle = accounts[2]
  const beneficiary = accounts[3]
  const fundsWallet = accounts[4]
  const feeAuthority = accounts[5]
  /*
   * Deploy the SafeMath contract.
   *
   * Additionally, tell truffle to link all the contracts that use the library
   * to the address it was deployed to.
   */
  const safeMath = await SafeDecimalMath.new()
  FeePool.link('SafeDecimalMath', safeMath.address)
  SynthetixState.link('SafeDecimalMath', safeMath.address)
  ExchangeRates.link('SafeDecimalMath', safeMath.address)
  Synthetix.link('SafeDecimalMath', safeMath.address)
  SupplySchedule.link('SafeDecimalMath', safeMath.address)
  RewardEscrow.link('SafeDecimalMath', safeMath.address)
  Depot.link('SafeDecimalMath', safeMath.address)
  EtherCollateral.link('SafeDecimalMath', safeMath.address)
  Issuer.link('SafeDecimalMath', safeMath.address)
  Exchanger.link('SafeDecimalMath', safeMath.address)


  const lastMintEvent = 0;
  const currentWeek = 0;

  // Deploy resolver
  const resolver = await AddressResolver.new(owner, { from: owner});

  // Deploy issuer
  const issuer = await Issuer.new(owner, resolver.address, { from: owner});

  // Deploy exchanger and exchange state
  const exchanger = await Exchanger.new(owner, resolver.address, { from: owner});
  const exchangeState = await ExchangeState.new(owner, exchanger.address, { from: owner});



  /*
   * Deploy the ExchangeRates contract
   */
  const exchangeRates = await ExchangeRates.new(owner, oracle, currencyKeys.slice(1,2), currencyRates)

  // Deploy the feepool

  // Deploy FeePoolState and FeePoolEternalStorage
  const feePoolEternalStorage = await FeePoolEternalStorage.new(owner, zeroAddress)
  const feePoolState = await FeePoolState.new(owner, zeroAddress)
  const synthetixEscrow = await SynthetixEscrow.new(owner, zeroAddress)
  const synthetixStateForSynthetix = await SynthetixState.new(owner, zeroAddress)
  const supplySchedule = await SupplySchedule.new(owner, lastMintEvent, currentWeek)

  const transferFeeRate = toUnit(0.01)  // 1%
  const exchangeFeeRate = toUnit(0.01)  // 1%

  const SYNTHETIX_TOTAL_SUPPLY = web3.utils.toWei('100000000');
  /*
   * Deploy the FeePool contract
   */
  const proxyForFeePool = await Proxy.new(owner)
  const feePool = await FeePool.new(
    proxyForFeePool.address,
    owner,
    exchangeFeeRate,
    resolver.address
  )
  await feePoolState.setFeePool(feePool.address, { from: owner });
  await feePoolEternalStorage.setAssociatedContract(feePool.address, { from: owner });

  await proxyForFeePool.setTarget(feePool.address, { from: owner })
  await feePool.setProxy(proxyForFeePool.address, { from: owner })

  /*
  * Deploy a RewardsDistribution & RewardEscrow
  */
  const rewardEscrow = await RewardEscrow.new(owner, zeroAddress, feePool.address)
  const rewardsDistribution = await RewardsDistribution.new(
    owner,
    zeroAddress,
    zeroAddress,
    rewardEscrow.address,
    proxyForFeePool.address
  )
  // Deploy delegate approval rates

  const delegateApprovals = await DelegateApprovals.new(owner, feePool.address);


  /*
   * Deploy the Synthetix contract
   */
  const proxyForSynthetix = await Proxy.new(owner)
  const tokenStateForSynthetix = await TokenState.new(owner, owner)
  const synthetix = await Synthetix.new(
    proxyForSynthetix.address,
    tokenStateForSynthetix.address,
    owner,
    SYNTHETIX_TOTAL_SUPPLY,
    resolver.address,
    { from: owner }
  )

  // Give the owner half the supply:
  await tokenStateForSynthetix.setBalanceOf(owner, web3.utils.toWei('50000000'), {
  from: owner,
});


  await proxyForSynthetix.setTarget(synthetix.address, { from: owner })
  await synthetix.setProxy(proxyForSynthetix.address, { from: owner })
  await tokenStateForSynthetix.setAssociatedContract(synthetix.address, { from: owner })
  await synthetixStateForSynthetix.setAssociatedContract(issuer.address, { from: owner })


  // Update RewardsDistribution and RewardEscrow with the Synthetix address
  await rewardEscrow.setSynthetix(synthetix.address, { from: owner })
  await rewardsDistribution.setAuthority(synthetix.address, { from: owner })
  await rewardsDistribution.setSynthetixProxy(proxyForSynthetix.address, { from: owner })

  /*
   * Deploy a Synth contract for each of the currency keys.
   */
  let synths = {}
  let synthStates = {}
  let synthProxies = {}

  // Only some currencyKeys as no synths are issued for `HAV`
  for (var i in currencyKeys.slice(0,2)) {
    const currencyKey = currencyKeys[i]
    // const asciiKey = web3.utils.hexToAscii(currencyKey)
    // Create the Synth, along with its proxy and state.
    let synth, proxy, state;
    if (currencyKey === toBytes32('sETH')) {
      [synth, proxy, state] = await deployMultiCollateralSynth(owner, currencyKey, resolver)
    } else {
      [synth, proxy, state] = await deploySynth(owner, currencyKey, resolver)
    }
    // Add this Synth to the Synthetix contract.
    await synthetix.addSynth(synth.address, { from: owner })
    // Store the synth, proxy and state for later.
    synths[currencyKey] = synth
    synthStates[currencyKey] = state
    synthProxies[currencyKey] = proxy
  }
  // await synthetix.addSynth(synths['sUSD'].address, { from: owner })
  // await synthetix.addSynth(synths['sETH'].address, { from: owner })
  const usdEth = '274957049546843687330';
  const usdSnx = '127474638738934625';

  const depot = await Depot.new(
    owner,
    fundsWallet,
    resolver.address
  )

  const ethcol = await EtherCollateral.new(
    owner,
    resolver.address
  )

  // set up resolver:

  await resolver.importAddresses(
  [
    'DelegateApprovals',
    'Depot',
    'EtherCollateral',
    'Exchanger',
    'ExchangeRates',
    'ExchangeState',
    'FeePool',
    'FeePoolEternalStorage',
    'FeePoolState',
    'Issuer',
    'MultiCollateral',
    'RewardEscrow',
    'RewardsDistribution',
    'SupplySchedule',
    'Synthetix',
    'SynthetixEscrow',
    'SynthetixState',
    'SynthsETH',
    'SynthsUSD',
  ].map(toBytes32),
  [
    delegateApprovals.address,
    depot.address,
    ethcol.address,
    exchanger.address,
    exchangeRates.address,
    exchangeState.address,
    feePool.address,
    feePoolEternalStorage.address,
    feePoolState.address,
    issuer.address,
    ethcol.address, // MultiCollateral for Synth uses EtherCollateral
    rewardEscrow.address,
    rewardsDistribution.address,
    supplySchedule.address,
    synthetix.address,
    synthetixEscrow.address,
    synthetixStateForSynthetix.address,
    synths[toBytes32('sETH')].address,
    synths[toBytes32('sUSD')].address,
  ],
  { from: owner }
);


  /*
   * Return an object with all the useful parts
   */
  return {
    accounts: { owner, oracle, beneficiary, fundsWallet, feeAuthority },
    synthetixTokenState: tokenStateForSynthetix,
    synthetixState: synthetixStateForSynthetix,
    synthetix,
    synthetixProxy: proxyForSynthetix,
    synths,
    synthStates,
    synthProxies,
    feePool,
    exchangeRates,
    currencyKeys,
    supplySchedule,
    depot,
    ethcol
  }
}
module.exports.deployTestRig = deployTestRig
