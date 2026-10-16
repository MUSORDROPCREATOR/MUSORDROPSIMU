import time
import random
import os
import json
import re
import datetime
import sys
import platform
import csv
import string
import urllib.request
import hashlib

# ============ ТАМАГОЧИ =========
name_pet = ""

def save_pets():
    """Сохраняет питомцев в файл."""
    path = os.path.join(SAVE_DIR, "pets.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pets, f, ensure_ascii=False, indent=2)

def load_pets():
    """Загружает питомцев из файла."""
    path = os.path.join(SAVE_DIR, "pets.json")
    if not os.path.isfile(path):
        return default_pets()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_pets()

def default_pets():
    """Стандартные питомцы. Пусто — пока не выбрали."""
    return {}

dogs = {
    "active": None,
    "male": None,
    "female": None,
}

def default_pet():
    return {
        "hunger": 100,
        "health": 100,
        "clean": 100,
        "mood": 100,
        "energy": 100,
        "age": 1,
    }

def tamagochi():
    global pets
    
    # Если питомца ещё нет — выбираем
    if not pets or "active" not in pets:
        print("🐕 Выбери питомца:")
        print("1 — Пацан ")
        print("2 — Девка")
        choice = input("> ").strip()
        
        if choice == "1":
            pets["male"] = default_pet()
            pets["active"] = "male"
            print("✅ Ты выбрал пацана!")
        elif choice == "2":
            pets["female"] = default_pet()
            pets["active"] = "female"
            print("✅ Ты выбрал девку!")
        else:
            print("Пиши нормально!")
            return
        
        save_pets()
    
    # Теперь у нас точно есть active — идём в меню
    main_tamagochi()

def main_tamagochi():
    global pets
    if pets["active"] == "male":
        base_name = "Арчег"
    else:
        base_name = "Софиня"
    
    if "name" not in pets:  # ← проверяем имя в pets, а не name_pet
        print(f"Вообще эту собаку зовут {base_name}, но ты её можешь назвать по другому. Пустая строка = Базовое имя")
        name_pet_vopros = input()
        if not name_pet_vopros:
            pets["name"] = base_name
        else:
            pets["name"] = name_pet_vopros
        save_pets()
    else:
        while True:
            print(f"== ТАМАГОЧИ ({pets['name']}) ==")
            print()
            print("1 — Выйти")
            choice = input().strip()
            if choice == "1":
                main()
            else:
                print("Напиши понятнее")
pets = default_pets() # Глобалка питомцев
locked_mode_active = False
_log_rollbacks = 0   # счётчик откатов

# ============ ШИФРОВАНИЕ ЛОГА ============

ЛОГ_КЛЮЧ = "musordrop_secret_2026_log"


def xor_encrypt(text, key):
    """Шифрует/расшифровывает текст XOR-ом с ключом."""
    result = []
    for i, ch in enumerate(text):
        result.append(chr(ord(ch) ^ ord(key[i % len(key)])))
    return "".join(result)


def encode_log(data_str):
    """Кодирует строку в безопасный текст (hex)."""
    encrypted = xor_encrypt(data_str, ЛОГ_КЛЮЧ)
    return encrypted.encode("utf-8").hex()


def decode_log(hex_str):
    """Расшифровывает hex обратно в строку."""
    try:
        encrypted = bytes.fromhex(hex_str).decode("utf-8")
        return xor_encrypt(encrypted, ЛОГ_КЛЮЧ)
    except Exception:
        return ""

def save_log():
    global _log_rollbacks

    log_path = os.path.join(SAVE_DIR, "load_log.txt")

    data = (
        f"balance={balance}\n"
        f"money={money}\n"
        f"cases={cases}\n"
        f"streak={streak}\n"
        f"best_streak={best_streak}\n"
        f"name={name}\n"
        f"player_id={player_id}\n"
        f"funny_mode={смешно_mode}\n"
        f"freezes={freezes}\n"
        f"visited={'|'.join(visited_dates)}\n"
        f"frozen={'|'.join(frozen_dates)}\n"
        f"rollbacks={_log_rollbacks}\n"
    )

    encoded = encode_log(data)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(encoded)

def load_log():
    """Читает лог из файла (расшифрованный)."""
    log_path = os.path.join(SAVE_DIR, "load_log.txt")

    if not os.path.isfile(log_path):
        return {}

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            encoded = f.read().strip()

        decoded = decode_log(encoded)
        if not decoded:
            return {}

        data = {}
        for line in decoded.split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip()

        # Преобразуем числа
        for key in ["balance", "money", "cases", "streak", "best_streak", "freezes", "rollbacks"]:
            if key in data:
                try:
                    data[key] = int(data[key])
                except ValueError:
                    data[key] = 0

        # Логические
        if "funny_mode" in data:
            data["funny_mode"] = data["funny_mode"] == "True"

        # Списки
        if "visited" in data:
            data["visited"] = [d for d in data["visited"].split("|") if d]
        else:
            data["visited"] = []

        if "frozen" in data:
            data["frozen"] = [d for d in data["frozen"].split("|") if d]
        else:
            data["frozen"] = []

        return data

    except Exception:
        return {}

def check_log():
    """Сверяет файлы с логом. Если изменены — откатывает."""
    global balance, money, cases, streak, best_streak, name, player_id, смешно_mode, freezes
    global visited_dates, frozen_dates

    log_data = load_log()

    if not log_data:
        save_log()
        return 0

    rollbacks = log_data.get("rollbacks", 0)
    changed = False

    # Сверяем ключевые значения
    if log_data.get("balance") != balance:
        balance = log_data.get("balance", 100)
        changed = True

    if log_data.get("money") != money:
        money = log_data.get("money", 0)
        changed = True

    if log_data.get("streak") != streak:
        streak = log_data.get("streak", 0)
        changed = True

    if log_data.get("best_streak") != best_streak:
        best_streak = log_data.get("best_streak", 0)
        changed = True

    if log_data.get("name") != name:
        name = log_data.get("name", "")
        changed = True

    if log_data.get("player_id") != player_id:
        player_id = log_data.get("player_id", "")
        changed = True

    if log_data.get("funny_mode") != смешно_mode:
        смешно_mode = log_data.get("funny_mode", False)
        changed = True

    if log_data.get("freezes") != freezes:
        freezes = log_data.get("freezes", 2)
        changed = True

    if changed:
        rollbacks += 1

        print(f"\n🔄 Файлы изменены — откат из лога (откатов: {rollbacks})\n")

        # Сохраняем новый счётчик
        global _log_rollbacks
        _log_rollbacks = rollbacks

        # Пересохраняем
        save()

        if rollbacks >= 10:
            print("🎮 ЧИТЕР MODE АКТИВИРОВАН! 🎮")
            time.sleep(2)
            # Здесь можно включить читы

    return rollbacks

# Смешно mode по умолчанию
смешно_mode=False
# По умолчанию пароль существует
password_is_detected=True

# ============ ПЛАТФОРМА ============

def get_platform():
    """Определяет реальную платформу (Android, Windows, Linux, macOS)."""
    system = platform.system()
    release = platform.release().lower()

    if "android" in release:
        return "Android"
    if system == "Windows":
        return "Windows"
    if system == "Darwin":
        return "macOS"
    if system == "Linux":
        return "Linux"
    return system


PLAT = get_platform()

# ============ ПУТИ (зависят от ОС) ============

if PLAT == "Android":
    BASE_DIR = "/storage/emulated/0"
    SAVE_DIR = f"{BASE_DIR}/.musordrop"
    MODLOADER_DIR = f"{BASE_DIR}/modloader"
elif PLAT == "Windows":
    APPDATA = os.getenv("APPDATA") or os.path.expanduser("~")
    BASE_DIR = APPDATA
    SAVE_DIR = os.path.join(BASE_DIR, "musordropdata")
    MODLOADER_DIR = os.path.join(BASE_DIR, "musordrop_modloader")
elif PLAT == "Linux":
    BASE_DIR = os.path.expanduser("~")
    SAVE_DIR = os.path.join(BASE_DIR, ".musordrop")
    MODLOADER_DIR = os.path.join(BASE_DIR, "musordrop_modloader")
else:  # macOS
    BASE_DIR = os.path.expanduser("~")
    SAVE_DIR = os.path.join(BASE_DIR, "musordropdata")
    MODLOADER_DIR = os.path.join(BASE_DIR, "musordrop_modloader")

# общие пути для ВСЕХ ОС
MODS_DIR = os.path.join(SAVE_DIR, "mods")
MDS_DIR = os.path.join(SAVE_DIR, "mds")
TEMP_DIR = os.path.join(SAVE_DIR, "temp")
PROCESS_LOG = os.path.join(TEMP_DIR, "process.log")

# ============ ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ============

player_id = ""
money = 0
balance = 100
cases = 0
name = ""
streak = 0
best_streak = 0
last_date = ""
freezes = 2
diff = 0
day = 0
visited_dates = []
frozen_dates = []

rarities = []
countries = []
name_vishka = ""


# ============ ФУНКЦИЯ ОЧИСТКИ ЭКРАНА ============

def clear_screen():
    """Очищает экран в зависимости от ОС."""
    if PLAT == "Windows":
        os.system('cls')
    else:
        os.system('clear')


# ============ СПИСОК ОШИБОК 6G ============

ERRORS_6G = [
    "Спутник внезапно отключился",
    "Слишком много подключённых",
    "Тарелка улетела в космос",
    "Украинский дрон взорвал спутник",
    "Спутник заблокирован на территории РФ",
    "Спутник украли инопланетяне",
    "Иди спать",
    "Кто то удалил вышку, она обиделась и не хочет больше работать",
    "Спутник пытается скачать тик ток мод",
    "А где",
    "Я чай разлил",
    "УУУУ Я ЗАБЫЛ ЧЕ НАДО ДЕЛАТЬ",
    "Не хочу подключаться",
    "Тише тише тише слышишь крик",
    "Вадик не умный",
    "Спутник сидит в лайке",
    "Вышка в доту играет, не отвлекай пж",
    "Хэй, итс ми, итс верити, ой ема прости это спутник музыку от Horror Skunx слушает а я пою",
    "Марат фиксирует вышку",
    "Ой, это не 6G вышка",
    "В чикен ганчик играю я, самая лучшая игра",
    "Не забывай что это мусор дроп",
    "Вышка слушает газана",
    "Вышка... Ой это инопланетяне",
    "СКАЧАЙ МАААКС",
    "Учусь Python, день 1",
    "Папа маму разлюбил, чикен ганчик полюбил",
    "ДА ПОЧЕМУ SyntaxError",
    "Ура сегодня суббота",
    "Разрабу симулятора 8 лет",
    "У разраба симулятора скоро др, подари подарок",
    "Вышка сдохла",
    "ыаыааыааы",
    f"Удали {PLAT} и выйди на улицу потрогай травку",
    "07.12", # У меня тогда др, юхууу
    "Что то произойдёт через 2 месяца",
    "Подключись к другой вышке",
    "ыыыы я сломался",
    "жжжжжжжжжжжжжжжж ой прости я в пчёлку превратился",
]

# ============ ПАРОЛЬ ============

СОЛЬ = "musordrop_secret_2026_v1"


def hash_password(password):
    """Хеширует пароль (SHA-256 + соль)."""
    return hashlib.sha256((password + СОЛЬ).encode()).hexdigest()


def check_password(password, hashed):
    """Проверяет, совпадает ли пароль с хешем."""
    return hash_password(password) == hashed


def get_password_file():
    """Возвращает путь к файлу с паролем."""
    return os.path.join(SAVE_DIR, "password.hash")


def save_password(password):
    """Сохраняет хеш пароля в файл."""
    hashed = hash_password(password)
    with open(get_password_file(), "w", encoding="utf-8") as f:
        f.write(hashed)


def load_password_hash():
    """Загружает хеш пароля из файла."""
    path = get_password_file()
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def get_reset_count():
    """Возвращает число сбросов пароля."""
    path = os.path.join(SAVE_DIR, "reset_count.txt")
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return int(f.read().strip())
        except:
            return 0
    return 0


def increase_reset_count():
    """Увеличивает счётчик сбросов на 1."""
    path = os.path.join(SAVE_DIR, "reset_count.txt")
    count = get_reset_count() + 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(count))
    return count


def reset_password():
    """Сбрасывает пароль, просит новый."""
    clear_screen()
    print("\033[43m\033[30m")
    print("╔══════════════════════════════╗")
    print("║  🚨 4 НЕУДАЧНЫЕ ПОПЫТКИ! 🚨  ║")
    print("║                              ║")
    print("║  ПАРОЛЬ СБРОШЕН.             ║")
    print("║  Аккаунт сохранён.           ║")
    print("║  Задай новый пароль.         ║")
    print("║                              ║")
    print("║  ⚠️ Ещё 4 промаха — РЕСЕТ!   ║")
    print("╚══════════════════════════════╝")
    print("\033[0m")

    path = get_password_file()
    if os.path.isfile(path):
        os.remove(path)

    print()
    new = input("Придумай новый пароль (мин. 4 символа): ").strip()
    while len(new) < 4:
        new = input("❌ Слишком короткий! Попробуй ещё: ").strip()

    save_password(new)
    print("\n✅ Новый пароль установлен!")
    print("⚠️ ВНИМАНИЕ: следующая серия из 4 промахов — РЕСЕТ АККАУНТА!")
    time.sleep(2)


def reset_account_by_password():
    """Сбрасывает ВЕСЬ аккаунт (после второй серии из 4 промахов)."""
    clear_screen()
    print("\033[41m\033[37m")
    print("╔══════════════════════════════╗")
    print("║  💀 АККАУНТ СБРОШЕН! 💀      ║")
    print("║                              ║")
    print("║  Вторая серия из 4 промахов. ║")
    print("║  Все сохранения удалены.     ║")
    print("║                              ║")
    print("║  Начни заново.               ║")
    print("╚══════════════════════════════╝")
    print("\033[0m")
    time.sleep(3)

    files = [
        "username.txt", "balance.txt", "money.txt", "kases_opened.txt",
        "streak.txt", "best_streak.txt", "last_date.txt", "freezes.txt",
        "visited_dates.txt", "frozen_dates.txt", "player_id.txt",
        "password.hash", "reset_count.txt", "drops_log.csv"
    ]

    for file in files:
        path = os.path.join(SAVE_DIR, file)
        if os.path.isfile(path):
            try:
                os.remove(path)
            except Exception:
                pass

    print("\n💀 Аккаунт сброшен. Перезапуск...")
    time.sleep(2)
    os.execv(sys.executable, [sys.executable] + sys.argv)


def verify_password():
    """Проверяет пароль с двухуровневой системой сброса."""
    saved = load_password_hash()

    if not saved:
        password_is_detected=False
        return True  # пароля нет — пропускаем

    attempts = 0
    maximum = 4

    while attempts < maximum:
        entered = input(f"🔐 Пароль ({attempts + 1}/{maximum}): ").strip()

        if check_password(entered, saved):
            print("✅ Пароль верный! Добро пожаловать!")

            # обнуляем счётчик — игрок вспомнил пароль
            path = os.path.join(SAVE_DIR, "reset_count.txt")
            if os.path.isfile(path):
                os.remove(path)

            return True

        attempts += 1
        left = maximum - attempts

        if left > 0:
            print(f"❌ Неверный пароль! Осталось: {left}")

    # 4 попытки исчерпаны
    count = get_reset_count()

    if count >= 1:
        # уже был сброс пароля — теперь РЕСЕТ АККАУНТА
        reset_account_by_password()
        return False
    else:
        # первый раз — сброс пароля
        increase_reset_count()
        reset_password()
        return True

# ============ ID СИСТЕМА ============

def generate_id(length=8):
    """Генерирует уникальный ID из букв и цифр."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def generate_unique_id(length=8):
    """Генерирует уникальный ID, проверяя, что такого нет."""
    existing_ids = set()
    id_file = os.path.join(SAVE_DIR, "all_ids.txt")

    if os.path.isfile(id_file):
        with open(id_file, "r", encoding="utf-8") as f:
            existing_ids = set(line.strip() for line in f if line.strip())

    while True:
        new_id = generate_id(length)
        if new_id not in existing_ids:
            with open(id_file, "a", encoding="utf-8") as f:
                f.write(f"{new_id}\n")
            return new_id


# ============ ПРОВЕРКА СЕРВЕРОВ ============

def check_custom_server():
    """Проверяет доступность кастомного сервера по URL."""
    print("\n\033[36m═══════════════════════════════")
    print("       🌐 ПРОВЕРКА СЕРВЕРА")
    print("═══════════════════════════════\033[0m")
    print("\nВведи URL сервера (например, http://192.168.1.100:8080)")
    print("Или нажми Enter, чтобы отменить:")

    url = input("> ").strip()

    if not url:
        print("📴 Отменено")
        input("\nНажми Enter чтобы вернуться в меню...")
        main()
        return

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url

    print(f"\n🔍 Проверяю: {url}")
    print("⏳ Подожди...")

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
                "Connection": "close",
            }
        )
        start = time.time()
        response = urllib.request.urlopen(req, timeout=5)
        ping = (time.time() - start) * 1000

        print(f"\n✅ Сервер работает!")
        print(f"📊 Код ответа: {response.status}")
        print(f"⏱️ Пинг: {ping:.0f} мс")
    except urllib.error.HTTPError as e:
        print(f"\n⚠️ Сервер отвечает, но с ошибкой:")
        print(f"📊 Код: {e.code} — {e.reason}")
    except urllib.error.URLError as e:
        print(f"\n❌ Сервер недоступен:")
        print(f"📊 Причина: {e.reason}")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

    input("\nНажми Enter чтобы вернуться в меню...")
    main()


def check_bro():
    """Проверяет доступность DeepSeek."""
    try:
        req = urllib.request.Request(
            "https://deepseek.com",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        urllib.request.urlopen(req, timeout=5)
        print("Помощник разраба работает✅")
        return True
    except Exception as e:
        print(f"Помощник разраба не работает❎ ({e})")
        return False

# ============ СИСТЕМА МОДОВ ============

_mods_cache = None


def import_mods():
    """Копирует моды из modloader в mods, ведёт лог."""
    global _mods_cache

    os.makedirs(MODLOADER_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(MODS_DIR, exist_ok=True)

    if not os.path.isdir(MODLOADER_DIR):
        return

    files = [f for f in os.listdir(MODLOADER_DIR) if f.endswith(".json")]
    if not files:
        return

    with open(PROCESS_LOG, "w", encoding="utf-8") as log:
        log.write(f"=== Импорт модов ===\n")
        log.write(f"Дата: {datetime.datetime.now().isoformat()}\n")
        log.write(f"Найдено файлов: {len(files)}\n\n")

        imported = 0
        skipped = 0
        errors = 0

        for filename in files:
            src = os.path.join(MODLOADER_DIR, filename)
            dst = os.path.join(MODS_DIR, filename)
            temp = os.path.join(TEMP_DIR, filename)

            try:
                with open(src, "r", encoding="utf-8") as f:
                    mod = json.load(f)
                if not isinstance(mod, dict):
                    log.write(f"❌ {filename}: не объект JSON\n")
                    errors += 1
                    continue
            except json.JSONDecodeError as e:
                log.write(f"❌ {filename}: ошибка JSON — {e}\n")
                errors += 1
                continue

            if os.path.exists(dst):
                log.write(f"⏭️ {filename}: уже установлен\n")
                skipped += 1
                continue

            try:
                with open(src, "r", encoding="utf-8") as f:
                    content = f.read()
                with open(dst, "w", encoding="utf-8") as f:
                    f.write(content)
                with open(temp, "w", encoding="utf-8") as f:
                    f.write(content)

                log.write(f"✅ {filename}: импортирован\n")
                imported += 1
            except Exception as e:
                log.write(f"❌ {filename}: ошибка копирования — {e}\n")
                errors += 1

        log.write(f"\n=== Итог ===\n")
        log.write(f"Импортировано: {imported}\n")
        log.write(f"Пропущено: {skipped}\n")
        log.write(f"Ошибок: {errors}\n")

    _mods_cache = None


def clear_temp():
    """Очищает папку temp при сохранении."""
    if not os.path.isdir(TEMP_DIR):
        return

    for filename in os.listdir(TEMP_DIR):
        if filename == "process.log":
            continue
        path = os.path.join(TEMP_DIR, filename)
        try:
            os.remove(path)
        except Exception:
            pass


def load_mods():
    """Загружает все моды из папки mods (с кэшированием)."""
    global _mods_cache
    if _mods_cache is not None:
        return _mods_cache

    mods = []
    os.makedirs(MODS_DIR, exist_ok=True)

    if not os.path.isdir(MODS_DIR):
        _mods_cache = mods
        return mods

    for filename in os.listdir(MODS_DIR):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(MODS_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                mod = json.load(f)
            if not isinstance(mod, dict):
                continue
            mods.append(mod)
        except json.JSONDecodeError:
            continue
        except Exception:
            continue

    _mods_cache = mods
    return mods


def get_start_balance():
    """Возвращает стартовый баланс с учётом модов."""
    start = 100
    for mod in load_mods():
        if "start_balance" in mod:
            try:
                sb = int(mod["start_balance"])
                if sb >= 0:
                    start = sb
            except (ValueError, TypeError):
                pass
    return start


def strip_ansi(text):
    """Удаляет ANSI-коды из строки."""
    return re.sub(r'\033\[[0-9;]*[a-zA-Z]', '', text)


def sanitize_text(text):
    """Очищает текст от ANSI-кодов и управляющих символов."""
    if not isinstance(text, str):
        text = str(text)
    text = strip_ansi(text)
    text = ''.join(ch for ch in text if ch.isprintable() or ch == ' ')
    return text


def build_rarities():
    """Собирает все редкости: базовые + из модов."""
    base_rarities = [
        {"name": "🛑 Ошибка сервера +", "chance": 0.02, "message": "\033[41m\033[37m🛑 ОШИБКА 429! СЛУЖБА НЕ РАБОТАЕТ!\033[0m"},
        {"name": "⛔ Ошибка сервера", "chance": 0.05, "message": "\033[41m\033[37m⛔ Ошибка 503: сервис MUSOR DROP временно недоступен.\033[0m"},
        {"name": "🎉 УЛЬТРА ЛЕГЕНДАРКО", "chance": 0.04, "message": "\033[35m\033[1m🎉 УЛЬТРА ЛЕГЕНДАРКО!\033[0m"},
        {"name": "🎉 ЛЕГЕНДАРКО", "chance": 0.01, "message": "\033[35m🎉 ЛЕГЕНДАРКО!\033[0m"},
        {"name": "🔵 Супер-редко", "chance": 0.40, "message": "\033[34m\033[1m🔵 Супер-редко!\033[0m"},
        {"name": "🟢 Редко", "chance": 0.17, "message": "\033[34m🟢 Редко!\033[0m"},
        {"name": "🟡 Ункомонка", "chance": 0.13, "message": "\033[37m🟡 Ункомонка!\033[0m"},
        {"name": "⚪ Комонка", "chance": 0.20, "message": "\033[90m⚪ Ну вот, коммонка.\033[0m"},
    ]

    result = list(base_rarities)

    for mod in load_mods():
        for r in mod.get("rarities", []):
            if not isinstance(r, dict) or "name" not in r or "chance" not in r:
                continue
            try:
                chance = float(r["chance"])
                if chance <= 0:
                    continue
            except (ValueError, TypeError):
                continue

            clean_name = sanitize_text(r["name"])
            clean_message = sanitize_text(r.get("message", r["name"]))

            result.append({
                "name": clean_name,
                "chance": chance,
                "message": f"\033[33m{clean_message}\033[0m",
            })

    return result


def normalize(items):
    """Нормализует шансы, если сумма > 1.0."""
    total = sum(i["chance"] for i in items)
    if total > 1.0:
        for i in items:
            i["chance"] /= total
    return items


def build_countries():
    """Базовые + из модов."""
    base_countries = [
        {"name": "🇺🇸 США", "chance": 0.05, "prize": 15000, "special": "return_all"},
        {"name": "🇩🇪 Германия", "chance": 0.05, "prize": 8000, "special": "return_half"},
        {"name": "🇨🇳 Китай", "chance": 0.30, "prize": 3000, "special": "free_case"},
        {"name": "🇰🇵 Корея", "chance": 0.27, "prize": 1500, "special": "discount"},
        {"name": "🇰🇿 Казахстан", "chance": 0.13, "prize": 700},
        {"name": "🇷🇺 Россия", "chance": 0.20, "prize": 300},
    ]

    result = list(base_countries)

    for mod in load_mods():
        for c in mod.get("countries", []):
            if not isinstance(c, dict) or "name" not in c or "chance" not in c:
                continue
            try:
                chance = float(c["chance"])
                if chance <= 0:
                    continue
                prize = int(c.get("prize", 0))
                if prize < 0:
                    continue
            except (ValueError, TypeError):
                continue

            clean_name = sanitize_text(c["name"])

            result.append({
                "name": clean_name,
                "chance": chance,
                "prize": prize,
                "special": c.get("special"),
            })

    return result


def init_game_data():
    """Загружает базовые данные + моды."""
    global rarities, countries
    rarities = normalize(build_rarities())
    countries = normalize(build_countries())

# ============ СОХРАНЕНИЕ ============

def reset_account():
    """Сбрасывает аккаунт при повреждённых данных."""
    global name, balance, money
    balance = get_start_balance()
    money = 0
    name = ""
    save()
    print("🆕 Аккаунт сброшен")


def save():
    """Сохраняет все данные игрока в файлы."""
    global name, balance, money, visited_dates, frozen_dates, streak, best_streak, last_date, freezes, player_id, locked_mode_active
    os.makedirs(SAVE_DIR, exist_ok=True)

    with open(os.path.join(SAVE_DIR, "username.txt"), "w", encoding="utf-8") as f:
        f.write(f"{name}")
    with open(os.path.join(SAVE_DIR, "balance.txt"), "w", encoding="utf-8") as f:
        f.write(f"{balance}")
    with open(os.path.join(SAVE_DIR, "money.txt"), "w", encoding="utf-8") as f:
        f.write(f"{money}")
    with open(os.path.join(SAVE_DIR, "kases_opened.txt"), "w", encoding="utf-8") as f:
        f.write(f"{cases}")
    with open(os.path.join(SAVE_DIR, "streak.txt"), "w", encoding="utf-8") as f:
        f.write(f"{streak}")
    with open(os.path.join(SAVE_DIR, "best_streak.txt"), "w", encoding="utf-8") as f:
        f.write(f"{best_streak}")
    with open(os.path.join(SAVE_DIR, "last_date.txt"), "w", encoding="utf-8") as f:
        f.write(f"{last_date}")
    with open(os.path.join(SAVE_DIR, "freezes.txt"), "w", encoding="utf-8") as f:
        f.write(f"{freezes}")
    with open(os.path.join(SAVE_DIR, "visited_dates.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(visited_dates))
    with open(os.path.join(SAVE_DIR, "frozen_dates.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(frozen_dates))
    with open(os.path.join(SAVE_DIR, "player_id.txt"), "w", encoding="utf-8") as f:
        f.write(f"{player_id}")
    with open(os.path.join(SAVE_DIR, "locked.txt"), "w", encoding="utf-8") as f:
        f.write(f"{locked_mode_active}")

    print("💾 Сохранено!")
    clear_temp()
    save_log()
    save_pets()


def load_game():
    """Возвращает True, если загрузились. Иначе — False."""
    global name, balance, money, cases, visited_dates, frozen_dates
    global streak, best_streak, last_date, freezes, player_id, locked_mode_active
    global pets

    if not os.path.isfile(os.path.join(SAVE_DIR, "username.txt")):
        print("🆕 Новый игрок, начинаем с нуля")
        return False

    with open(os.path.join(SAVE_DIR, "username.txt"), "r", encoding="utf-8") as f:
        raw_name = f.read().strip()
    if not check_name(raw_name):
        print("⚠️ Файл с ником повреждён! Сброс аккаунта.")
        reset_account()
        return False

    with open(os.path.join(SAVE_DIR, "balance.txt"), "r", encoding="utf-8") as f:
        raw_balance = f.read()
    if not is_valid_number(raw_balance):
        print("⚠️ Файл баланса повреждён! Сброс аккаунта.")
        reset_account()
        return False

    with open(os.path.join(SAVE_DIR, "money.txt"), "r", encoding="utf-8") as f:
        raw_money = f.read()
    if not is_valid_number(raw_money):
        print("⚠️ Файл статистики повреждён! Сброс аккаунта.")
        reset_account()
        return False

    name = raw_name
    balance = int(raw_balance.strip())
    money = int(raw_money.strip())

    if os.path.isfile(os.path.join(SAVE_DIR, "player_id.txt")):
        with open(os.path.join(SAVE_DIR, "player_id.txt"), "r", encoding="utf-8") as f:
            player_id = f.read().strip()
    else:
        player_id = generate_unique_id(8)

    if os.path.isfile(os.path.join(SAVE_DIR, "kases_opened.txt")):
        with open(os.path.join(SAVE_DIR, "kases_opened.txt"), "r", encoding="utf-8") as f:
            raw_cases = f.read()
        cases = int(raw_cases.strip()) if is_valid_number(raw_cases) else 0
    else:
        cases = 0

    if os.path.isfile(os.path.join(SAVE_DIR, "visited_dates.txt")):
        with open(os.path.join(SAVE_DIR, "visited_dates.txt"), "r", encoding="utf-8") as f:
            visited_dates = [line.strip() for line in f if line.strip()]
    else:
        visited_dates = []

    if os.path.isfile(os.path.join(SAVE_DIR, "frozen_dates.txt")):
        with open(os.path.join(SAVE_DIR, "frozen_dates.txt"), "r", encoding="utf-8") as f:
            frozen_dates = [line.strip() for line in f if line.strip()]
    else:
        frozen_dates = []

    if os.path.isfile(os.path.join(SAVE_DIR, "streak.txt")):
        with open(os.path.join(SAVE_DIR, "streak.txt"), "r", encoding="utf-8") as f:
            raw = f.read().strip()
        streak = int(raw) if is_valid_number(raw) else 0
    else:
        streak = 0

    if os.path.isfile(os.path.join(SAVE_DIR, "best_streak.txt")):
        with open(os.path.join(SAVE_DIR, "best_streak.txt"), "r", encoding="utf-8") as f:
            raw = f.read().strip()
        best_streak = int(raw) if is_valid_number(raw) else 0
    else:
        best_streak = 0

    if os.path.isfile(os.path.join(SAVE_DIR, "last_date.txt")):
        with open(os.path.join(SAVE_DIR, "last_date.txt"), "r", encoding="utf-8") as f:
            last_date = f.read().strip()
    else:
        last_date = ""

    if os.path.isfile(os.path.join(SAVE_DIR, "freezes.txt")):
        with open(os.path.join(SAVE_DIR, "freezes.txt"), "r", encoding="utf-8") as f:
            raw = f.read().strip()
        freezes = int(raw) if is_valid_number(raw) else 2
    else:
        freezes = 2

    # ИСПРАВЛЕННЫЙ БЛОК ЧТЕНИЯ РЕЖИМА БЛОКИРОВКИ
    locked_path = os.path.join(SAVE_DIR, "locked.txt")
    if os.path.isfile(locked_path):
        with open(locked_path, "r", encoding="utf-8") as f:
            locked_mode_active = f.read().strip() == "True"
    else:
        locked_mode_active = False
    pets = load_pets()

    os.makedirs(MODS_DIR, exist_ok=True)
    os.makedirs(MDS_DIR, exist_ok=True)
    return True


# ============ ПРОВЕРКА ИМЕНИ И ЧИСЕЛ ============

def is_valid_number(text):
    """Проверяет, что строка — целое неотрицательное число."""
    text = text.strip()
    if not text:
        return False
    if not text.isdigit():
        return False
    number = int(text)
    if number > 1_000_000_000:
        return False
    return True


def check_name(name):
    """Проверяет, что ник на кириллице и не пустой."""
    name = name.strip()
    if len(name) < 3:
        return False
    if len(name) > 15:
        return False
    for ch in name:
        code = ord(ch)
        if not (1040 <= code <= 1103 or code in (1025, 1105)):
            if ch == ' ' or ch.isdigit() or ch == '_':
                continue
            return False
    return True


# ============ СТРАЙК ============

def check_streak():
    """Проверяет и обновляет страйк с учётом заморозок."""
    global streak, best_streak, last_date, freezes, diff, visited_dates, frozen_dates
    today = datetime.date.today().isoformat()

    if today not in visited_dates:
        visited_dates.append(today)

    if last_date == today:
        return

    if last_date == "":
        streak = 1
        last_date = today
        return

    last = datetime.date.fromisoformat(last_date)
    diff = (datetime.date.today() - last).days
    skipped = diff - 1

    if skipped == 0:
        streak += 1
        freezes = 2
    elif skipped == 1:
        if freezes > 0:
            freezes -= 1
            streak += 1
            yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
            if yesterday not in frozen_dates:
                frozen_dates.append(yesterday)
        else:
            streak = 1
    else:
        streak = 1

    if streak > best_streak:
        best_streak = streak

    last_date = today


def show_streak():
    """Показывает недельную полоску страйка."""
    global visited_dates, frozen_dates, streak, best_streak, freezes
    today = datetime.date.today()
    days = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]

    DAY_SHORT = {0: "пн", 1: "вт", 2: "ср", 3: "чт", 4: "пт", 5: "сб", 6: "вс"}
    icons = []
    names = []

    for day_date in days:
        names.append(DAY_SHORT[day_date.weekday()])
        date_str = day_date.isoformat()
        if date_str in visited_dates:
            icons.append("🔥")
        elif date_str in frozen_dates:
            icons.append("🧊")
        else:
            icons.append(" .")

    print("\n\033[36m═══════════════════════════════")
    print("         ТВОЙ СТРАЙК")
    print("═══════════════════════════════\033[0m")
    print()
    print("  " + "  ".join(icons))
    print("  " + "  ".join(names))
    print()
    print(f"🔥 Текущий страйк: {streak} дней")
    print(f"🏆 Лучший страйк: {best_streak} дней")
    print(f"🧊 Заморозок: {freezes}")
    print("\033[36m═══════════════════════════════\033[0m")

    input("\nНажми Enter чтобы вернуться в меню...")
    main()


# ============ СКИЛЛ ============

def progress_bar(current, target, length=20):
    """Рисует прогресс-бар."""
    if target <= 0:
        return "█" * length

    percent = min(current / target, 1.0)
    filled = int(length * percent)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percent * 100:.1f}%"


def show_skill():
    """Показывает скилл игрока в фарме."""
    print("\n\033[36m═══════════════════════════════")
    print("       📊 СКИЛЛ ФАРМА")
    print("═══════════════════════════════\033[0m")
    profit = balance - 100
    print(f"💻 Ты сидишь на {PLAT}!")
    print(f"🔑 ID: {player_id}")
    print(f"\n💰 Баланс: {balance}₽")
    print(f"💸 Потрачено: {money}₽")
    print(f"📈 Прибыль: {profit}₽")
    if money > 0:
        roi = (balance - 100) / money * 100
        print(f"🎯 ROI: {roi:.1f}%")
    else:
        print("🎯 ROI: — (ещё не играл)")
    print(f"🎰 Кейсов открыто: {cases}")
    print("\n🏆 Твой уровень:")

    levels = [
        (0, "🐣 НОВИЧОК"),
        (1_000, "🌱 НАЧИНАЮЩИЙ ФАРМЕР"),
        (10_000, "🌟 ОПЫТНЫЙ ФАРМЕР"),
        (50_000, "🥉 БРОНЗОВЫЙ ФАРМЕР"),
        (100_000, "🥈 СЕРЕБРЯНЫЙ ФАРМЕР"),
        (500_000, "🥇 ЗОЛОТОЙ ФАРМЕР"),
        (1_000_000, "💎 АЛМАЗНЫЙ ФАРМЕР"),
    ]

    current_level = levels[0]
    next_level = None

    for i, (threshold, title) in enumerate(levels):
        if balance >= threshold:
            current_level = (threshold, title)
            if i + 1 < len(levels):
                next_level = levels[i + 1]

    print(f"   {current_level[1]}")

    if next_level:
        threshold, title = next_level
        current_start = current_level[0]
        progress = balance - current_start
        target = threshold - current_start
        bar = progress_bar(progress, target, length=20)
        print(f"   {bar}")
        print(f"   До {title}: {threshold - balance}₽")
    else:
        print(f"   💎 МАКСИМАЛЬНЫЙ УРОВЕНЬ!")
        print(f"   [{('█' * 20)}] 100.0%")

    print("\033[36m═══════════════════════════════\033[0m")
    input("\nНажми Enter чтобы вернуться в меню...")
    main()


# ============ ЛОГ ДРОПОВ ============

def log_drop(drop_type, name_drop, chance, prize=None, cases_num=None):
    """Записывает дроп в CSV-файл."""
    log_path = os.path.join(SAVE_DIR, "drops_log.csv")
    file_exists = os.path.isfile(log_path)

    try:
        with open(log_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Дата", "Время", "Тип", "Название", "Шанс (%)", "Приз (₽)", "Номер кейса"])

            now = datetime.datetime.now()
            writer.writerow([
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S"),
                drop_type,
                name_drop,
                f"{chance * 100:.2f}",
                prize if prize else "",
                cases_num if cases_num else ""
            ])
    except Exception:
        pass


def show_top_drops():
    """Показывает топ-5 лучших дропов."""
    log_path = os.path.join(SAVE_DIR, "drops_log.csv")
    if not os.path.isfile(log_path):
        print("📊 Лог пуст (дропов ещё не было)")
        input("\nНажми Enter чтобы вернуться...")
        main()
        return

    best_drops = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("Название", "").strip()
                chance_str = row.get("Шанс (%)", "").strip()
                if not name or not chance_str:
                    continue
                try:
                    chance = float(chance_str)
                except ValueError:
                    continue
                best_drops.append({
                    "name": name,
                    "chance": chance,
                    "date": row.get("Дата", ""),
                    "time": row.get("Время", ""),
                    "type": row.get("Тип", ""),
                })
    except Exception:
        print("⚠️ Ошибка чтения лога")
        input("\nНажми Enter...")
        main()
        return

    if not best_drops:
        print("📊 Лог пуст")
        input("\nНажми Enter...")
        main()
        return

    best_drops.sort(key=lambda x: x["chance"])
    top5 = best_drops[:5]

    print("\n\033[36m═══════════════════════════════")
    print("       🏆 ТОП-5 ЛУЧШИХ ДРОПОВ")
    print("═══════════════════════════════\033[0m")
    print("\n   (самые редкие — самые крутые)\n")

    for i, drop in enumerate(top5, 1):
        print(f"   {i}. {drop['name']}")
        print(f"      📊 Шанс: {drop['chance']:.2f}%")
        print(f"      📅 {drop['date']} в {drop['time']}")
        print(f"      🎰 Тип: {drop['type']}")
        print()

    print("\033[36m═══════════════════════════════\033[0m")
    input("Нажми Enter чтобы вернуться в меню...")
    main()

# ============ КЕЙСЫ ============

def vopros():
    """Спрашивает: кейснуть ещё раз?"""
    while True:
        print("\nКейснуть ещё раз?")
        print("Да или нет или меню (д/н/м) ", end="")
        otvet = input().lower().strip()
        if otvet == "н":
            save()
            print("Пока!")
            exit_p()
        elif otvet == "д":
            save()
            kase()
            return
        elif otvet == "м":
            main()
            return
        else:
            print("пиши нормально!")


def kase():
    """Открывает обычный кейс."""
    global money, balance, cases
    print(f"Крутим кейс, {name}...")
    time.sleep(random.randint(1, 5))

    if balance < 5:
        print("💀 У тебя нет 5₽ на кейс. Иди ставку делай или зарабатывай.")
        main()
        return

    balance -= 5
    money += 5
    cases += 1

    chanse = random.random()
    cumulative = 0.0
    chosen = None

    for r in rarities:
        cumulative += r["chance"]
        if chanse < cumulative:
            chosen = r
            break

    if chosen is None:
        chosen = rarities[-1]

    if chosen["name"] == "🛑 Ошибка сервера +":
        print("🛑 Ошибка 429: сервис MUSOR DROP перегружен.")
        print("Игра закрывается. Запусти заново позже.")
        exit_p()

    msg = chosen.get("message", chosen["name"])
    print(f"{msg} шанс {chanse * 100:.2f}%")
    log_drop("kase", chosen["name"], chanse, cases_num=cases)
    vopros()
def vopros_c():
    """Спрашивает после кейса страны."""
    while True:
        print("\nКейснуть ещё раз?")
        print("Да или нет или меню (д/н/м) ", end="")
        otvet = input().lower().strip()
        if otvet == "н":
            print("Пока!")
            main()
        elif otvet == "д":
            kase_country()
            return
        elif otvet == "м":
            main()
            return
        else:
            print("пиши нормально!")


def kase_country():
    """Открывает кейс страны."""
    global money, balance, cases
    print(f"🌍 Открываем бокс с кейсами из разных стран, {name}...")
    time.sleep(2)

    if balance < 50:
        print("💀 Нужно 50₽ на кейс. Иди ставку делай или зарабатывай.")
        main()
        return

    balance -= 50
    money += 50
    cases += 1

    chanse = random.random()
    cumulative = 0.0
    chosen = None

    for c in countries:
        cumulative += c["chance"]
        if chanse < cumulative:
            chosen = c
            break

    if chosen is None:
        chosen = countries[-1]

    print(chosen["name"])
    print("\n🎁 Ваш приз:")

    prize = chosen.get("prize", 0)
    if prize > 0:
        print(f"💰 +{prize}₽ к балансу. Было: {balance}. Стало: {balance + prize}")
        balance += prize

    special = chosen.get("special")
    if special == "return_all":
        print(f"💸 Возврат всех потраченных: {money}₽")
        balance += money
        money = 0
    elif special == "return_half":
        half = money // 2
        print(f"💸 Возврат половины потраченных: {half}₽")
        balance += half
        money -= half
    elif special == "free_case":
        print("🍜 Бонус: бесплатный кейс!")
        balance += 5
        money = max(0, money - 5)
    elif special == "discount":
        print("🎮 Бонус: +1 к следующему кейсу (скидка 5₽)")
        balance += 5
        money = max(0, money - 5)

    log_drop("country", chosen["name"], chanse, prize=prize, cases_num=cases)
    save()
    vopros_c()


# ============ СТАВКА ============

def stavka():
    """Ставка на редкость."""
    global balance
    if balance <= 0:
        print("💀 Денег нет. Иди работай.")
        main()
        return

    print(f"\n💰 Баланс: {balance}")
    print("Сколько ставишь? (0 — назад)")
    try:
        summa = int(input())
    except ValueError:
        print("Число вводи, ёма!")
        stavka()
        return

    if summa == 0:
        main()
        return
    if summa < 0:
        print("Отрицательную ставку? Хитрый?")
        stavka()
        return
    if summa > balance:
        print(f"У тебя только {balance}, куда ты {summa} ставишь?")
        stavka()
        return

    print("\nНа что ставишь?")
    print("1 — Ультра-легендарка (шанс 5%, выплата x10)")
    print("2 — Легендарка (5%, x8)")
    print("3 — Супер-редко (40%, x3)")
    print("4 — Редко (17%, x2)")
    print("5 — Ункомонка (13%, x2)")
    print("6 — Коммонка (20%, x1.5)")
    vybor = input().strip()

    stavki = {
        "1": ("ультра-легендарку", 0.05, 10),
        "2": ("легендарку",        0.05, 8),
        "3": ("супер-редко",       0.40, 3),
        "4": ("редко",             0.17, 2),
        "5": ("ункомонку",         0.13, 2),
        "6": ("коммонку",          0.20, 1.5),
    }
    if vybor not in stavki:
        print("Нет такого варианта.")
        stavka()
        return

    nazvanie, shans, koeff = stavki[vybor]
    balance -= summa
    print(f"\nСтавишь {summa} на {nazvanie}...")
    time.sleep(2)

    chanse = random.random()
    if chanse < 0.05:
        vypalo = "1"
    elif chanse < 0.1:
        vypalo = "2"
    elif chanse < 0.5:
        vypalo = "3"
    elif chanse < 0.67:
        vypalo = "4"
    elif chanse < 0.8:
        vypalo = "5"
    else:
        vypalo = "6"

    if vypalo == vybor:
        vyigrysh = int(summa * koeff)
        balance += vyigrysh
        print(f"🎉 УГАДАЛ! Выпало: {stavki[vypalo][0]}. Забрал {vyigrysh}!")
    else:
        print(f"💀 Не угадал. Выпало: {stavki[vypalo][0]}.")

    print(f"💰 Баланс: {balance}")
    main()


# ============ 6G ============

def SIX_G():
    """Подключение к 6G вышке."""
    global name_vishka, balance
    print("\n\033[45m\033[30m================")
    print("ПОДКЛЮЧЕНИЕ К 6G")
    print("================\033[0m")
    vopros = input("\nВы действительно хотите подключить 6G? (д/н) ").strip().lower()

    if vopros == "д":
        print("Ищем ближайшую 6G вышку...")
        time.sleep(random.randint(1, 3))
        kilometres = random.randint(100, 1500)
        chanse = random.randint(1, 100)

        if chanse < 50:
            print(f"Вышка найдена! Расстояние: {kilometres / 100:.2f}км!")
            letters = string.ascii_uppercase
            digits = string.digits
            name_vishka = f"6G-{random.choice(letters)}{random.choice(digits)}{random.choice(letters)}-STATION"
            print(f"Подключаемся к вышке {name_vishka}...")
            time.sleep(2)

            if random.randint(1, 100) < 50:
                print(f"Вышка {name_vishka} успешно подключена!")
                print("Проверка интернета...")
                time.sleep(3)

                if kilometres > 1000:
                    procent = random.randint(50, 60)
                elif kilometres > 500:
                    procent = random.randint(50, 80)
                elif kilometres > 200:
                    procent = random.randint(50, 90)
                else:
                    procent = random.randint(50, 100)

                if procent >= 67:
                    print(f"Пинг: {procent}% (чем больше цифра, тем меньше пинг)")
                    print("Наслаждайтесь своим 6G!")
                    balance += 1000
                    print("🎁 +1000₽ за подключение!")
                else:
                    print("Плохой сигнал! Отключение...")
                    time.sleep(2)
            else:
                if смешно_mode == True:
                    e = random.choice(ERRORS_6G)
                    print(f"Не удалось подключиться. Ошибка: {e}")
                else:
                    print("Не удалось подключится. Попробуйте позже.")
        else:
            print("Не удалось найти вышку :( Попробуйте позже.")

    elif vopros == "н":
        pass
    else:
        print("не понял. перебрасываю в меню")
        time.sleep(1)

    input("\nНажми Enter чтобы вернуться в меню...")
    main()


# ============ СПИНОЧЕСАЛКА ============

def spinochesalka():
    """Рофл-функция."""
    print("ДА АЛО ЭТО РОФЛ БЫЛ")
    input("\nНажми Enter чтобы вернуться в меню...")
    main()


# ============ ПРОВЕРКА СТИХА ============

def check_poem():
    """Проверяет, выучил ли игрок стих Тютчева 'Листья'."""
    global balance

    original = """Пусть сосны и ели
Всю зиму торчат,
В снега и метели
Закутавшись, спят.
Их тощая зелень,
Как иглы ежа,
Хоть ввек не желтеет,
Но ввек не свежа.

Мы ж, лёгкое племя,
Цветём и блестим
И краткое время
На сучьях гостим.
Всё красное лето
Мы были в красе,
Играли с лучами,
Купались в росе!..

Но птички отпели,
Цветы отцвели,
Лучи побледнели,
Зефиры ушли.
Так что же нам даром
Висеть и желтеть?
Не лучше ль за ними
И нам улететь!

О буйные ветры,
Скорее, скорей!
Скорей нас сорвите
С докучных ветвей!
Сорвите, умчите,
Мы ждать не хотим,
Летите, летите!
Мы с вами летим!.."""

    print("\n\033[36m═══════════════════════════════")
    print("       📚 ПРОВЕРКА СТИХА")
    print("═══════════════════════════════\033[0m")
    print("\nВыучил стих Тютчева «Листья»?")
    print("Введи его (Enter для новой строки, пустая строка — конец):")
    print()

    lines = []
    while True:
        line = input()
        if line.strip() == "" and len(lines) > 0:
            break
        if line.strip() == "":
            print("⚠️ Введи хотя бы одну строку!")
            continue
        lines.append(line.strip())

    player_text = " ".join(lines).lower()
    original_text = " ".join(original.split()).lower()

    import string as st
    for punct in st.punctuation:
        player_text = player_text.replace(punct, "")
        original_text = original_text.replace(punct, "")

    player_words = player_text.split()
    original_words = original_text.split()

    matches = sum(1 for word in player_words if word in original_words)

    if len(player_words) == 0:
        print("📚 Ты ничего не ввёл!")
        main()
        return

    percent = matches / len(original_words) * 100

    print(f"\n📊 Совпадение: {percent:.1f}%")
    print(f"📝 Слов введено: {len(player_words)}")
    print(f"📖 Слов в оригинале: {len(original_words)}")

    if percent >= 90:
        print("\n🎉 МОЛОДЕЦ! Ты выучил стих!")
        print("🎁 Бонус: +5000₽")
        balance += 5000
    elif percent >= 70:
        print("\n⚠️ Почти! Но есть ошибки.")
        print("💸 Штраф: -100₽")
        balance -= 100
    else:
        print("\n💀 Не выучил! Иди учи!")
        print("📚 Возврат в меню...")
        input("\nНажми Enter чтобы вернуться...")
        main()
        return

    input("\nНажми Enter чтобы вернуться в меню...")
    main()


# ============ ДОКУМЕНТАЦИЯ ============

DOCS = {
    "README.md": """# MUSOR DROP SIMU 🎰

Симулятор открытия кейсов с сохранением, ставками и модами.

## Быстрый старт
1. Запусти `MUSORDROP.py`
2. Введи ник (русские буквы, 3-15 символов)
3. Открывай кейсы и фарми баланс!

## Документация
- [Как играть](how_to_play.md)
- [Как делать моды](how_to_mod.md)
- [Список фич](features.md)
- [FAQ](faq.md)
""",
    "how_to_play.md": """# Как играть 🎮

## Меню
1. **Продолжить лут** — открыть обычный кейс (5₽)
2. **Выход** — сохранить и выйти
3. **Баланс** — посмотреть сколько нафармил
4. **Ставка** — рискнуть деньгами
5. **Сохранить** — сохранить вручную
6. **Кейсы из стран** — бокс с разными странами (50₽)
7. **Скилл фарма** — статистика

## Редкости
- ⛔ Ошибка сервера — 5%
- 🎉 УЛЬТРА ЛЕГЕНДАРКО — 4%
- 🎉 ЛЕГЕНДАРКО — 1%
- 🔵 Супер-редко — 40%
- 🟢 Редко — 17%
- 🟡 Ункомонка — 13%
- ⚪ Комонка — 20%
""",
    "how_to_mod.md": """# Как делать моды 📦

## Формат
Мод — это JSON-файл в папке `mods/`.

## Пример
{
  "name": "Мой мод",
  "author": "твой_ник",
  "version": "1.0",
  "start_balance": 500,
  "rarities": [
    {"name": "🌈 МИФ", "chance": 0.01, "message": "МИФ!"}
  ],
  "countries": [
    {"name": "🇯🇵 Япония", "chance": 0.15, "prize": 2000}
  ]
}
""",
    "features.md": """# Фичи MUSOR DROP 📋

## v1.0
- ✅ Обычные кейсы
- ✅ Сохранение
- ✅ Ставки

## v1.1
- ✅ Кейсы стран
- ✅ Скилл фарма

## v1.2
- ✅ Моды на JSON
- ✅ Документация
- ✅ Цветной вывод редкостей

## v1.3
- ✅ 6G подключение
- ✅ Проверка серверов
- ✅ Топ-5 дропов
- ✅ Проверка стиха
- ✅ Система паролей
""",
    "faq.md": """# FAQ ❓

## Как сохранить игру?
Пункт 5 в меню или автоматически при выходе.

## Где хранятся сохранения?
Папка `.musordrop` в домашней директории.

## Как сбросить прогресс?
Удали файлы из папки сохранений.
""",
}


def ensure_docs():
    """Создаёт документацию, если её нет."""
    os.makedirs(MDS_DIR, exist_ok=True)
    created = 0
    for filename, content in DOCS.items():
        path = os.path.join(MDS_DIR, filename)
        if not os.path.isfile(path):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                created += 1
            except Exception:
                pass
    if created > 0:
        print(f"📖 Создано файлов документации: {created}")


# ============ HTML-РЕДАКТОР МОДОВ ============

HTML_EDITOR = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>MUSOR DROP — Редактор модов</title>
<style>
body { font-family: sans-serif; background: #1a1a1a; color: #e0e0e0; padding: 20px; max-width: 800px; margin: 0 auto; }
h1 { color: #ff4444; text-align: center; }
.section { background: #2a2a2a; border-radius: 10px; padding: 20px; margin-bottom: 20px; }
input, select { width: 100%; padding: 10px; background: #1a1a1a; border: 1px solid #444; color: #e0e0e0; margin-bottom: 10px; border-radius: 5px; }
button { background: #ff4444; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; margin-right: 10px; }
.preview { background: #0a0a0a; padding: 15px; border-radius: 5px; font-family: monospace; color: #44ff44; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }
</style>
</head>
<body>
<h1>🎰 MUSOR DROP — Редактор модов</h1>

<div class="section">
<h2>📦 Основное</h2>
<label>Название мода</label>
<input type="text" id="modName" placeholder="Мой крутой мод">
<label>Автор</label>
<input type="text" id="modAuthor" placeholder="твой_ник">
<label>Стартовый баланс</label>
<input type="number" id="startBalance" placeholder="500">
</div>

<div class="section">
<h2>👁️ Предпросмотр</h2>
<div class="preview" id="preview">Заполни форму — тут появится JSON</div>
</div>

<div class="section">
<button onclick="downloadMod()">💾 Скачать мод</button>
<button onclick="copyToClipboard()">📋 Скопировать JSON</button>
</div>

<script>
function buildMod() {
    const mod = {
        name: document.getElementById('modName').value || "Без названия",
        author: document.getElementById('modAuthor').value || "неизвестно",
        version: "1.0",
    };
    const sb = document.getElementById('startBalance').value;
    if (sb) mod.start_balance = parseInt(sb);
    return mod;
}
function updatePreview() {
    document.getElementById('preview').textContent = JSON.stringify(buildMod(), null, 2);
}
document.addEventListener('input', updatePreview);
function downloadMod() {
    const mod = buildMod();
    const json = JSON.stringify(mod, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = (mod.name.replace(/[^a-zа-я0-9]/gi, '_') || 'mod') + '.json';
    a.click();
}
function copyToClipboard() {
    navigator.clipboard.writeText(JSON.stringify(buildMod(), null, 2));
    alert('✅ JSON скопирован!');
}
</script>
</body>
</html>"""


def ensure_mod_editor():
    """Создаёт HTML-редактор модов, если его нет."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    editor_path = os.path.join(SAVE_DIR, "mode_creator.html")

    if not os.path.isfile(editor_path):
        try:
            with open(editor_path, "w", encoding="utf-8") as f:
                f.write(HTML_EDITOR)
            print(f"🌐 Создан редактор модов: {editor_path}")
        except Exception:
            pass


# ============ ВЫХОД ============

def exit_p():
    """Сохраняет и выходит."""
    save()
    clear_screen()
    sys.exit(0)

# ============ ГЛАВНОЕ МЕНЮ ============

def show_money():
    print(f"\n💰 Баланс: {balance}")
    print(f"💸 Всего списано на кейсы: {money}")

def info():
    print("\033[42m\033[30m=======================")
    print("    ИНФОРМАЦИЯ О ПРОЕКТЕ")
    print("=======================\033[0m")
    print("Дата создания: 02.10.2026")
    print("Версия: 1.0 2303")
    print("Дата создания версии: 16.10.2026")
    print("Автор: Кирилл")
    print("\nНажми Enter что бы вернуться в меню...")
    input()

# ===========РЕЖИМ БЛОКИРОВКИ==========
def locked_mode():
    clear_screen()
    print("        Игра переведена в режим блокировки.")
    print("Данная сессия предостановлена.")
    print("Для разблокировки введите пароль.")
    print()
    print("Пароль введите тут: ", end="")
    while True:
        entered = input().strip()
        saved = load_password_hash()

        if check_password(entered, saved):
            print("\n✅ Пароль верный! Разблокировка...")
            time.sleep(1)
            with open(os.path.join(SAVE_DIR, "locked.txt"), "w", encoding="utf-8") as f:
                f.write("False")
            clear_screen()
            os.execv(sys.executable, [sys.executable] + sys.argv)

        print("❌ Неверный пароль! Попробуй ещё.\n")
    
def create_password():
        # придумываем пароль
        print("\n🔑 Придумай пароль (минимум 4 символа):")
        password = input()
        while len(password) < 4:
            print("❌ Пароль слишком короткий. Попробуй ещё:")
            password = input()

        save_password(password)
        print("✅ Пароль сохранён!")

def logo():
    print('\n\033[31m█████████████████')
    print('█\033[1m\033[36mMUSOR DROP SIMU\033[0m\033[31m█')
    print('█████████████████\033[0m')

def main():
    """Главное меню игры."""
    global locked_mode_active
    while True:
        logo()
        print("\033[42m\033[30m\n1 — продолжить лут")
        print("2 — выход без сохранения")
        print("3 — посмотреть баланс и списанные деньки")
        print("4 — поставить ставку")
        print("5 — сохранить данные")
        print("6 — кейсы из различных стран")
        print("7 — посмотреть скилл фарма 📊")
        print("8 — документация 📖")
        print("9 — Спиночесалка")
        print("10 — Страйк")
        print("11 — Лог импорта модов 📝")
        print("12 — сделать за тебя дз")
        print("13 — Топ-5 лучших дропов 🏆")
        print("14 — Проверить помощника разраба")
        print("15 — Проверить свой сервер 🌐")
        print("16 — подключить интернет 6G")
        print("17 — Информация об проекте🆔")
        print("18 — Перезагрузить меню")
        print("19 — Выход")
        print("20 — Перезагрузится из настоящих данных файлов")
        print("21 — Перевести игру в режим блокировки")
        if balance >= 500:
            print("22 — Тамагочи")
        else:
            print(f"22 — 🔒 Заблокировано ({500 - balance} осталось)")
        print("\033[0m")
        choice = input().strip()

        if choice == "1":
            kase()
            return
        elif choice == "2":
            sys.exit(0)
        elif choice == "3":
            show_money()
        elif choice == "4":
            stavka()
            return
        elif choice == "5":
            save()
        elif choice == "6":
            kase_country()
            return
        elif choice == "7":
            show_skill()
            return
        elif choice == "8":
            print(f"\n📖 Документация в: {MDS_DIR}/")
            if os.path.isdir(MDS_DIR):
                for f in sorted(os.listdir(MDS_DIR)):
                    if f.endswith(".md"):
                        print(f"   📄 {f}")
            input("\nНажми Enter чтобы вернуться в меню...")
        elif choice == "9":
            spinochesalka()
        elif choice == "10":
            show_streak()
        elif choice == "11":
            if os.path.isfile(PROCESS_LOG):
                with open(PROCESS_LOG, "r", encoding="utf-8") as f:
                    print(f.read())
            else:
                print("📝 Лог пуст")
            input("\nНажми Enter чтобы вернуться в меню...")
        elif choice == "12":
            check_poem()
        elif choice == "13":
            show_top_drops()
        elif choice == "14":
            check_bro()
        elif choice == "15":
            check_custom_server()
        elif choice == "16":
            SIX_G()
        elif choice == "17":
            info()
        elif choice == "18":
            pass
        elif choice == "19":
            exit_p()
        elif choice == "20":
            load_game()
        elif choice == "21":
            if password_is_detected == True:
                locked_mode_active=True
                clear_screen()
                save()
                os.execv(sys.executable, [sys.executable] + sys.argv)
            else:
                print("У тебя нету пароля для блокировки. Задай пароль.")
                create_password()
        elif choice == "22":
            if balance >= 500:
                tamagochi()
            else:
                print("Ниче не понял")
        else:
            print("Ниче не понял")


# ============ ЗАПУСК ============

if __name__ == "__main__":
    clear_screen()

    # 1. ПЕРВЫМ ДЕЛОМ ЗАГРУЖАЕМ ДАННЫЕ (чтобы узнать статус locked_mode_active)
    game_exists = load_game()

    # 2. ПРОВЕРЯЕМ СТАТУС БЛОКИРОВКИ
    if locked_mode_active == True:
        locked_mode()  # Уходим в блокировку (если в файле True)
    else:
        # Показывать заставку, только если блокировки нет
        print("твой ", end="", flush=True)
        time.sleep(0.3)
        print("высокий ", end="", flush=True)
        time.sleep(0.5)
        print("шанс ", end="", flush=True)
        time.sleep(0.4)
        print("на ", end="", flush=True)
        time.sleep(0.3)
        print("большой ", end="", flush=True)
        time.sleep(0.6)
        print("дроп")
        time.sleep(0.6)
        print("\nмусор ", end="", flush=True)
        time.sleep(0.3)
        print("дроп")
        time.sleep(0.6)
        print("\n✨\n")
        time.sleep(0.8)

    # 3.ОБРАБАТЫВАЕМ ОСТАЛЬНУЮ ЛОГИКУ ИГРОКА
    if not game_exists:
        # новый игрок — придумывает ник и пароль
        print("\nВведите свой ник в кс и нажмите Enter")
        name = input()
        while not check_name(name):
            print("Попробуй ещё раз:")
            name = input()
        create_password()
        player_id = generate_unique_id(8)
        print(f"🔑 Твой ID: {player_id}")

        balance = get_start_balance()
        save()
    else:
        # старый игрок — проверка пароля
        print(f"🔑 Твой ID: {player_id}")
        verify_password()
        check_log()
        
    import_mods()
    check_streak()
    ensure_docs()
    ensure_mod_editor()
    init_game_data()
    main()