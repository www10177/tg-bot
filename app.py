# -*- coding: UTF-8 -*-
from flask import *
import telegram
from telegram.ext import Updater
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
"""
reload(sys)
sys.setdefaultencoding("utf-8")
tw = pytz.timezone('Asia/Taipei')
"""


app = Flask(__name__)
LOGFORMAT='%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.DEBUG,format=LOGFORMAT)
fh = logging.FileHandler(datetime.now().strftime('/home/www10177/logs/tg-bot/%Y%m%d.txt'),)
logging.getLogger ('').addHandler(fh)
main_group_id= -1001249646387
bot_name = '@TianTaiBot'
# Channel Access Token
global bot
global token
config= configparser.ConfigParser()
config.read('/var/www/tg-bot/config.ini')
token=config['TELEGRAM']['TOKEN']
print(token)
bot=telegram.Bot(token=token)
backup_msg=[]
logging_msg=[]

# Channel Secret
@app.route('/')
def hello():
    return 'Hello World!!'
@app.route('/tg', methods=['POST'])
def launcher():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
#logging.info(update)
        '''
        message= update.message
        handle_msg(message)
        '''
        message= update.message
        if len(sys.argv) > 1 :
            logging.debug('Clean Message')
            return 'ok'
        if message is None or message.text is None:
            logging.debug("ERROR : " + ' is not text')
            return 'ok'
        try:
            handle_msg(message)
            123
        except:
            logging.info("ERROR : " +message)
    return 'ok'


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
def backup(msg,chat_id):
    if msg.chat_id != chat_id :
        logging.debug('not backup %s'%msg.chat_id)
        return
    try:
        name = msg.from_user.first_name.encode('utf-8')+msg.from_user.last_name.encode('utf-8')
        raw_time= msg.date+datetime.timedelta(hours=12)
        time = raw_time.strftime('%Y-%m-%d %H:%M:%S')
        backup_msg.append({'time':time,'name':name,'text':msg.text.encode('utf-8')})
        logging.debug(backup_msg[-1])
        if len(backup_msg)>250:
            backup_msg.pop(0)
        else:
            logging.info('msg backup length now :%d'%len(backup_msg))
    except:
        logging.warning('Backup Error')
        logging.warning(msg)
            

def handle_text(message):
#backup(message,main_group_id)
    text =message.text.encode('utf-8')
    text = text.lower()
    text_stripped = text.strip()
    if message.chat_id == main_group_id:
        logging.info('STRIPPED_MSG : {}'.format(text_stripped))
    else :
        print ('BOT get : ' + text_stripped)
    if u"天臺" in text or u"天台" in text in text or text_stripped.startswith('/price'):
        return price()
    elif text_stripped == "/command":
     return cmd_str
    elif text_stripped == "/show":
        return show()
    elif text_stripped.startswith('/lmgtfy'):
        return lmgtfy(text_stripped)
    elif text_stripped.startswith('/cal'):
        return calculate(text_stripped)
    elif '林北爽兵' in text:
        now = datetime.now(timezone('Asia/Taipei')).date()
        now_time = datetime.now(timezone('Asia/Taipei'))
        out = datetime(2019,2,27).date()
        in_date = datetime(2018,11,8).date()
        next_sat = now + timedelta((12-now.weekday())%7)
        next_sat = datetime.combine(next_sat,time(hour=8,minute=0,tzinfo=timezone('Asia/Taipei')))
        delta_next_sat = next_sat - now_time
        delta_next_sat = delta_next_sat.days*24+ delta_next_sat.seconds//3600
        delta_in = now - in_date
        delta = out-now
        delta_in = delta_in.days
        delta = delta.days
        return "下次鬼門開： %s, 還有%d 小時QAQ\n返陽日：%s, 倒數 : %d天, 入殮已%d天, 登出進度: %.2f %%" %(next_sat.strftime('%m/%d'),delta_next_sat,out.strftime('%Y/%m/%d'),delta,delta_in, (1-(float(delta)/115))*100)
    return ''
def handle_msg(message):
    text = message.text
    text = text.encode('utf-8')
#logtofile(text)
    result=handle_text(message)
#logging.info("send : %s"%result)
    if result is not '':
        bot.sendMessage(chat_id=message.chat.id,text=result,disable_web_page_preview=False,parse_mode='MarkDown')

def logtofile(msg,freq = 10,fp='./textlog/'):
    logging_msg.append(msg)
    if len(msg) >= freq:
        fname = os.path.join(fp,datetime.now(timezone('Asia/Taipei').strftime('%Y%m%d')))
        f.write(i+'\n')
        logging_msg = []
        
        


if __name__ == "__main__":
    app.run(host='192.168.88.187',ssl_context=('cert.pem', 'key.pem'),threaded=True)
