# -*- coding: UTF-8 -*-
from flask import *
import telegram
from telegram.ext import Dispatcher,MessageHandler,Filters,CommandHandler
from linebot import  LineBotApi, WebhookHandler
from linebot.exceptions import  InvalidSignatureError
from linebot.models import  (
    MessageEvent,PostbackEvent, TextMessage, TextSendMessage,TemplateSendMessage,ButtonsTemplate,MessageAction,PostbackAction,ConfirmTemplate
)
import requests
from parse import *
from logging.config import dictConfig
import os
from urllib.parse import quote
import pytz
from datetime import datetime, timedelta,time,date
from pytz import timezone
import configparser
import sqlite3 
import pickle


#Logging
#'format': '%(asctime)s - %(name)6s - %(levelname)s - %(message)s',
dictConfig({
        'version': 1,
        'formatters': {'default': {
                    'format': '%(asctime)s - %(levelname)s - %(message)s',
                }},
        'handlers': {'wsgi': {
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://flask.logging.wsgi_errors_stream',
                    'formatter': 'default',
                    },
                    'file': {
                        'class':'logging.FileHandler',
                        'filename':'/home/www10177/logs/tg-bot/log.txt',
                        'formatter':'default',
                    }
        },
        'root': {
                    'level': 'INFO',
                    'handlers': ['wsgi','file']
                },

})

#Config Parser
config= configparser.ConfigParser()
config.read('/var/www/tg-bot/config.ini')

#Global Timezone
taipei= timezone('Asia/Taipei')

app = Flask(__name__)

@app.before_first_request
def init():
    #Initialize Database
    with sqlite3.connect(lw_db) as conn:
        cursor=conn.cursor()
        cursor.execute(r"SELECT count(name) FROM sqlite_master WHERE type ='table' AND name='working_hours'")
        if cursor.fetchone()[0] == 1:
            app.logger.debug('connected to working_hours table')
        else :
            cursor.execute('''CREATE TABLE working_hours( 
                           id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           userid TEXT NOT NULL,
                           time DATETIME NOT NULL,
                           period INTEGER NOT NULL,
                           title TEXT)''')
            cursor.execute(r'PRAGMA encoding="UTF-8";')
            app.logger.info('Created working_hours table')
    '''
    #Load Killed Session
    path = '/tmp/'
    app.logger.info('Receive Quit SIGNAL, Save files to %s'%path)
    global session_dict #UserId : Start_time 
    global end_session_dict #  UserId : end_time
    fp = path+'bot_session.pkl'
    if os.path.exists(fp):
        app.logger.info('Previous Receive Quit SIGNAL, Load %s'%fp)
        with open(fp,'r') as f:
            session_dict = pickle.load(f)
    fp = path+'bot_endsession.pkl'
    if os.path.exists(fp):
        app.logger.info('Previous Receive Quit SIGNAL, Load %s'%fp)
        with open(fp,'r') as f:
            end_session_dict = pickle.load(f)
    '''


@app.route('/',methods=['GET'])
def main_page():
    return 'this is mainapge'
###########################################################################################
####################              TG-TIANTAI-BOT              #############################
###########################################################################################
bot_name = '@TianTaiBot'
tiantai_token=config['TELEGRAM']['TIANTAI_TOKEN']
tiantai_bot=telegram.Bot(token=tiantai_token)

@app.route('/tiantai', methods=['POST','GET'])
def tiantai():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force = True),tiantai_bot)
        tiantai_dispatcher.process_update(update)
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
def handle_text(chat_text):
    cmd_str = '''
    /price | Show the ETH price
    /lmgtfy $1| Let the bot google that for you
    /cal EXP | calculate the mathematic expression
    '''
    text =chat_text
    text = text.lower()
    text_stripped = text.strip()
    app.logger.info('TIANTAI : ',chat_text)
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


#Dispatcher Setup
tiantai_dispatcher = Dispatcher(tiantai_bot,update_queue = None,use_context=True)
tiantai_dispatcher.add_handler(MessageHandler(Filters.text, text_reply_handler))
tiantai_dispatcher.add_handler(CommandHandler('price', price_cmd_handler))

###########################################################################################
####################              LINE-WORKING-BOT                  #######################
###########################################################################################



lw_api= LineBotApi(config['LINE']['WORKING_TOKEN'])
lw_handler= WebhookHandler(config['LINE']['WORKING_SECRET'])
session_dict={}# Userid : starttime
end_session_dict ={} # Userid : endtime
lw_db= config['PATH']['DB']

@app.route('/line-working',methods=['POST','GET'])
def line_working():
    if request.method == "POST":
        signature = request.headers['X-Line-Signature']
        # get request body as text
        body = request.get_data(as_text=True)
        try:
            lw_handler.handle(body, signature)
        except InvalidSignatureError:
            print("Invalid signature. Please check your channel access token/channel secret.")
            abort(400)
        return 'ok'
    else :
        return 'Work Hard, Play Hard.'
@lw_handler.add(MessageEvent,message=TextMessage)
def line_working_handle_message(event):
    text = event.message.text.lower()
    userid = event.source.user_id
    app.logger.info('LINE-WORKING : From %s received : %s'%(userid, text))
    app.logger.debug(session_dict)
    app.logger.debug(end_session_dict)
    if text.startswith('/stop'):
        if userid in session_dict:
            time = datetime.now()
            button = TemplateSendMessage(alt_text='停止計時',
                                         template=ConfirmTemplate(  text='停止計時, 是否紀錄工作內容',
                                                                  actions=[ PostbackAction( label='Yes', display_text='紀錄工作內容', data='title'),
                                                                           PostbackAction( label='No', display_text='不紀錄工作內容', data='notitle')]))
            app.logger.debug(end_session_dict)
            if userid not in end_session_dict:
                end_session_dict[userid]=time
                app.logger.debug('add user to end_session')
            lw_api.reply_message(event.reply_token,button)
        else: 
            lw_api.reply_message(event.reply_token,\
                                 TextSendMessage(text=r'請先"開始計時" (輸入/start) '))
    elif userid in end_session_dict and not text.startswith('@'):
        lw_api.reply_message(event.reply_token,
                             TextSendMessage(text='請先按下不紀錄工作內容的按鈕，或輸入工作內容\n指令:@工作內容\nExample : @耍廢'))
                             
    elif text.startswith('/start'):
        app.logger.debug(session_dict)
        if userid in session_dict:
            button = TemplateSendMessage(alt_text='重新計時?',
                                         template=ConfirmTemplate(  text='存在尚未停止的計時，是否重新計時？',
                                                                  actions=[ PostbackAction( label='Yes', display_text='重新計時', data='restart'),
                                                                           PostbackAction( label='No', display_text='保留目前計時狀態', data='remain') ]))
            lw_api.reply_message(event.reply_token,button)
        else:
            try :
                time = start_recording(userid)
                text = '開始計時，開始時間: %s'%time
            except:
                text = '開始計時失敗'
                app.logger.error('LINE-WORKER : /start ERROR',userid,session_dict)
            lw_api.reply_message(event.reply_token,
                                 TextSendMessage(text=text))

    elif text.startswith('/add'):
        reply_text='請輸入 \"@新增 工作內容 工時(hr)\"\nExample: /add 耍廢 3.2   ====> 耍廢3.2hr'
        lw_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    elif text.startswith('@新增 ') and userid not in end_session_dict:
        parsed = text.split(' ')
        try :
            time = datetime.now()
            period = float(parsed[2])
            period = int(period*3600)
            time= datetime.strftime(time,'%Y-%m-%d')
            title = parsed[1]
            var = (userid,time,period,title)
            with sqlite3.connect(lw_db) as conn:
                cursor=conn.cursor()
                cursor.execute('INSERT INTO working_hours (userid,time,period,title) VALUES(?,?,?,?)',var)
            reply_text = '成功新增 %s - %sHR - %s' %(time, parsed[2],title)
        except :
            reply_text='請輸入 \"@新增 工作內容 工時(hr)\"\nExample: /add 耍廢 3.2   ====> 耍廢3.2hr'
        lw_api.reply_message(event.reply_token,
                                 TextSendMessage(text=reply_text))
    elif (text.startswith('/report') or text.startswith('@report')) and userid not in end_session_dict:
        def sec2time(total_seconds):
            sum_h,remainder = divmod( total_seconds,3600)
            sum_m,sum_s = divmod(remainder,60)
            return (sum_h,sum_m,sum_s)
        days = 15
        if len(text.split(' ') )>1:
            try :
                days = int(text.split(' ')[1])
            except :
                text = '若欲指定近n天的工作統計請用\"@report n\"\n n 為自然數'
                lw_api.reply_message(event.reply_token,\
                                     TextSendMessage(text=text))
                return
        startdate = date.today() - timedelta(days=days)
        startdate = datetime.strftime(startdate,'%Y-%m-%d')
        text = '若欲指定近n天的工作統計請用\"/report n\"\n'
        text += '以下為近%d天的工作內容 : \n'%days
        text += '%s-%s-%s\n'%('日期','工時(HH:MH:SS)','工作內容')
        with sqlite3.connect(lw_db) as conn:
            cursor=conn.cursor()
            cursor.execute('SELECT * FROM working_hours WHERE userid == ? AND  time >= ? ORDER BY time ASC',(userid,startdate))
            formatstr='%s-%s-%s\n'
            records = cursor.fetchall()
        total_seconds = 0
        for _id,_userid,_time,_period,_title in records:
            period_str ='%02d:%02d:%02d'%sec2time(_period)
            text+=formatstr %(_time[5:].replace('-','/'),period_str,_title)#Remove Year
            total_seconds += _period
        text += '總時長(HH:MM:SS) : %02d:%02d:%02d'%sec2time(total_seconds)
        lw_api.reply_message(event.reply_token,
                             TextSendMessage(text=text))
    elif text.startswith('@'): 
        if userid not in session_dict:
            text = '不存在尚未儲存的計時階段，請先開始計時'
        else :
            if userid not in end_session_dict:
                text = '請先輸入\"/stop\"以終止目前的計時階段'
            else:
                title = text[1:]
                var = stop_recording(userid,title)
                text ='成功紀錄: %s : %.1f HR - %s'%(var[1],var[2]/3600,var[3])
        lw_api.reply_message(event.reply_token,\
                             TextSendMessage(text=text))
        

@lw_handler.add(PostbackEvent)
def line_working_postback(event):
    data= event.postback.data
    userid = event.source.user_id
    app.logger.debug('LINE-WORKER : POSTBACK : ')
    app.logger.debug(data)
    text ='NULL'
    if data == 'restart':
        app.logger.debug('LINE-WORKER : restart: drop ',userid)
        try :
            session_dict.pop(userid)
            time = start_recording(userid)
            text = '成功重新計時，開始時間: %s'%time
        except :
            text = '重新計時失敗：不存在已開始的計時階段'
            app.logger.error('LINE-WORKER : restart ERROR',userid,session_dict)
    elif data == 'remain':
        now = datetime.now()
        period =datetime.now()
        if userid in session_dict: 
            now = datetime.now()
            periods = now - session_dict[userid]
            hours = periods.total_seconds() /3600 
            text = '請先結束上個計時階段 (已持續 %.1f 小時)'%hours
        else:
            text = '不存在已開始的計時階段，不要玩我QQ'
    elif data == 'title':
        if userid in session_dict: 
            text ='請用指令 \"@工作內容\"來記錄，\
                   Examples : @耍廢'
        else:
            text = '不存在已開始的計時階段，不要玩我QQ'
    elif data =='notitle':
        try :
            app.logger.debug('LINE-WORKER :notitle enter') 
            var=stop_recording(userid,'無工作內容')
            text ='成功紀錄: %s : %.1f HR - %s'%(var[1],var[2]/3600,var[3])
        except: 
            text ='紀錄失敗，不存在尚未儲存的計時階段'
    else:
        app.logger.error('LINE-WORKER : POSTBACK : GETEXCEPTION',data)
    lw_api.reply_message(event.reply_token,\
                         TextSendMessage(text=text))

def start_recording(userid):
    if userid in session_dict:
        raise 'Start RECORDING　ERROR'
    else:
        t = datetime.now()
        session_dict[userid] = t
        return datetime.strftime(t,'%Y/%m/%d - %H:%M:%S')
def stop_recording(userid,text):
    app.logger.debug('LINE-WORKER :stop-recording')
    app.logger.debug(session_dict)
    app.logger.debug(end_session_dict)
    if userid not in session_dict:
        app.logger.debug('not in session_dict')
        raise 'STOP RECORDING　ERROR'
    else:
        if userid not in end_session_dict:
            app.logger.error('LINE-WORKER : STOP: GETEXCEPTION',userid, session_dict,end_session_dict)
            app.logger.debug('not in end session_dict')
            raise 'STOP ERROR  USERID NOT IN END_TIME'
        else :
            app.logger.debug('in both session_dict')
            endtime = end_session_dict[userid]
    starttime = session_dict[userid] 
    period = endtime-starttime
    period = int(period.total_seconds())
    starttime = datetime.strftime(starttime,'%Y-%m-%d')
    var = (userid,starttime,period,text)
    with sqlite3.connect(lw_db) as conn:
        cursor=conn.cursor()
        cursor.execute('INSERT INTO working_hours (userid,time,period,title) VALUES(?,?,?,?)',var)
    session_dict.pop(userid)
    end_session_dict.pop(userid)
    return var
'''
def save_file(a):
    path = '/tmp/'
    app.logger.info('Receive Quit SIGNAL, Save files to %s'%path)
    with open(path+'bot_session.pkl','w') as f:
        pickle.dump(session_dict,f)
    with open(path+'bot_endsession.pkl','w') as f:
        pickle.dump(end_session_dict,f)
'''










if __name__ == "__main__":
    app.run(host='192.168.88.187',threaded=True)
