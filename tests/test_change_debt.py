import brownie
from brownie import Contract
from brownie import config
import math

# test passes as of 21-06-26


def test_change_debt(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    yfi,
    woofy,
    swapper
):
    # deposit to the vault after approving
    aidrop = 10*1e18
    startingWhale = token.balanceOf(whale)-aidrop
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.setDoHealthCheck(False, {"from": gov})
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # evaluate our current total assets
    old_assets = vault.totalAssets()
    startingStrategy = strategy.estimatedTotalAssets()

    # debtRatio is in BPS (aka, max is 10,000, which represents 100%), and is a fraction of the funds that can be in the strategy
    currentDebt = 10000
    vault.updateStrategyDebtRatio(strategy, currentDebt / 2, {"from": gov})
    # sleep for a day to make sure we are swapping enough (Uni v3 combined with only 6 decimals)
    chain.sleep(86400)
    strategy.setDoHealthCheck(False, {"from": gov})
    strategy.harvest({"from": gov})
    chain.sleep(1)

    assert strategy.estimatedTotalAssets() <= startingStrategy

    # simulate one day of earnings
    chain.sleep(86400)
    chain.mine(1)
    token.transfer(vault, aidrop, {"from": whale})

    # set DebtRatio back to 100%
    vault.updateStrategyDebtRatio(strategy, currentDebt, {"from": gov})
    chain.sleep(1)
    strategy.setDoHealthCheck(False, {"from": gov})
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # evaluate our current total assets
    new_assets = vault.totalAssets()

    # confirm we made money, or at least that we have about the same
    assert new_assets >= old_assets or math.isclose(
        new_assets, old_assets, abs_tol=5)

    # simulate a day of waiting for share price to bump back up
    chain.sleep(86400)
    chain.mine(1)

    # withdraw and confirm our whale made money

    print(yfi.balanceOf(swapper))
    print(woofy.balanceOf(swapper))

    print(strategy.estimatedTotalAssets())
    print(vault.strategies(strategy).dict())
    vault.withdraw({"from": whale})
    assert token.balanceOf(whale) >= startingWhale
