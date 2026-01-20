user_lang = {}

def set_language(user_id, lang):
    user_lang[user_id] = lang

def get_language(user_id):
    return user_lang.get(user_id, "uz")  # default 'uz'
