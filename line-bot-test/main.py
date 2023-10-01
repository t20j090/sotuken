
from flask import Flask, request, abort
from bs4 import BeautifulSoup
import datetime
import os
import requests
import time

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

yahoo_categories = ['国内', '国際', '経済', 'エンタメ', 'スポーツ', 'IT', '科学', 'ライフ']
cnn_categories = ['World', 'USA', 'Business', 'Tech', 'Entertainment', 'Odd News']
news_sites = ['ヤフーニュース', 'CNN']

# 0:ヤフーニュース 1:CNNニュース
news_flag = 0

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

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

#上位5位のCNNニュースを取得
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

def send_news_ranking():
    news_urls = yahoo_news_ranking()
    messages = [TextSendMessage(text=url) for url in news_urls]
    line_bot_api.broadcast(messages=messages)
    
    news_urls = cnn_news_ranking()
    messages = [TextSendMessage(text=url) for url in news_urls]
    line_bot_api.broadcast(messages=messages)


# 現在の時刻を取得
now = datetime.datetime.now().time()

# 判定する時間帯を設定（開始時刻・終了時刻から-9時間する必要がある）
start_time = datetime.time(21, 50)  # 開始時刻 21:50
end_time = datetime.time(22, 10)   # 終了時刻 22:10

#現在の日付を取得
# t_delta = datetime.timedelta(hours=9)
# JST = datetime.timezone(t_delta, 'JST')
# now = datetime.datetime.now(JST)
# current_time = now.strftime('%Y/%m/%d %H:%M:%S')

#LineのユーザーID
user_id = 'U2925b78f74c0cbde9804be066eb707f0'

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
        elements = soup.select('.sc-iMCRTP.ePfheF.yjSlinkDirectlink.highLightSearchTarget')
    
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

#データをきれいに整える
def clean_data(articles):
    for i in range(len(articles)):
        articles[i]['title'] = articles[i]['title'].replace('\u3000', '') 
        articles[i]['title'] = articles[i]['title'].lstrip('0123456789')
        articles[i]['text'] = articles[i]['text'].replace('\u3000', '')
        articles[i]['text'] = articles[i]['text'].replace('\n', '')

    return articles

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event): 
    
    #ユーザーIDを取得する
    # user_id = event.source.user_id
    # line_bot_api.reply_message(
    #     event.reply_token,
    #     TextMessage(text=user_id))
    
    global news_flag
    
    if (event.message.text == 'ヤフーニュース'):
        news_flag = 0
    elif (event.message.text == 'CNN'):
        news_flag = 1
    
    if (news_flag == 0):
        if event.message.text in yahoo_categories:
            articles_dict = yahoo_news_scraping(event.message.text)
            articles = clean_data(articles_dict)
        elif (event.message.text in news_sites):
            pass
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='国内, 国際, 経済, エンタメ, スポーツ, IT, 科学, ライフのいずれかを入力してください。'))
    elif (news_flag == 1):
        if (event.message.text in cnn_categories):
            articles_dict = cnn_news_scraping(event.message.text)
            articles = clean_data(articles_dict)
        elif (event.message.text in news_sites):
            pass
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='World, USA, Business, Tech, Entertainment, Odd Newsのいずれかを入力してください。'))
        
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
