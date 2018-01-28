#!/bin/bash


SUDO_WEB="sudo -HE -u web"
SUDO_ROOT="sudo"
VENV_DIR="~web/venv"
SRC_DIR="~web/src"
SETTINGS="wt_accounts.settings.production"

deploy() {

    ssh "$1" -At <<EOF

        set -xve

        echo \$SSH_AUTH_SOCK
        $SUDO_ROOT chown web:web -R \$(dirname "\$SSH_AUTH_SOCK")    
        cd $SRC_DIR && $SUDO_WEB git pull
        $SUDO_ROOT chown \$(whoami):\$(whoami) -R \$(dirname "\$SSH_AUTH_SOCK")    

        $SUDO_WEB $VENV_DIR/bin/pip install -r $SRC_DIR/requirements.txt

        $SUDO_WEB $VENV_DIR/bin/python $SRC_DIR/manage.py migrate --no-input --settings=$SETTINGS
        $SUDO_WEB $VENV_DIR/bin/python $SRC_DIR/manage.py collectstatic --clear --no-input --settings=$SETTINGS
        # $SUDO_WEB $VENV_DIR/bin/python $SRC_DIR/manage.py compilemessages --settings=$SETTINGS
        date '+%s' | $SUDO_WEB tee $SRC_DIR/deploy_timestamp

        $SUDO_ROOT supervisorctl update
        $SUDO_ROOT supervisorctl restart web-1
        $SUDO_ROOT supervisorctl restart web-2
        sudo /etc/init.d/nginx reload

EOF

}

deploy ubuntu@wt-web-1
deploy ubuntu@wt-web-2
