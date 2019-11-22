# -*- coding: UTF-8 -*-
from flask import *
import telegram
from telegram.ext import Dispatcher,MessageHandler,Filters,CommandHandler
import requests
from parse import *
import logging
import os
import sys
from urllib.parse import quote
import pytz
from sys import argv
from datetime import datetime, timedelta,time
from pytz import timezone
import configparser

app = Flask(__name__)

#Logging

LOGFORMAT='%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.DEBUG,format=LOGFORMAT)
fh = logging.FileHandler(datetime.now().strftime('/home/www10177/logs/tg-bot/%Y%m%d.txt'),)
logging.getLogger ('').addHandler(fh)

#Basic Config for This BOT
main_group_id= -1001249646387
bot_name = '@TianTaiBot'

#Config Parser
config= configparser.ConfigParser()
config.read('/var/www/tg-bot/config.ini')

#BOT Initilize
token=config['TELEGRAM']['TOKEN']
bot=telegram.Bot(token=token)


@app.route('/tiantai', methods=['POST','GET'])
def webhook_handler():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force = True),bot)
        dispatcher.process_update(update)
        return 'ok'
    else :
        return 'Hi! I\'m TianTaiBOT!'




def get_eth():
    ticket = requests.get('https://api.coinmarketcap.com/v1/ticker/ethereum/')
    ticket2 = requests.get('https://bb.otcbtc.com/api/v2/tickers/ethusdt')
    json = ticket.json()[0]
    price=json['price_usd']
    percent=json['percent_change_24h']
    json = ticket2.json()['ticker']
    buy = json['buy']
    sell = json['sell']
    return [price,percent,buy,sell]

def price():
    eth=get_eth()
    price = eth[0]
    percent = eth[1]
    back = u'價格 : ${} \n24hr 變化幅度 : {}% \n'.format(price, percent)
    back += u'還不快跳？' if percent[0] =='-' else u'準備起飛啦，甭跳吧' 
    back += u'\notcbtc 買賣價格 : ${:0,.2f}/${:0,.2f}(USDT)'.format(float(eth[2]),float(eth[3]))
    return back

def lmgtfy(text_stripped):
    parsed = parse('/lmgtfy {}',text_stripped)
    print(parsed)
    return '[Let me Google %s for you](https://lmgtfy.com/?q=%s )' %(parsed[0].upper(),quote(parsed[0]))

def calculate(text_stripped):
    parsed = parse('/cal {}',text_stripped)
    parsed = parsed[0].strip()
    try :
        result = '%s = %s' %(parsed.replace('*','x'), str(eval(parsed)))
    except:
        result = 'cannot calculate it...'
    return result

cmd_str = '''
        /price | Show the ETH price
        /lmgtfy $1| Let the bot google that for you
        /cal EXP | calculate the mathematic expression
        '''

def handle_text(chat_text):
    text =chat_text
    text = text.lower()
    text_stripped = text.strip()
    logging.info(chat_text)
    if "天臺" in text or "天台" in text in text :
        return price()
    elif '免役'  in text:
        return '閉嘴醜男'
    elif text_stripped == "/command":
     return cmd_str
    elif text_stripped == "/show":
        return show()
    elif text_stripped.startswith('/lmgtfy'):
        return lmgtfy(text_stripped)
    elif text_stripped.startswith('/cal'):
        return calculate(text_stripped)
    else :
        return None

def text_reply_handler(update,context):
    text = update.message.text
    reply = handle_text(text)
    if reply is not None :
        update.message.reply_text(reply)
def price_cmd_handler(update,context):
    reply = price()
    update.message.reply_text(reply)

#dispatcher Setu
dispatcher = Dispatcher(bot,update_queue = None,use_context=True)
dispatcher.add_handler(MessageHandler(Filters.text, text_reply_handler))
dispatcher.add_handler(CommandHandler('price', price_cmd_handler))
        
        


if __name__ == "__main__":
    app.run(host='192.168.88.187',threaded=True)
