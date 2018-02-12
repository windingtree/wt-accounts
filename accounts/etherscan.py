# -*- coding: utf-8 -*-
import logging

from collections import defaultdict

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


def get_transactions_response(startblock, endblock, internal=False):
    """
    :return: only successfull transactions
    """
    logger.debug('requests.get: startblock=%s, endblock=%s, internal=%s', startblock, endblock, internal)
    resp = requests.get('http://api.etherscan.io/api', params={
        'module': 'account',
        'action': 'txlistinternal' if internal else 'txlist',
        'address': settings.ETH_WALLET,
        'startblock': startblock,
        'endblock': endblock,
        'sort': 'asc',
        'apikey': settings.ETHERSCAN_TOKEN
    })
    # https://etherscan.io/apis#transactions
    return resp

def range_blocks(start, end, step):
    begins = range(start, end)[::step]
    ends = range(start,end)[step-1::step]
    return zip(begins, ends)

def get_transactions(internal=False):
    start = settings.ETH_STARTBLOCK
    end = settings.ETH_ENDBLOCK
    step = settings.ETH_BLOCKSTEP
    ret = []
    for startblock, endblock in range_blocks(start, end, step):
        ret += get_transactions_response(startblock, endblock, internal).json()['result']
    return ret

def filter_failed(transactions):
    return [one for one in transactions if one.get('isError', '0') == '0']

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
