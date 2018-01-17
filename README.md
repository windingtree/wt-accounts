## Install
```
python3 -m venv ENV || virtualenv --python=/usr/bin/python3 ENV
source ENV/bin/activate
pip install -r requirements.txt
```

## Usage

Create your `settings/local.py` import the dev module if you want to get
some developer goodies `from .dev import *`.

```
./manage.py migrate
./manage.py runserver
```

Go to `http://localhost:8000/accounts/login`

## TODO

https://github.com/onfido/api-python-client

https://documentation.onfido.com

