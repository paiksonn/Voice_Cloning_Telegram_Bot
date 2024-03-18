from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
import tempfile
import torch
from TTS.api import TTS
import soundfile as sf
import random
from bs4 import BeautifulSoup
import requests


def voice_clon(massage: str, input_wav: str, output_wav: str):
    device = "cuda" if torch.cuda.is_available() else "cpu"

    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=True).to(device)

    tts.tts_to_file(text=massage, 
                    speaker_wav=input_wav,
                    language="ru", 
                    file_path=output_wav)
    
def ogg_to_wav_converter(input_file: str, output_file: str):
    # Конвертируем из ogg в wav
    data, samplerate = sf.read(input_file)
    sf.write(output_file, data, samplerate, format='WAV', subtype='PCM_16')  

updater = Updater('YOUR TELEGRAMM BOT TOKEN')
dispatcher = updater.dispatcher

def help_command(update, context):
    help_text = """
Доступные команды:
/start - Начать работу с ботом и получить инструкции (можно использовать, чтобы перезаписать аудио)
/mem - Получить случайный мем из предоставленной коллекции смешнявок (можно спамить эту команду бесконечно, но все мемы рандомные, поэтому автор бота не несет ответственности за чьи-то задетые чувства)
/anekdot - Получить рандомный анекдот, озвученный Вашим прекрасным голосом
    """
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Для получения списка всех доступных команд введите /help")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Пожалуйста, отправьте голосовое сообщение на русском языке длиной от 20 до 40 секунд.")
    
def voice_handler(update, context):
    user_id = update.message.from_user.id
    file = context.bot.getFile(update.message.voice.file_id)
    ogg_file = os.path.join(tempfile.gettempdir(), f'voice_{user_id}.ogg')
    wav_file = os.path.join(tempfile.gettempdir(), f'voice_{user_id}.wav')
    file.download(ogg_file)
    
    ogg_to_wav_converter(input_file=ogg_file, output_file=wav_file)
    
    context.user_data['wav_file'] = wav_file
    
    if 'already_sent' not in context.user_data:
        context.user_data['already_sent'] = True
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Теперь напишите текст, который Вы хотите озвучить.\nПомните, что пока что я понимаю только русский текст"
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Ваш новый текст будет озвучен тем же голосом. Просто напишите его ниже."
        )

def text_handler(update, context):
    text = update.message.text
    wav_file = context.user_data.get('wav_file')
    
    if not wav_file:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Сначала отправьте голосовое сообщение."
        )
        return

    # Уведомление пользователя о начале генерации голосового сообщения
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Подождите, пожалуйста, немного. Сейчас я сгенерирую голосовое сообщение и пришлю его Вам."
    )
    
    output_wav = os.path.join(tempfile.gettempdir(), f'output_{update.message.from_user.id}.wav')
    
    voice_clon(text, wav_file, output_wav)
    
    with open(output_wav, 'rb') as f:
        context.bot.send_voice(chat_id=update.effective_chat.id, voice=f)
    
    # Удаление выходного wav файла
    os.remove(output_wav)
    
    # Уведомление пользователя об окончании генерации и возможности озвучить еще текст
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Если Вы хотите озвучить еще какой-то текст, то просто напишите его ниже. Не нужно записывать еще одно голосовое сообщение."
    )

def send_random_mem(update, context):
    mems_folder = "D:/ML LEARNING/Voice_copy_generator/mems"
    mem_files = [os.path.join(mems_folder, f) for f in os.listdir(mems_folder) if os.path.isfile(os.path.join(mems_folder, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    random_mem = random.choice(mem_files)
    with open(random_mem, 'rb') as file:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=file)

def get_anekdot():
    url = 'https://www.anekdot.ru/author-best/years/?years=anekdot'
    response = requests.get(url)
    # Проверяем, успешно ли выполнен запрос
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем все элементы с классом 'text', что соответствует тексту анекдота
        anekdots = soup.find_all('div', class_='text')
        
        # Выбираем случайный анекдот из полученного списка
        random_anekdot = random.choice(anekdots).get_text(strip=True)
        return random_anekdot
    else:
        print("Произошла ошибка при получении страницы: статус", response.status_code)
        return None

def send_anekdot(update, context):
    anekdot_text = get_anekdot()
    wav_file = context.user_data.get('wav_file')
    
    if not wav_file:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Сначала отправьте голосовое сообщение."
        )
        return
    
    # Уведомление пользователя о начале генерации анекдота
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Итак, сейчас будет А Н Е К Д О Т"
    )
    
    output_anek_wav = os.path.join(tempfile.gettempdir(), f'output_anek_{update.message.from_user.id}.wav')
    
    voice_clon(anekdot_text, wav_file, output_anek_wav)
    
    with open(output_anek_wav, 'rb') as f:
        context.bot.send_voice(chat_id=update.effective_chat.id, voice=f)
    
    # Удаление выходного wav файла
    os.remove(output_anek_wav)

dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(MessageHandler(Filters.voice, voice_handler))
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), text_handler))
dispatcher.add_handler(CommandHandler('mem', send_random_mem))
dispatcher.add_handler(CommandHandler('help', help_command))
dispatcher.add_handler(CommandHandler('anekdot', send_anekdot))

updater.start_polling()
updater.idle()
