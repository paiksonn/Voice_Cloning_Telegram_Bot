from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
import tempfile
import torch
from TTS.api import TTS
import soundfile as sf
import random


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
    
# def wav_to_ogg_converter(input_file: str, output_file: str):
#     # Конвертируем из wav в ogg
#     data, samplerate = sf.read(input_file)
#     sf.write(output_file, data, samplerate, format='OGG', subtype='VORBIS')    

updater = Updater('6426199729:AAGAhHT25qO4WSqoYcGVYHUE9701l3CnXoU')
dispatcher = updater.dispatcher

def help_command(update, context):
    help_text = """
Доступные команды:
/start - Начать работу с ботом и получить инструкции (можно использовать, чтобы перезаписать аудио)
/mem - Получить случайный мем из предоставленной коллекции смешнявок (можно спамить эту команду бесконечно, но все мемы рандомные, поэтому автор бота не несет ответственности за чьи-то задетые чувства)
/help - Получить список доступных команд
    """
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Пожалуйста, отправьте голосовое сообщение на русском языке длиной от 20 до 40 секунд.")
    context.bot.send_message(chat_id=update.effective_chat.id, text="Для получения списка всех доступных команд введите /help")

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

dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(MessageHandler(Filters.voice, voice_handler))
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), text_handler))
dispatcher.add_handler(CommandHandler('mem', send_random_mem))
dispatcher.add_handler(CommandHandler('help', help_command))

updater.start_polling()
updater.idle()
