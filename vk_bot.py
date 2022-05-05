import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from threading import Thread

import lab4

vk_session = vk_api.VkApi(token="8a8c105055d8984df26032fc1a4721012a2c37560d89e736b0b62f884486f636e131da76d4f3019e59f24")
session_api = vk_session.get_api()
longpool = VkLongPoll(vk_session)

keyboard = VkKeyboard()
keyboard.add_button("Привет", VkKeyboardColor.PRIMARY)
keyboard.add_line()
keyboard.add_button("Хочу получать новости", VkKeyboardColor.POSITIVE)
keyboard.add_line()
keyboard.add_button("Я не хочу получать новости", VkKeyboardColor.NEGATIVE)

def sender(id, text, keyboard):
    vk_session.method('messages.send', {
        'user_id': id,
        'message': text,
        'random_id': 0,
        'keyboard': keyboard.get_keyboard()
    })

def send_msg():
    all_users = lab4.Bot.query.all()
    for i in all_users:
        sender(i.id_vk, 'Вышла новая запись??',keyboard)

def aaa(Thread):
    for event in longpool.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                msg = event.text.lower()
                id = event.user_id

                if msg == 'начать':
                    sender(id, 'Привет', keyboard)

                if msg == 'привет':
                    sender(id, 'и тебе привет', keyboard)

                if msg == 'хочу получать новости':
                    if not lab4.Bot.query.filter_by(id_vk = id).first():
                        u = lab4.Bot(id_vk = id)
                        lab4.dbalc.session.add(u)
                        lab4.dbalc.session.flush()
                        lab4.dbalc.session.commit()
                        sender(id, 'Теперь вы подписаны на рассылку!', keyboard)
                    else:
                        sender(id, 'Вы уже подписаны на рассылку!', keyboard)

                if msg == 'я не хочу получать новости':
                    u = lab4.Bot.query.filter_by(id_vk = id).first()
                    if(lab4.Bot.query.filter_by(id_vk = id).first()):
                        lab4.dbalc.session.delete(u)
                        lab4.dbalc.session.commit()
                        sender(id, 'Вы отписались от рассылки', keyboard)
                    else:
                        sender(id, 'Но вы итак не подписаны на рассылку', keyboard)