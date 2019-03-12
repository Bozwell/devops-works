#-*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import datetime

import smtplib
import email.message

GMAIL_USER = 'bob@example.com'
GMAIL_PWD = 'bob_passwrod'

MAIL_TO = 'tomy@example.com'


today_str = datetime.date.today().strftime('%Y.%m.%d')

# 오늘 날짜에 보안공지가 없을수있으므로 테스트용으로 날짜를 지정한다.
# today_str = '2018.11.21'

keywords = (
    u'Apple',
    u'MS',
    u'Adobe',
    u'긴급'
)


def send_mail(subject, email_text):
    msg = email.message.Message()
    msg['Subject'] = '[Security Notice] ' + subject
    msg['From'] = GMAIL_USER
    msg['To'] = MAIL_TO
    msg.add_header('Content-Type', 'text/html')
    msg.set_payload('<html><body>{}</body></html>'.format(email_text))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(GMAIL_USER, GMAIL_PWD)
        server.sendmail(msg['From'], [msg['To']], msg.as_string())
        server.close()
    except Exception as ex:
        print '--------->', ex


# KISA 보안공지 html을 가져온다.
req = requests.get('https://www.krcert.or.kr/data/secNoticeList.do?page1')
html = req.text

# BeautifulSoup으로 검색가능한 구조를 만든다.
soup = BeautifulSoup(html,'html.parser')


my_title = soup.select(
    'td.colTit > a'
)


for title in my_title:
    # 카워드에 해당하는 내용을 가져온다.
    for keyword in keywords:
        if title.text.find(keyword) != -1:
            req2 = requests.get('https://www.krcert.or.kr{}'.format(title.get('href')))
            html2 = req2.text
            soup2 = BeautifulSoup(html2, 'html.parser')

            date = soup2.select(
                'tr > th > span'
            )

            # 오늘날짜인지 확인
            if date[0].text == today_str:
                # print title.get('href')
                # contentDiv > table > tbody > tr:nth-child(2) > td
                cont = soup2.select('tr > td')

                #이메일을 보낸다.
                send_mail(subject=title.text, email_text=cont[0])








