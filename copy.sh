#! /bin/bash
[ "$UID" -eq 0 ] || exec sudo "$0" "$@"
cp config.ini /var/www/tg-bot/
cp app.py /var/www/tg-bot/
cp *.pem /var/www/tg-bot/
chown -R  www-data:www-data /var/www/tg-bot/
chown -R  www10177:www10177 /var/www/tg-bot/bot

