import re
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

MCV_USERNAME = os.environ['MCV_USERNAME']
MCV_PASSWORD = os.environ['MCV_PASSWORD']

URL = "https://www.mycourseville.com"


class Notification:
    def __init__(self, course, type, title, created, icon_img, link):
        self.course = course
        self.type = type
        self.title = title
        self.created = created
        self.icon_img = icon_img
        self.link = link


class Scraper:
    def __init__(self):
        self.s = requests.Session()
        self.init()

    def init(self):
        r = self.s.get(f'{URL}/api/oauth/authorize?response_type=code&client_id=mycourseville.com&redirect_uri={URL}')
        soup = BeautifulSoup(r.text, 'html.parser')
        self.form_token = soup.find('input', {'name': '_token'}).get('value')

    def login(self, username, password):
        r = self.s.post(f'{URL}/api/chulalogin', data={
            '_token': self.form_token,
            'loginfield': 'name',
            'username': username,
            'password': password
        })
        if r.status_code != 200:
            raise Exception("Login failed")

    def scrape(self):
        r = self.s.get(
            f'{URL}/?q=courseville/course/notification'
        )
        soup = BeautifulSoup(r.text, 'html.parser')
        items = soup.find_all('a', {'class': 'courseville-feed-item'})

        notifications = []
        for item in items:
            created = item.find(
                'div', {'class': 'courseville-feed-item-created'}
            )
            notifications.append(
                Notification(
                    course=item.find(
                        'div', {'class': 'courseville-feed-item-course'}).text.strip(),
                    type=item.find(
                        'div', {'class': 'courseville-feed-item-type'}).text.strip(),
                    title=item.find(
                        'div', {'class': 'courseville-feed-item-title'}).text.strip(),
                    created=re.search(
                        r"Created on (.+)      -- (?:.+)", created.text).group(1),
                    icon_img=item.find(
                        'img', {'class': 'courseville-feed-item-icon-img'}).get('src'),
                    link=item.get("href")
                )
            )
        return notifications


# checks if it represents today's date in Thailand
def check_today_date(date_str):
    date_obj = datetime.strptime(date_str, "%d %b %Y")

    # convert datetime object to Thailand timezone
    thailand_timezone = timezone(timedelta(hours=7))
    date_obj_thailand = date_obj.astimezone(thailand_timezone)

    # get today's date in Thailand
    today_thailand = datetime.now(thailand_timezone).date()

    # check if input date is today in Thailand
    is_today = date_obj_thailand.date() == today_thailand
    return is_today


# check if it is within the past days in Thailand time
def check_within_days(date_str, day):
    date_obj = datetime.strptime(date_str, "%d %b %Y")

    # convert datetime object to Thailand timezone
    thailand_timezone = timezone(timedelta(hours=7))
    date_obj_thailand = date_obj.astimezone(thailand_timezone)

    # get today's date in Thailand
    now = datetime.now(thailand_timezone)

    # Check if date_obj is within the past days from now
    delta = timedelta(days=day + 1)
    within_days = (now - delta) <= date_obj_thailand <= now
    return within_days


# check if it is within the past 7 days in Thailand time
def check_within_week(date_str):
    date_obj = datetime.strptime(date_str, "%d %b %Y")

    # convert datetime object to Thailand timezone
    thailand_timezone = timezone(timedelta(hours=7))
    date_obj_thailand = date_obj.astimezone(thailand_timezone)

    # get today's date in Thailand
    now = datetime.now(thailand_timezone)

    # Check if date_obj is within the past 7 days from now
    delta = timedelta(days=7 + 1)
    within_7_days = (now - delta) <= date_obj_thailand <= now
    return within_7_days


# the date is within the time delta from today's date in Thailand time
def get_day_different(date_str):
    date_obj = datetime.strptime(date_str, "%d %b %Y")

    # convert datetime object to Thailand timezone
    thailand_timezone = timezone(timedelta(hours=7))
    date_obj_thailand = date_obj.astimezone(thailand_timezone)

    # get today's date in Thailand
    today_th = datetime.now(thailand_timezone)
    date_delta = (today_th - date_obj_thailand).days
    return date_delta


def get_notifications(days=7, select=None):
    scraper = Scraper()
    scraper.login(MCV_USERNAME, MCV_PASSWORD)

    week_notification = []
    notifications = scraper.scrape()

    for notification in notifications:
        if not check_within_days(notification.created, int(days)): continue
        day_delta = get_day_different(notification.created)

        noti_type   = f"Type    : {notification.type.title()}"
        noti_title  = f"Title   : {notification.title}"
        noti_create = f"Created : {notification.created} - {day_delta} days ago"
        noti_link   = f"[{notification.type.title()} Link]({URL}/{notification.link})"

        if select is None or select.title() == notification.type.title():
            each_notification = [notification.course, f"{noti_type}\n{noti_title}\n{noti_create}", noti_link]
            week_notification.append(each_notification)

    return week_notification