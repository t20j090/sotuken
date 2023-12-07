from flask import Flask, request, abort
from bs4 import BeautifulSoup
import datetime
import os
import re
import requests
import time

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    AudioSendMessage, MessageEvent, TextMessage, TextSendMessage
)

from linebot.models import FlexSendMessage
from linebot.models.flex_message import BubbleContainer
from gtts import gTTS
import dropbox
from dropbox.exceptions import AuthError
import tempfile


app = Flask(__name__)

yahoo_categories = ['国内', '国際', '経済', 'エンタメ', 'スポーツ', 'IT', '科学', 'ライフ']
cnn_categories = ['World', 'USA', 'Business', 'Tech', 'Entertainment', 'Odd News']
cnn_categories_change = ['世界', 'アメリカ', '経済', 'テクノロジー', 'エンタメ', '変わったニュース']
sankei_categories = ['社会', '政治', '国際', '経済', 'スポーツ', 'エンタメ', 'ライフ']
news_sites = ['ヤフーニュース', 'CNNニュース', '産経ニュース', '要約', '音声変換']

# 0:ヤフーニュース 1:CNNニュース 2:産経ニュース
news_flag = 0

#0:要約しない 1:要約する
summary_flag = 0

#0:音声変換しない 1:音声変換する
text_to_speech_flag = 0

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

# Dropboxアプリのキーとシークレット
app_key = '7cxbb0znnuk211n'
app_secret = 'p41f3wefjt3blmw'

# アクセストークン 
access_token = 'sl.BrQvSFEKU2Fay_hLDdfzbHS5ZNKlsYyf6Cp2xiYTCDSHV0ZTLN_Xv4J9izQJ1MeBw3Wp0ta1LR24UOWHBaZJVy9G6sjYrz5NtUf9Xc5hPA2NDnylw5aNA1qA17ldmr3NVbXRd64hhrXE79c'    
dbx = dropbox.Dropbox(access_token)


@app.route("/")
def hello_world():
    return "hello world!"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# ボタンメッセージのFlex Messageを作成する関数
def create_button_message():
    if (news_flag == 1):
        bubble = BubbleContainer(
            body={
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "最新の人気ニュース",
                        "weight": "bold",
                        "size": "xl",
                    },
                    {
                        "type": "text",
                        "text": "興味のあるカテゴリーを押してください",
                        "color": "#888888",
                        "margin": "lg",
                    },
                ],
            },
            footer={
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "世界",
                            "text": "世界",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "アメリカ",
                            "text": "アメリカ",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "経済",
                            "text": "経済",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "テクノロジー",
                            "text": "テクノロジー",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "エンタメ",
                            "text": "エンタメ",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "変わったニュース",
                            "text": "変わったニュース",
                        },
                    },
                ],
            },
        )

        flex_message = FlexSendMessage(alt_text="ボタンメッセージ", contents=bubble)
        return flex_message
    elif(news_flag == 0):
        bubble = BubbleContainer(
            body={
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "最新の人気ニュース",
                        "weight": "bold",
                        "size": "xl",
                    },
                    {
                        "type": "text",
                        "text": "興味のあるカテゴリーを押してください",
                        "color": "#888888",
                        "margin": "lg",
                    },
                ],
            },
            footer={
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "国内",
                            "text": "国内",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "国際",
                            "text": "国際",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "経済",
                            "text": "経済",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "エンタメ",
                            "text": "エンタメ",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "スポーツ",
                            "text": "スポーツ",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "IT",
                            "text": "IT",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "科学",
                            "text": "科学",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "ライフ",
                            "text": "ライフ",
                        },
                    },
                ],
            },
        )

        flex_message = FlexSendMessage(alt_text="ボタンメッセージ", contents=bubble)
        return flex_message
    elif(news_flag == 2):
        bubble = BubbleContainer(
            body={
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "最新の人気ニュース",
                        "weight": "bold",
                        "size": "xl",
                    },
                    {
                        "type": "text",
                        "text": "興味のあるカテゴリーを押してください",
                        "color": "#888888",
                        "margin": "lg",
                    },
                ],
            },
            footer={
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "社会",
                            "text": "社会",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "政治",
                            "text": "政治",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "国際",
                            "text": "国際",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "経済",
                            "text": "経済",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "スポーツ",
                            "text": "スポーツ",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "エンタメ",
                            "text": "エンタメ",
                        },
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "ライフ",
                            "text": "ライフ",
                        },
                    },
                ],
            },
        )

        flex_message = FlexSendMessage(alt_text="ボタンメッセージ", contents=bubble)
        return flex_message
        
        
# ボタンメッセージを送信
def send_button_message(user_id):
    flex_message = create_button_message()
    line_bot_api.push_message(user_id, messages=flex_message)

#上位5位のヤフーニュースを取得
def yahoo_news_ranking():
    url = 'https://news.yahoo.co.jp'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    #クラス名が変わるので注意！！
    elements = soup.select('.sc-fXazdy.UjHkE')
    elements = elements[:5]
    
    news_urls = []
    for element in elements:
        link = element.a['href']
        news_urls.append(link)
    
    return news_urls

#上位3位のCNNニュースを取得
def cnn_news_ranking():
    url = 'https://www.cnn.co.jp/world/'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    elements = soup.select('.list-rank li a')

    news_urls = []
    news_titles = []
    # ニュースのURLとタイトルを取得
    for element in elements:
        link = 'https://www.cnn.co.jp' + element.get('href')
        news_urls.append(link)
    
    return news_urls

#上位5位の産経ニュースを取得
def sankei_news_ranking():
    url = 'https://www.sankei.com/'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    
    elements = soup.select('.ranking__item')
    
    news_urls = []
    # ニュースのURLとタイトルを取得
    for element in elements:
        link = element.a['href']
        news_urls.append(link)
    
    return news_urls

def send_news_ranking():
    if (news_flag == 0):
        news_urls = yahoo_news_ranking()
        messages = [TextSendMessage(text=url) for url in news_urls]
        line_bot_api.broadcast(messages=messages)
    elif (news_flag == 1):
        news_urls = cnn_news_ranking()
        messages = [TextSendMessage(text=url) for url in news_urls]
        line_bot_api.broadcast(messages=messages)
    elif (news_flag == 2):
        news_urls = sankei_news_ranking()
        messages = [TextSendMessage(text=url) for url in news_urls]
        line_bot_api.broadcast(messages=messages)


# 現在の時刻を取得
now = datetime.datetime.now().time()

# 判定する時間帯を設定（開始時刻・終了時刻から-9時間する必要がある）
start_time = datetime.time(4, 40)  # 開始時刻
end_time = datetime.time(5, 20)   # 終了時刻

#現在の日付を取得
# t_delta = datetime.timedelta(hours=9)
# JST = datetime.timezone(t_delta, 'JST')
# now = datetime.datetime.now(JST)
# current_time = now.strftime('%Y/%m/%d %H:%M:%S')


# 判定条件
if (start_time <= now <= end_time):
   send_news_ranking()
#else:
   #line_bot_api.push_message(user_id, TextSendMessage(text='送信できません'))


        
#ヤフーニュースの情報を取得
def yahoo_news_scraping(topic):
    url = 'https://news.yahoo.co.jp/'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    
    list_item = soup.find_all('li')
    #もしかしたらエラーの原因になるかも
    list_item = list_item[12:21]
    
    # <a>要素からトピックを取得
    a_contents = [li.a for li in list_item]
    
    articles_dict = []
    topic = topic 
    #トピックのURL取得
    for i, a_content in enumerate(a_contents):
        if topic in a_content.text:
            categories_num = i
    
    a_content = a_contents[categories_num]
    
    topic_url = a_content['href']
    URL = url + topic_url
    
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, "html.parser")
    #クラス名が変わるので注意！！
    elements = soup.select('.sc-fXazdy.UjHkE')
    
    elements = elements[:5]
    
    news_urls = []
    news_titles = []
    #ニュースのURLとタイトルを取得
    for element in elements:
        url = element.a['href']
        title = element.text[1:]
        news_urls.append(url)
        news_titles.append(title)
            
    news_text = []
    #ニュースの本文を取得
    for news_url in news_urls:
        r = requests.get(news_url)
        soup = BeautifulSoup(r.text, "html.parser")
        #クラス名が変わるので注意！！ 
        elements = soup.select('.sc-ksXiki.dXXEDb.yjSlinkDirectlink.highLightSearchTarget')
    
        text = ""
    
        #ニュース記事の本文が配列で区切られていた場合
        for i in range(0, 8):
            try:
                if (i == 0):
                    text = elements[0].text
                else:
                    text += elements[i].text
            except:
                pass
    
        #ページが1つだけのとき、エラーが出るため
        try:
            #クラス名が変わるので注意！！ （取得例：２ページ)
            page_element = soup.select('.sc-cpUASM.bqNXll')
            page = page_element[0].text         
            page_str = ''.join(filter(str.isdigit, page))
            page_num = int(page_str)
        except:
            page_num = 1
            
        #ページ数が複数のとき、ページ遷移し本文を取得
        if (page_num > 1):
            for i in range(2, page_num + 1):
                news_url_page = news_url + "?page=" + str(page_num)
                r = requests.get(news_url_page)
                soup = BeautifulSoup(r.text, "html.parser")
                #クラス名が変わるので注意！！ 
                elements = soup.select('.sc-iMCRTP.ePfheF.yjSlinkDirectlink.highLightSearchTargett')
                #ニュース記事の本文が配列で区切られていた場合
                for i in range(0, 8):
                    try:
                        text += elements[i].text
                    except:
                        pass
                        
        news_text.append(text)
    
        time.sleep(0.5)

    articles = []
    for url, title, text in zip(news_urls, news_titles, news_text):
        article = {
            "title" : title,
            "URL" : url,
            "text" : text
        }
        articles.append(article)

    return articles

#CNNニュースの情報を取得
def cnn_news_scraping(topic):
    url = 'https://www.cnn.co.jp'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    
    #クラス名が変わるので注意！！
    elements = soup.select('.pg-container li a')
    elements = elements[6:11] + [elements[14], elements[16]]
    
    topic = topic
    #トピックのURL取得
    for i, element in enumerate(elements):
        if topic in element.text:
            categories_num = i
    
    element = elements[categories_num]
    
    topic_url = element['href']
    URL = url + topic_url
    
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, "html.parser")
    
    #クラス名が変わるので注意！！
    elements = soup.select('.cd a')
    
    elements = elements[:3]
    
    news_urls = []
    news_titles = []
    #ニュースのURLとタイトルを取得
    for element in elements:
        news_url =  url + element['href']
        news_title = element.text
    
        news_urls.append(news_url)
        news_titles.append(news_title)
    
    news_text = []
    #ニュースの本文を取得
    for i, news_url in enumerate(news_urls):
        text = ""
        
        for j in range(1, 7):
            num = str(j)
            page = '-' + num + '.html'    
            # 文字列の置換を行い新しいURLを生成
            news_url_page = news_urls[i].replace('.html', page)
    
            #ページ数が複数のとき、ページ遷移し本文を取得
            response = requests.get(news_url_page)
    
            # レスポンスのステータスコードを確認
            if response.status_code != 404: 
                r = requests.get(news_url_page)
                soup = BeautifulSoup(r.text, "html.parser")
                #クラス名が変わるので注意！！ 
                elements = soup.find(id = 'leaf-body')
                text += elements.text
            else:
                continue
    
        news_text.append(text)

    articles = []
    for url, title, text in zip(news_urls, news_titles, news_text):
        article = {
            "title" : title,
            "URL" : url,
            "text" : text
        }
        articles.append(article)

    return articles

#産経ニュースの情報を取得
def sankei_news_scraping(topic):
    url = 'https://www.sankei.com/'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    elements = soup.select('.nav-link')
    categories_elements = elements[11:18]
    
    #カテゴリーのURL取得
    category_urls = []
    for i, element in enumerate(categories_elements):
        link = 'https://www.sankei.com/' + element.a['href']
        category_urls.append(link)

        if (topic == element.text):
            categories_num = i
        time.sleep(0.2)
    
    r = requests.get(category_urls[categories_num])
    soup = BeautifulSoup(r.text, "html.parser")
    elements = soup.select('.ranking__item ')
    
    #取得するニュースの数を５つにしている
    elements = elements[0:5]
    
    #ニュースのURLの取得
    news_urls = []
    for element in elements:
        link = element.a['href']
        news_urls.append(link)
        time.sleep(0.2)
    
    #ニュースの本文を取得
    news_text = []
    for news_url in news_urls:
        r = requests.get(news_url)
        soup = BeautifulSoup(r.text, "html.parser")
        elements = soup.select('.article-text')

        time.sleep(0.2)
    
        text = ''
        for element in elements:
            text += element.text
            
        news_text.append(text)

    articles = []
    for url, text in zip(news_urls, news_text):
        article = {
            "URL" : url,
            "text" : text
        }
        articles.append(article)

    return articles

#データを整える
def clean_data(articles):
    for i in range(len(articles)):
        articles[i]['title'] = articles[i]['title'].replace('\u3000', '') 
        articles[i]['title'] = articles[i]['title'].lstrip('0123456789')
        articles[i]['text'] = articles[i]['text'].replace('\u3000', '')
        articles[i]['text'] = articles[i]['text'].replace('\n', '')

    return articles

#データを整える(産経)
def clean_data_sankei(articles):
    for i in range(len(articles)):
        articles[i]['text'] = articles[i]['text'].replace('\u3000', '')
        articles[i]['text'] = articles[i]['text'].replace('\n', '')

    return articles

#ヤフーニュースの要約を行う本文の取得
def yahoo_news_text(url):
    #ニュースの本文を取得
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    #クラス名が変わるので注意！！ 
    elements = soup.select('.sc-ksXiki.dXXEDb.yjSlinkDirectlink.highLightSearchTarget')

    text = ""

    #ニュース記事の本文が配列で区切られていた場合
    for i in range(0, 8):
        try:
            if (i == 0):
                text = elements[0].text
            else:
                text += elements[i].text
        except:
            pass

    #ページが1つだけのとき、エラーが出るため
    try:
        #クラス名が変わるので注意！！ （取得例：２ページ)
        page_element = soup.select('.sc-cpUASM.bqNXll')
        page = page_element[0].text         
        page_str = ''.join(filter(str.isdigit, page))
        page_num = int(page_str)
    except:
        page_num = 1
        
    #ページ数が複数のとき、ページ遷移し本文を取得
    if (page_num > 1):
        for i in range(2, page_num + 1):
            news_url_page = url + "?page=" + str(page_num)
            r = requests.get(news_url_page)
            soup = BeautifulSoup(r.text, "html.parser")
            #クラス名が変わるので注意！！ 
            elements = soup.select('.sc-iMCRTP.ePfheF.yjSlinkDirectlink.highLightSearchTargett')
            #ニュース記事の本文が配列で区切られていた場合
            for i in range(0, 8):
                try:
                    text += elements[i].text
                except:
                    pass
    text = text.replace('\u3000', '')
    text = text.replace('\n', '')
    return text

#CNNニュースの要約を行う本文の取得
def cnn_news_text(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    
    #ニュースの本文を取得
    text = ""
    for j in range(1, 7):
        num = str(j)
        page = '-' + num + '.html'    
        # 文字列の置換を行い新しいURLを生成
        news_url_page = url.replace('.html', page)
    
        #ページ数が複数のとき、ページ遷移し本文を取得
        response = requests.get(news_url_page)
    
        # レスポンスのステータスコードを確認
        if response.status_code != 404: 
            r = requests.get(news_url_page)
            soup = BeautifulSoup(r.text, "html.parser")
            #クラス名が変わるので注意！！ 
            elements = soup.find(id = 'leaf-body')
            text += elements.text
        else:
            continue
    
    text = text.replace('\u3000', '')
    text = text.replace('\n', '')

    return text

#産経ニュースの要約を行う本文の取得
def sankei_news_text(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    elements = soup.select('.article-text')

    time.sleep(0.2)

    text = ''
    for element in elements:
        text += element.text
    
    text = text.replace('\u3000', '')
    text = text.replace('\n', '')

    return text

#ニュースの本文を区切る
def length_decision(sentence):
    if (len(sentence) > 350):
        split_sentence = []
        count = round(len(sentence) / 350)
        for i in range(count+1):
            start = i * 350
            stop = (i + 1) * 350
            split_sentence.append(sentence[start:stop])
    return split_sentence


#要約を行う
def text_summary(sentence, errormessage):
    # 抽出文章数は入力文章数の2分の1
    count = sentence.count('。')
    count = round(count / 2)
    if count < 1:
        count = 1

    # WebAPIにパラメータをPOSTで渡す
    url = 'https://api.a3rt.recruit.co.jp/text_summarization/v1'
    apikey = 'DZZkH17tdljiJjcI6DwY5ToVTWWGxwqc'
    
    post_data = {
        'apikey': apikey,
        'sentences': sentence,
        'linenumber': count,
        'separation': '。'
    }

    # 要約
    res = ''
    errormessage[0] = ''
    response = requests.post(url, data=post_data)
    json_data = response.json()

    # エラーチェック
    if not json_data:
        res = False
        errormessage[0] = 'WebAPIが停止'
    elif 'status' in json_data and json_data['status'] == 0:
        if 'summary' in json_data and json_data['summary']:
            for ss in json_data['summary']:
                res += str(ss) + '。'
        else:
            res = False
            errormessage[0] = '要約データが存在しません'
    else:
        res = False
        errormessage[0] = json_data['message']

    return res

def is_valid_url(url):
    # URLの正規表現パターン
    url_pattern = re.compile(r'^(http|https)://[a-zA-Z0-9.-]+(\.[a-zA-Z]{2,6})([a-zA-Z0-9/+.-]*)?$')

    # URLの正規表現パターンに一致するか確認
    if url_pattern.match(url):
        return True
    else:
        return False

def text_to_speech(text):
    try:
    # 音声ファイルを作成
        tts = gTTS(text, lang="ja")

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            tts.save(temp_file.name)
            temp_file.close()
            audio_file_path = temp_file.name

        # Dropboxにファイルをアップロード
        with open(audio_file_path, 'rb') as file:
            dbx.files_upload(file.read(), '/uploaded-files/' + os.path.basename(audio_file_path))

        # Dropbox上のファイルへの共有可能なURLを生成
        shared_link_metadata = dbx.sharing_create_shared_link('/uploaded-files/' + os.path.basename(audio_file_path))
        shared_url = shared_link_metadata.url.replace('&dl=0', '&dl=1')

    finally:
        # 一時ファイルを削除
        os.remove(audio_file_path)

    return shared_url


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    #ユーザーIDを取得する
    user_id = event.source.user_id
    
    global news_flag
    global summary_flag
    global text_to_speech_flag
    
    if (event.message.text == 'ヤフーニュース'):
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='ヤフーニュースを取得します。'))
        news_flag = 0
        send_button_message(user_id)
    elif (event.message.text == 'CNNニュース'):
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='CNNニュースを取得します。'))
        news_flag = 1
        send_button_message(user_id)
    elif (event.message.text == '産経ニュース'):
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='産経ニュースを取得します。'))
        news_flag = 2
        send_button_message(user_id)
    elif (event.message.text == '要約'):
        summary_flag = 1
    elif (event.message.text == '音声変換'):
        text_to_speech_flag = 1
    
    if ((news_flag == 0) and (summary_flag == 0) and (text_to_speech_flag == 0)):
        if event.message.text in yahoo_categories:
            articles_dict = yahoo_news_scraping(event.message.text)
            articles = clean_data(articles_dict)
        else:
            pass
    elif ((news_flag == 1) and (summary_flag == 0) and (text_to_speech_flag == 0)):
        if (event.message.text in cnn_categories_change):
            articles_dict = cnn_news_scraping(cnn_categories[cnn_categories_change.index(event.message.text)])
            articles = clean_data(articles_dict)
        else:
            pass
    elif ((news_flag == 2) and (summary_flag == 0) and (text_to_speech_flag == 0)):
        if (event.message.text in sankei_categories):
            articles_dict = sankei_news_scraping(event.message.text)
            articles = clean_data_sankei(articles_dict)
        else:
            pass
    elif ((summary_flag == 1) and (text_to_speech_flag == 0)):
        url = event.message.text
        if (is_valid_url(url)):
            try:
                try:
                    sentence = yahoo_news_text(url)
                except:
                    pass
                
                try:
                    sentence = cnn_news_text(url)
                except:
                    pass
                
                try:
                    sentence = sankei_news_text(url)
                except:
                    pass
                
                split_sentence = length_decision(sentence)
                
                errormessage = ['']
                summary_sentence = ''
                for i, sentence in enumerate(split_sentence):
                    sentence = sentence.replace(' ', '')
                    result = text_summary(sentence, errormessage)
                    try:
                        summary_sentence += result
                    except:
                        pass
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=summary_sentence))
                
                summary_flag = 0
            
            except:
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='このニュース記事は要約できません。'))
            finally:    
                return
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='要約したいニュース記事のURLを入力してください。'))
    elif ((text_to_speech_flag == 1) and (summary_flag == 0)):
        url = event.message.text
        if (is_valid_url(url)):
            try:
                text = yahoo_news_text(url)
            except:
                pass
            
            try:
                text = cnn_news_text(url)
            except:
                pass
            
            try:
                text = sankei_news_text(url)
            except:
                pass
        
            shared_url = text_to_speech(text)
            line_bot_api.reply_message(
                event.reply_token,
                AudioSendMessage(type="audio", original_content_url=shared_url, duration=11000))
            
            text_to_speech_flag = 0
        
            return
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='音声変換したいニュース記事のURLを入力してください。'))

    article_urls = []
    for i, article in enumerate(articles):
        article_urls.append(articles[i]['URL'])
    
    messages = []
    for article_url in article_urls:
        message = TextSendMessage(text=article_url)
        messages.append(message)

    line_bot_api.reply_message(
        event.reply_token,
        messages
    )
    
if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
