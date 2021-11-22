import re

import requests
from bs4 import BeautifulSoup

# Заголовки HTTP-запроса
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 6.1; rv:88.0)'
                   ' Gecko/20100101 Firefox/88.0'),
    'Accept': '*/*',
}

# Пример URL: 'https://www.telefonnyjdovidnyk.com.ua/nomer/380931282965'
BASE_URL = 'https://www.telefonnyjdovidnyk.com.ua/nomer/'

# Телефонный префикс для Украины
PHONE_PREFIX = '380'

# Телефонный номер передаётся как строка без национального префикса +380
def scrape_phone_info(phone_number: str) -> dict:
    """Возвращается словарь в виде:
    {
        'safety': str,
        'marks': str,
        'last_mark_date': str,
        'views': str,
        'last_view_date': str,
        'comments': list,
    }

    Каждый элемент списка 'comments' - это словарь:
    {
        'content': str,
        'date': str,
    }

    В случае ошибки функция возвращает None.
    """
    phone_info = {}

    url = BASE_URL + PHONE_PREFIX + phone_number
    try:
        r = requests.get(url, headers=HEADERS)
    except requests.exceptions.RequestException:
        print(f'Не удалось выполнить HTTP-запрос при доступе к {url}.')
        return None
    if r.status_code != requests.codes.ok:
        print(f'Ошибка {r.status_code} при доступе к {url}.')
        return None

    try:
        soup = BeautifulSoup(r.text, 'lxml')

        phone_info['safety'] = soup.find(
            'div', id='progress-bar-inner').get_text()
        phone_info['marks'] = soup.find('span', id='count-comments').get_text()

        phone_info['last_mark_date'] = (
            soup.find('td', text='Остання оцінка:').
            find_next_sibling('td').get_text().split()[0]
        )
        if phone_info['last_mark_date'] == 'Не':
            phone_info['last_mark_date'] = 'Нет оценки'

        phone_info['views'] = (
            soup.find('td', text='Кількість переглядів:').
            find_next_sibling('td').get_text().split('×')[0]
        )

        phone_info['last_view_date'] = (
            soup.find('td', text='Останній перегляд:').
            find_next_sibling('td').get_text()
        )

        phone_info['comments'] = []

        # Псевдокомментарий от администратора сайта: значит, комментариев нет
        if soup.find('strong', class_='comment-heading'):
            return phone_info

        for comment in soup.find_all('p', class_='comment-text'):
            content = comment.get_text()

            try:
                date = (comment.find_next_sibling('div').
                        p.find('span', class_='date').get_text())
            except AttributeError:
                continue

            phone_info['comments'].append({'content': content, 'date': date})

    except Exception as e:
        print('Неизвестная ошибка: ' + str(e))
        return None

    return phone_info

def main():
    while True:
        # Номера для теста: 931282965, 976554802, 976181030, 933896613
        phone_number = input('Введите украинский телефонный номер '
                             '(или нажмите ENTER для выхода): +380')
        if not phone_number:
            return
        if not re.findall(re.compile(r'^\d{9}$'), phone_number):
            print('Неправильный формат номера. Требуется ровно 9 цифр.')
            continue

        phone_info = scrape_phone_info(phone_number)
        if phone_info == None:
            print('Не удалось получить информацию о телефонном номере.')
            continue

        print(f'\n******** Информация по номеру +{PHONE_PREFIX}{phone_number} '
              '********\n')
        print(f"\tЧисло оценок: {phone_info['marks']}")
        print(f"\tДата последней оценки: {phone_info['last_mark_date']}")
        print(f"\tЧисло просмотров: {phone_info['views']}")
        print(f"\tДата последнего просмотра: {phone_info['last_view_date']}")
        print(f"\t>>>> Уровень угрозы {phone_info['safety']} %\n")

        if phone_info['comments']:
            print('>>>>>>>> Комментарии пользователей <<<<<<<<\n')
            for comment in phone_info['comments']:
                print(f"\t>>>> Добавлено: {comment['date']}")
                print(f"\t{comment['content']}\n")

if __name__ == '__main__':
    main()
