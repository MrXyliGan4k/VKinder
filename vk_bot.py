from config import USER_TOKEN, GROUP_TOKEN, PASSWORD
from vk_functions import *
from db import User, Viewed, Contact

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
    user_info = get_user(user_id=response_id, chat_id=chat_id)

    if not user:
        send_message(chat_id=chat_id, text='Такого пользователя нет в бд', keyboard=keyboard)
        response, chat_id = longpoll_listen()
        if response != 'создать':
            raise Exception('не нажата кнопка создать')

        user_db.add_user(user_id=response_id)
        send_message(chat_id=chat_id, text='Пользователь создан')

    return user_info


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
    id, user_id, offset = user_db.select_user(user_id=user['user_id'])[0]

    while True:
        contacts = search_contacts(user=user, offset=offset)
        send_message(chat_id=chat_id,
                     text=f'Найдено пользователей: {len(contacts)}',
                     keyboard=keyboard[0])
        response, chat_id = longpoll_listen()

        if response == 'показать':
            for contact in contacts:
                if viewed_db.select_contact(contact_id=contact['user_id'], user_id=user['user_id']):
                    continue
                viewed_db.add_contact(contact_id=contact['user_id'], user_id=user_id)
                offset += 1
                user_db.update_user(user_id=user_id, offset=offset)

                contact_photos = get_photos(contact_id=contact['user_id'])
                send_message(chat_id=chat_id,
                             text=f"Имя: {contact['first_name']}\n"
                                  f"Фамилия: {contact['last_name']}\n"
                                  f"Ссылка: {contact['link']}\n"
                                  f"Фото: {contact_photos if not isinstance(contact_photos, list) else len(contact_photos)}",
                             attachment=','.join(contact_photos),
                             keyboard=keyboard[1])
                response, chat_id = longpoll_listen()
                if response == 'нравится':
                    contact_db.add_contact(contact=contact, user_id=user_id)

            send_message(chat_id=chat_id, text='Конец поиска\nХотите еще посмотреть?', keyboard=keyboard[2])
            response, chat_id = longpoll_listen()
            if response == 'нет':
                return


def profile(chat_id):
    """ Показывает профиль

    :param chat_id: id чата
    :type chat_id: str
    """
    user = check_user(chat_id=chat_id)
    show_user(user=user, chat_id=chat_id)


def show_contacts(chat_id):
    """ Показывает понравшиеся людей из бд

    :param chat_id: id чата
    :type chat_id: str
    """

    keyboard = create_keyboard(keyboard_contact=('удалить из бд', 'далее', VkKeyboardColor.NEGATIVE))

    user = check_user(chat_id=chat_id)
    id, user_id, offset = user_db.select_user(user_id=user['user_id'])[0]

    contacts_select = contact_db.select_contact(user_id=user_id)
    contacts = get_contacts(contacts=contacts_select, chat_id=chat_id)
    send_message(chat_id=chat_id,
                 text=f'Найдено пользователей: {len(contacts)}',
                 keyboard=keyboard[0])
    response, chat_id = longpoll_listen()

    if response == 'показать':
        for contact in contacts:
            contact_photos = get_photos(contact_id=contact['user_id'])
            send_message(chat_id=chat_id,
                         text=f"Имя: {contact['first_name']}\n"
                              f"Фамилия: {contact['last_name']}\n"
                              f"Ссылка: {contact['link']}\n"
                              f"Фото: {contact_photos if not isinstance(contact_photos, list) else len(contact_photos)}",
                         attachment=','.join(contact_photos),
                         keyboard=keyboard[1])
            response, chat_id = longpoll_listen()
            if response == 'удалить из бд':
                contact_db.delete_contact(contact_id=contact['user_id'])


if __name__ == '__main__':
    vk_user = vk_api.VkApi(token=USER_TOKEN)
    vk_group = vk_api.VkApi(token=GROUP_TOKEN)

    longpoll = VkLongPoll(vk=vk_group)
    upload = vk_api.VkUpload(vk=vk_group)

    user_db = User(database='vkinder', password=PASSWORD)
    viewed_db = Viewed(database='vkinder', password=PASSWORD)
    contact_db = Contact(database='vkinder', password=PASSWORD)

    while True:
        global_command, user_id = longpoll_listen()
        try:
            if global_command == '/search' or global_command == 'поиск':
                search(chat_id=user_id)
            elif global_command == '/profile' or global_command == 'профиль':
                profile(chat_id=user_id)
            elif global_command == '/like' or global_command == 'понравшиеся пользователи':
                show_contacts(chat_id=user_id)
        except Exception as error:
            send_message(chat_id=user_id, text=error)
        menu(chat_id=user_id)


