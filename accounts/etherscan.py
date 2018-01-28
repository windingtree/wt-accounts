# -*- coding: utf-8 -*-
from collections import defaultdict

import requests
from django.conf import settings


def get_transactions():
    resp = requests.get('http://api.etherscan.io/api', params={
        'module': 'account', 'action': 'txlist',
        'address': settings.ETH_WALLET,
        'startblock': '4000000',
        'endblock': '99999999', 'sort': 'asc',
        'apikey': settings.ETHERSCAN_TOKEN
    })
    return resp.json()['result']


def get_sum_for_accounts(transactions, accounts):
    trans_by_account = defaultdict(list)
    for one in transactions:
        trans_by_account[one['from']].append(int(one['value']))

    return {account: sum(trans_by_account[account]) for account in accounts if
            account in trans_by_account}


def eth_get_total(transactions):
    return sum([int(one['value']) for one in transactions])
