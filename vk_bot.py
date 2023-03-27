from config import USER_TOKEN, GROUP_TOKEN, PASSWORD
from vk_functions import *
from db import User, Viewed, Contact, Photos

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def menu(chat_id, text='Меню:'):
    """ Показ меню

    :param chat_id: id чата
    :type chat_id: str

    :param text
    :type str
    """
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button(label='профиль', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button(label='поиск', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button(label='понравшиеся пользователи', color=VkKeyboardColor.POSITIVE)
    send_message(chat_id=user_id, text=text, keyboard=keyboard)


def check_user(chat_id):
    """ Поверяет есть ли пользователь в бд

    :param chat_id: id чата
    :type chat_id: str

    :return возращает пользователя если он есть
    """

    keyboard = VkKeyboard(inline=True)
    keyboard.add_button(label='создать', color=VkKeyboardColor.POSITIVE)

    send_message(chat_id=chat_id, text='Введите id пользователя')
    response_id, chat_id = longpoll_listen()

    user = user_db.select_user(user_id=response_id)

    if not user:
        send_message(chat_id=chat_id, text='Такого пользователя нет в бд', keyboard=keyboard)
        response, chat_id = longpoll_listen()

        while response != 'создать':
            send_message(chat_id=chat_id, text='Неверная команда', keyboard=keyboard)
            response, chat_id = longpoll_listen()

        user = get_user(user_id=response_id, chat_id=chat_id)
        user_db.add_user(user)
        send_message(chat_id=chat_id, text='Пользователь создан')
        user = user_db.select_user(user_id=response_id)
    return user[0]


def create_keyboard(keyboard_contact):
    """ Создает клавиатуру

    :param keyboard_contact
    :type tuple
    """
    keyboard_contact_1 = keyboard_contact[0]
    keyboard_contact_2 = keyboard_contact[1]
    keyboard_contact_color = keyboard_contact[2]

    keyboard = VkKeyboard(inline=True)
    keyboard.add_button(label='показать', color=VkKeyboardColor.PRIMARY)

    keyboard_contact = VkKeyboard(inline=True)
    keyboard_contact.add_button(label=keyboard_contact_1, color=keyboard_contact_color)
    keyboard_contact.add_button(label=keyboard_contact_2, color=VkKeyboardColor.PRIMARY)

    keyboard_choice = VkKeyboard(inline=True)
    keyboard_choice.add_button(label='да', color=VkKeyboardColor.PRIMARY)
    keyboard_choice.add_button(label='нет', color=VkKeyboardColor.NEGATIVE)

    return keyboard, keyboard_contact, keyboard_choice


def search(chat_id):
    """ Ищет людей

    :param chat_id: id чата
    :type chat_id: str
    """

    keyboard = create_keyboard(keyboard_contact=('нравится', 'далее', VkKeyboardColor.POSITIVE))
    user = check_user(chat_id=chat_id)
    user_id = user[1]
    offset = user[-1]

    while True:
        contacts = search_contacts(filters=user, offset=offset)
        send_message(chat_id=chat_id,
                     text=f'Найдено пользователей: {len(contacts)}',
                     keyboard=keyboard[0])
        response, chat_id = longpoll_listen()

        if response == 'показать':
            for contact in contacts:
                offset += 1
                user_db.update_user(user_id=user_id, offset=offset)

                viewed_contact = viewed_db.select_contact(contact_id=contact['user_id'])
                if viewed_contact:
                    continue
                viewed_db.add_contact(contact_id=contact['user_id'])

                contact_photos = get_photos(contact_id=contact['user_id'])
                send_message(chat_id=chat_id,
                             text=f'Имя: {contact["first_name"]}\n'
                                  f'Ссылка: {contact["link"]}',
                             attachment=','.join(contact_photos[0]),
                             keyboard=keyboard[1])
                response, chat_id = longpoll_listen()

                if response == 'нравится':
                    contact_db.add_contact(contact=contact, user_id=user_id)
                    photos_db.add_photos(photos=contact_photos[1], contact_id=contact['user_id'])

            send_message(chat_id=chat_id, text='Конец поиска\nХотите еще посмотреть?', keyboard=keyboard[2])
            response, chat_id = longpoll_listen()

            if response == 'нет':
                menu(chat_id=chat_id)
                return


def profile(chat_id):
    """ Показывает профиль

    :param chat_id: id чата
    :type chat_id: str
    """

    user = check_user(chat_id=chat_id)
    show_user(user=user, chat_id=chat_id)
    menu(chat_id=chat_id)


def show_contacts(chat_id):
    """ Показывает понравшиеся людей из бд

    :param chat_id: id чата
    :type chat_id: str
    """

    keyboard = create_keyboard(keyboard_contact=('удалить из бд', 'далее', VkKeyboardColor.NEGATIVE))
    user = check_user(chat_id=chat_id)

    user_id = user[1]

    contacts = contact_db.select_contact(user_id=user_id)
    send_message(chat_id=chat_id,
                 text=f'Найдено пользователей: {len(contacts)}',
                 keyboard=keyboard[0])
    response, chat_id = longpoll_listen()

    if response == 'показать':
        for contact in contacts:
            contact_photos = photos_db.select_photos(contact_id=contact[1])
            send_message(chat_id=chat_id,
                         text=f'Имя: {contact[2]}\n'
                              f'Ссылка: {contact[5]}',
                         attachment=','.join(contact_photos[0]),
                         keyboard=keyboard[1])
            response, chat_id = longpoll_listen()

            if response == 'удалить из бд':
                contact_db.delete_contact(contact_id=contact[1])
    menu(chat_id=chat_id)


if __name__ == '__main__':
    vk_user = vk_api.VkApi(token=USER_TOKEN)
    vk_group = vk_api.VkApi(token=GROUP_TOKEN)

    longpoll = VkLongPoll(vk=vk_group)
    upload = vk_api.VkUpload(vk=vk_group)

    user_db = User(database='vkinder', password=PASSWORD)
    viewed_db = Viewed(database='vkinder', password=PASSWORD)
    contact_db = Contact(database='vkinder', password=PASSWORD)
    photos_db = Photos(database='vkinder', password=PASSWORD)

    while True:
        global_command, user_id = longpoll_listen()
        if global_command == '/search' or global_command == 'поиск':
            search(chat_id=user_id)
        elif global_command == '/profile' or global_command == 'профиль':
            profile(chat_id=user_id)
        elif global_command == '/like' or global_command == 'понравшиеся пользователи':
            show_contacts(chat_id=user_id)
        else:
            menu(chat_id=user_id, text='Привет, меня зовут VKinder')


