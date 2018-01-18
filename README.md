## Install
```bash
python3 -m venv ENV || virtualenv --python=/usr/bin/python3 ENV
source ENV/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Create your `wt_accounts/settings/local.py` import the dev module
# if you want to get some developer goodies: `from .dev import *`.
echo 'from .dev import *' > wt_accounts/settings/local.py

# Now create a database and you will be able to run the dev server
./manage.py migrate
./manage.py runserver
```

Go to http://localhost:8000/accounts/registration

## TODO

https://github.com/onfido/api-python-client

https://documentation.onfido.com

