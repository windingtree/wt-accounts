import pickle, zlib

from django.core.management.base import BaseCommand

from django.core.cache import cache

from accounts import models, etherscan

class Command(BaseCommand):
    help = 'fill how much did one user contribute'

    def handle(self, *args, **options):
        users = models.User.objects.exclude(eth_address='')
        users_by_eth_address = {u.eth_address.lower(): u for u in users}

        all_transactions = etherscan.get_transactions() + etherscan.get_transactions(internal=True)
        transactions = etherscan.filter_failed(all_transactions)

        # cache forever
        cache.set(etherscan.CACHE_KEY, zlib.compress(pickle.dumps(all_transactions)), timeout=None)

        total = etherscan.eth_get_total(transactions)
        sum_for_accounts = etherscan.get_sum_for_accounts(transactions, users_by_eth_address.keys())

        unique_contributions = etherscan.get_unique_contributions(transactions)
        unique_contributions_sum = int(sum( v for (a,v) in unique_contributions.items() )) / 10**18
        registered_contributions = [ (a,v) for (a,v) in sum_for_accounts.items() if v > 0 ]
        registered_contributions_sum = int(sum( v for (a,v) in sum_for_accounts.items() )) / 10**18


        self.stdout.write('stats>')
        self.stdout.write('total tx: {}'.format(len(all_transactions)))
        self.stdout.write('clear tx: {}'.format(len(transactions)))
        self.stdout.write('total eth: {}'.format(total / 10**18))
        self.stdout.write('number of tx from unique contributors: {}'.format(len(unique_contributions)))
        self.stdout.write('value of contributions: {}'.format(unique_contributions_sum))
        self.stdout.write('number of registered contributions: {}'.format(len(registered_contributions)))
        self.stdout.write('value of registered contributions: {}'.format(registered_contributions_sum))
        self.stdout.write('number of users: {}'.format(len(users)))
        self.stdout.write('~~~~~~')

        for account, sum_ in sum_for_accounts.items():
            user = users_by_eth_address[account]
            self.stdout.write('User {u} contributed {s} form {u.eth_address}'.format(u=user, s=sum_))
            users_by_eth_address[account].eth_contrib = str(sum_)
            users_by_eth_address[account].save(update_fields=['eth_contrib'])

