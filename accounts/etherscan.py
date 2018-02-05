# -*- coding: utf-8 -*-
from collections import defaultdict

import requests
from django.conf import settings


def get_transactions(internal=False):
    """
    :return: only successfull transactions
    """
    resp = requests.get('http://api.etherscan.io/api', params={
        'module': 'account',
        'action': 'txlistinternal' if internal else 'txlist',
        'address': settings.ETH_WALLET,
        'startblock': '4000000',
        'endblock': '99999999',
        'sort': 'asc',
        'apikey': settings.ETHERSCAN_TOKEN
    })
    # https://etherscan.io/apis#transactions
    return [one for one in resp.json()['result'] if one.get('isError', '0') == '0']

def get_sum_for_accounts(transactions, accounts):
    accounts = [ a.lower() for a in accounts ]
    trans_by_account = defaultdict(list)
    for one in transactions:
        trans_by_account[one['from'].lower()].append(int(one['value']))

    return {account: sum(trans_by_account[account]) for account in accounts if
            account in trans_by_account}

def get_unique_contributions(transactions):
    froms = { one['from'] for one in transactions }
    return get_sum_for_accounts(transactions, froms)

def eth_get_total(transactions):
    return sum([int(one['value']) for one in transactions])
