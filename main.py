import requests
from bs4 import BeautifulSoup
import sqlite3

from telegram import Bot
import asyncio

token = input('token:\n')
chat_id = input('chat_id:\n')
con = sqlite3.connect('news.db')
bot = Bot(token=token)


def create_news_table(con):
    try:
        cur = con.cursor()
        cur.execute(""" CREATE TABLE IF NOT EXISTS news_ru_inv(
                                                links text NOT NULL UNIQUE
                                            ); """)
        cur.execute(""" CREATE TABLE IF NOT EXISTS news_rbc(
                                                        links text NOT NULL UNIQUE
                                                    ); """)
        cur.execute(""" CREATE TABLE IF NOT EXISTS news_cryptonews(
                                                        links text NOT NULL UNIQUE
                                                    ); """)
    except:
        print('already exists')

def add_news(con, link, site):
    if site == 'ru_inv':
        try:
            cur = con.cursor()
            cur.execute('INSERT INTO news_ru_inv(links) VALUES(?);', (link,))
            con.commit()
            return True
        except:
            return False
    elif site == 'rbc':
        try:
            cur = con.cursor()
            cur.execute('INSERT INTO news_rbc(links) VALUES(?);', (link,))
            con.commit()
            return True
        except:
            return False
    elif site == 'cryptonews':
        try:
            cur = con.cursor()
            cur.execute('INSERT INTO news_cryptonews(links) VALUES(?);', (link,))
            con.commit()
            return True
        except:
            return False

def get_text_rbc(url):
    headers = {

        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    all_text = soup.find_all('p')
    news_text = ''
    for i in all_text:
        if ('Подписка отключает баннерную рекламу на сайтах РБК и обеспечивает его корректную работу' in i.text) or ('Всего 99₽ в месяц для 3-х устройств' in i.text) or ('Продлевается автоматически каждый месяц, но вы всегда сможете отписаться' in i.text):
            continue
        if '—' in i.text and '—' in all_text[all_text.index(i)+1].text and '—' in all_text[all_text.index(i)+2].text:
            break
        news_text += f'{i.text}\n'
    return news_text

def get_text_cryptonews(url):
    headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    all_text = soup.find_all('p')
    news_text = ''
    for i in all_text:
        if 'Источник: ' in i.text:
            continue
        if 'При использовании материалов ссылка на cryptonews.net обязательна.' in i.text:
            break
        if 'Investing' in i.text and 'Investing' in all_text[all_text.index(i)+1].text and 'Investing' in all_text[all_text.index(i)+2].text:
            break
        news_text += f'{i.text}\n'
    return news_text

def get_text_ru_inv(url):
    headers = {

        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    all_text = soup.find_all('p')
    news_text = ''
    for i in all_text:
        if 'Попробуйте другой запрос' in i.text:
            continue
        if 'Оригинальная статья' in i.text or 'Текст подготов' in i.text:
            break
        news_text += f'{i.text}\n'
    return news_text

async def get_urls_ru_inv(con):
    while True:
        headers = {

            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        }
        response = requests.get('https://ru.investing.com/news/cryptocurrency-news', headers = headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        title_page = soup.find_all('div', {'class': 'largeTitle'})
        articles = title_page[0].find_all('article', limit = 10)
        x = 0
        for i in articles:
            x += 1
            url_link = i.find('a').get('href')
            if '/news/' in url_link:
                url_link= 'https://ru.investing.com' + url_link
            news_title = i.find('img').get('alt')
            if add_news(con, url_link, 'ru_inv'):
                news_text = get_text_ru_inv(url_link)
                try:
                    bot.send_message(chat_id, text = f'<b>{news_title}</b>'+'\n\n'+
                                                f'{news_text}\n\n'
                                                 'Читать подробнее: '+url_link, parse_mode='HTML')
                    await asyncio.sleep(10)
                except:
                    print(f'{url_link} - Слишком длинный текст')
        await asyncio.sleep(300)


async def get_urls_rbc(con):
    while True:
        headers = {

            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        }
        response = requests.get('https://www.rbc.ru/crypto/', headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        title_page = soup.find_all('div', {'class': 'js-index-exclude'}, limit=10)
        for i in title_page:
            url_link = i.find('a', {'class':'item__link'}).get('href')
            news_title = i.find('span', {'class': 'item__title rm-cm-item-text'}).text.strip()

            if add_news(con, url_link, 'rbc'):
                news_text = get_text_rbc(url_link)
                try:
                    bot.send_message(chat_id, text=f'<b>{news_title}</b>' + '\n\n' +
                                                    f'{news_text}\n\n'
                                                   'Ссылка на текст: ' + url_link, parse_mode='HTML')
                    await asyncio.sleep(10)
                except:
                    print(f'{url_link} - Слишком длинный текст')
        await asyncio.sleep(300)

async def get_urls_cryptonews(con):
    while True:
        headers = {

            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"
        }
        response = requests.get('https://cryptonews.net/ru/', headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        title_page = soup.find_all('a', {'class': 'title'}, limit=3)
        for i in title_page:
            url_link = i.get('href')
            url_link = 'https://cryptonews.net' + url_link
            news_title = i.text
            if add_news(con, url_link, 'cryptonews'):
                news_text = get_text_cryptonews(url_link)
                try:
                    bot.send_message(chat_id, text=f'<b>{news_title}</b>' + '\n\n' +
                                                   f'{news_text}\n\n'
                                                   'Ссылка на текст: ' + url_link, parse_mode='HTML')
                    await asyncio.sleep(10)
                except:
                    print(f'{url_link} - Слишком длинный текст')
        await asyncio.sleep(300)
        bot.send_message(chat_id=383387282, text='work')

create_news_table(con)
loop = asyncio.get_event_loop()
loop.create_task(get_urls_ru_inv(con))
loop.create_task(get_urls_rbc(con))
loop.create_task(get_urls_cryptonews(con))
loop.run_forever()



