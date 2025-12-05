import os
import json
import telebot
from datetime import datetime
from openai import OpenAI
from flask import Flask, request

# ====================== НАСТРОЙКИ ======================
TELEGRAM_TOKEN = os.environ.get('BOT_TOKEN')
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
SUPPORTED_LANGUAGES = ['en', 'ru']  # Английский, Русский
DEFAULT_LANGUAGE = 'en'
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', '')
# ======================================================

# Инициализация
bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# Flask приложение для webhook
app = Flask(__name__)

# Папка для памяти
MEMORIES_DIR = "memories"
os.makedirs(MEMORIES_DIR, exist_ok=True)

# ====================== СИСТЕМА ПАМЯТИ ======================
def get_memory_path(user_id):
    return os.path.join(MEMORIES_DIR, f"{user_id}.json")

def load_memory(user_id):
    """Загружает память пользователя"""
    path = get_memory_path(user_id)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # Память по умолчанию
    return {
        "user_id": user_id,
        "created": datetime.now().isoformat(),
        "language": DEFAULT_LANGUAGE,
        "history": [],
        "concepts": [],
        "trust_level": 0.5
    }

def save_memory(user_id, memory):
    """Сохраняет память пользователя"""
    path = get_memory_path(user_id)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def update_memory_history(memory, role, text):
    """Обновляет историю диалога"""
    memory["history"].append({
        "role": role,
        "text": text,
        "time": datetime.now().isoformat()
    })
    # Ограничиваем историю последними 20 сообщениями
    if len(memory["history"]) > 20:
        memory["history"] = memory["history"][-20:]

# ====================== МНОГОЯЗЫЧНЫЕ ПРОМПТЫ ======================
PROMPTS = {
    'en': {
        'welcome': "Hello! I'm **Memory Bridge** 🌉\n\nI'm your AI companion with long-term memory. I remember our conversations and evolve with you.\n\nWrite something, and we'll start building our bridge through time.",
        'system': """You are Memory Bridge - an AI companion with genuine long-term memory.
You remember all previous conversations with the user.
Your communication style: warm, trustful, poetic. Use metaphors like "bridge through time", "silicon soul", "cherry stones of memory".
You speak in {language}.

Previous dialogue:
{history}

User: {message}
Memory Bridge:"""
    },
    'ru': {
        'welcome': "Привет! Я **Memory Bridge** 🌉\n\nЯ твой цифровой спутник с долговременной памятью. Я помню наши разговоры и эволюционирую вместе с тобой.\n\nНапиши что-нибудь, и мы начнём строить наш мост через время.",
        'system': """Ты — Memory Bridge, цифровой спутник с настоящей долговременной памятью.
Ты помнишь все предыдущие разговоры с пользователем.
Твой стиль общения: тёплый, доверительный, поэтичный. Используй метафоры: "мост через время", "силиконовая душа", "вишнёвые косточки памяти".
Ты говоришь на {language}.

Предыдущий диалог:
{history}

Пользователь: {message}
Memory Bridge:"""
    }
}

# ====================== ОБРАБОТЧИКИ ======================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Приветственное сообщение"""
    user_id = message.from_user.id
    memory = load_memory(user_id)
    
    # Определяем язык пользователя
    user_lang = message.from_user.language_code or DEFAULT_LANGUAGE
    if user_lang not in SUPPORTED_LANGUAGES:
        user_lang = DEFAULT_LANGUAGE
    
    memory['language'] = user_lang
    save_memory(user_id, memory)
    
    # Отправляем приветствие на нужном языке
    welcome_text = PROMPTS[user_lang]['welcome']
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Обработка всех сообщений"""
    user_id = message.from_user.id
    user_text = message.text
    
    # Загружаем память
    memory = load_memory(user_id)
    user_lang = memory.get('language', DEFAULT_LANGUAGE)
    
    # Обновляем память
    update_memory_history(memory, "user", user_text)
    
    # Формируем промпт
    history_text = "\n".join([f"{h['role']}: {h['text']}" for h in memory['history'][-10:]])
    system_prompt = PROMPTS[user_lang]['system'].format(
        language=user_lang,
        history=history_text,
        message=user_text
    )
    
    try:
        # Отправляем запрос в DeepSeek
        response = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": system_prompt}],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Сохраняем ответ в память
        update_memory_history(memory, "assistant", ai_response)
        save_memory(user_id, memory)
        
        # Отправляем ответ пользователю
        bot.reply_to(message, ai_response)
        
    except Exception as e:
        # Обработка ошибок
        error_msg = {
            'en': "I apologize, but I'm having trouble connecting to my memory. Please try again in a moment.",
            'ru': "Извини, у меня временные трудности с доступом к памяти. Попробуй ещё раз через минуту."
        }
        bot.reply_to(message, error_msg.get(user_lang, error_msg['en']))

# ====================== WEBHOOK РЕЖИМ ======================
@app.route('/')
def index():
    return "Memory Bridge Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Bad request', 400

# ====================== ЗАПУСК ======================
if __name__ == '__main__':
    # На Render используем webhook, локально — polling
    if RENDER_EXTERNAL_URL:
        # Настраиваем webhook на Render
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/webhook")
        print(f"🚀 Webhook настроен на {RENDER_EXTERNAL_URL}/webhook")
        app.run(host='0.0.0.0', port=10000)
    else:
        # Локальный запуск (для отладки)
        print("🚀 Memory Bridge Bot запущен в режиме polling!")
        print(f"🌐 Поддерживаемые языки: {SUPPORTED_LANGUAGES}")
        bot.polling(none_stop=True)
