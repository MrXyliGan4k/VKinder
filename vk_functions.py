from config import USER_TOKEN, GROUP_TOKEN
import datetime
import re

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


vk_user = vk_api.VkApi(token=USER_TOKEN)

vk_group = vk_api.VkApi(token=GROUP_TOKEN)
longpoll = VkLongPoll(vk=vk_group)
upload = vk_api.VkUpload(vk=vk_group)


def longpoll_listen():
    """ Слушает бота

    :return возвращает сообщение и id отправителя
    """

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            text = event.text.lower()
            user_id = event.user_id
            return text, user_id


def send_message(chat_id, text=None, attachment=None, keyboard=None):
    vk_group.method('messages.send',
                    {
                        'user_id': chat_id,
                        'message': text,
                        'random_id': 0,
                        'attachment': attachment,
                        'keyboard': keyboard.get_keyboard() if keyboard else None
                    })


def is_valid(filter, chat_id):
    """ Проверка на правильность данных

    :param filter: фильтр
    :type filter: tuple

    :param chat_id: id чата
    :type chat_id: str

    :return возвращает правильный фильтр
    """

    value = filter[1]
    while True:
        if filter[0] == 'bdate':
            if re.fullmatch('\d{1,2}.\d{1,2}.\d{4}', value) == None:
                send_message(chat_id=chat_id, text=f'Не правильно введен фильтр дата рождения\n'
                                                   f'Введите фильтр по шаблону: 00.00.0000')
            else:
                value = datetime.date.today().year - int(value.split('.')[-1])
                break
        elif filter[0] == 'sex':
            if int(value) not in [1, 2]:
                send_message(chat_id=chat_id, text=f'Не правильно введен фильтр пол\n'
                                                   f'Введите фильтр по шаблону:\n'
                                                   f'1 — женский\n'
                                                   f'2 — мужской')
            else:
                break
        elif filter[0] == 'relation':
            if int(value) not in [1, 5, 6, 0]:
                send_message(chat_id=chat_id, text=f'Не правильно введен фильтр отношение\n'
                                                   f'Введите фильтр по шаблону:\n'
                                                   f'1 — не женат/не замужем\n'
                                                   f'5 — всё сложно\n'
                                                   f'6 — в активном поиске\n'
                                                   f'0 — не указано')
            else:
                break
        else:
            break
        value, user_id = longpoll_listen()
    return value


def get_user(user_id, chat_id):
    """ Получает информацию о пользователе

    :param user_id: id пользователя
    :type user_id: str

    :param chat_id: id чата
    :type chat_id: str

    :return возвращает информацию о пользователе
    """

    user = vk_group.method('users.get',
                           {
                               'user_ids': user_id,
                               'fields': 'bdate, sex, city, home_town, relation, photo_50, photo_id'
                           })[0]

    while user['first_name'] == 'DELETED':
        send_message(chat_id=chat_id, text='Не правильный id\nВведите id пользователя')
        user_id, chat_id = longpoll_listen()
        user = vk_group.method('users.get',
                               {
                                   'user_ids': user_id,
                                   'fields': 'bdate, sex, city, home_town, relation, photo_50, photo_id'
                               })[0]

    user_info = {
        'user_id': user_id,
        'first_name': user.get('first_name', None),
        'last_name': user.get('last_name', None)
    }
    keys = [
        'bdate',
        'sex',
        'city' if 'city' in user else 'home_town',
        'relation',
        'photo_id',
        'photo_50'
    ]

    for key in keys:
        if key in user:
            value = is_valid(filter=(key, user[key]), chat_id=chat_id)
        else:
            send_message(chat_id=chat_id, text=f'Нету фильтра {key}\n'
                                               f'Введите фильтр')
            response, user_id = longpoll_listen()
            value = is_valid(filter=(key, response), chat_id=chat_id)
        if key in ['city', 'home_town']:
            value = user[key]['title'].capitalize() if key == 'city' else user[key].capitalize()
        user_info[key] = value
    user_info['profile_link'] = f'https://vk.com/id{user_id}'

    return user_info


def show_user(user, chat_id):
    """ Показывает информацию о пользователе

    :param user: пользователь
    :type user: dict

    :param chat_id: id чата
    :type chat_id: str
    """

    relation = {
        1: 'не женат/не замужем',
        5: 'всё сложно',
        6: 'в активном поиске',
        0: 'не указано'
    }
    send_message(chat_id=chat_id,
                 text=f"id: {user[1]}\n"
                      f"Имя: {user[2]}\n"
                      f"Фамилия: {user[3]}\n"
                      f"Возраст: {user[4]}\n"
                      f"Город: {user[6]}\n"
                      f"Семейное положение: {relation[user[7]]}",
                 attachment=f'photo{user[8]}')


def search_contacts(filters, offset=0):
    """ Ищет пользователей по критериям

    :param filters: фильтр с критериями
    :type filters: dict

    :return возвращает список найденых пользователей
    """

    contacts_list = []
    contacts = vk_user.method('users.search',
                              {
                                  'count': 10,
                                  'offset': offset,
                                  'sort': 1,
                                  'age_from': 18,
                                  'age_to': filters[4],
                                  'sex': '1' if filters[5] == '2' else '2',
                                  'hometown': filters[6],
                                  'status': filters[7],
                                  'has_photo': 1,
                                  'fields': 'bdate, sex, city, home_town, status'
                              })

    for contact in contacts['items']:
        if contact['is_closed'] == False and ('city' in contact or 'home_town' in contact):
            contacts_list.append(
                {
                    'user_id': contact['id'],
                    'first_name': contact['first_name'],
                    'last_name': contact['last_name'],
                    'city': contact['city']['title'].capitalize() if 'city' in contact else contact['home_town'].capitalize(),
                    'link': f'https://vk.com/id{contact["id"]}'
                })
    return contacts_list


def get_photos(contact_id):
    """ Находит список фотографий пользователя по id

    :param contact_id: id пользователя
    :type contact_id: str

    :return возвращает список фотографий пользователя
    """

    photos = []
    contact_photos = vk_user.method('photos.get',
                                    {
                                        'owner_id': contact_id,
                                        'album_id': 'profile',
                                        'count': 10,
                                        'extended': 1,
                                        'photo_sizes': 1
                                    })

    for photo in contact_photos['items'][:3]:
        photos.append(
            [
                photo['likes']['count'] + photo['comments']['count'],
                f"photo{photo['owner_id']}_{photo['id']}",
                photo['sizes'][-1]['url']
            ])

    photos_list = []
    photos = sorted(photos, reverse=True)
    for photo in photos:
        photos_list.append(photo[1])

    return photos_list, photos