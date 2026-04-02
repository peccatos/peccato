# d.fkk Store (Flask)

Минималистичный интернет-магазин на Python/Flask с адаптивным UI, мягкими анимациями, корзиной, checkout-потоком и простой админ-панелью.

## Что реализовано
- Адаптивный каталог/карточка/корзина (смартфоны, desktop, Telegram WebApp).
- Лёгкие micro-animations (fade-in, hover scale).
- Корзина в сессии + создание заказа в SQLite.
- Checkout-поток: заказ -> ссылка на оплату (stub для кассы).
- Webhook endpoint `/webhook/yookassa` (каркас под подтверждение оплаты).
- Админ-панель `/admin` с логином для редактирования каталога и просмотра заказов.

## Быстрый старт
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Откройте: `http://localhost:8000`.

## Настройки безопасности админки
Никогда не хардкодьте пароль в коде или шаблонах. Используйте переменные окружения:

```bash
export SECRET_KEY='your-long-random-key'
export ADMIN_USERNAME='owner'
export ADMIN_PASSWORD_HASH='pbkdf2:sha256:....'
```

Сгенерировать hash пароля:
```bash
python - <<'PY'
from werkzeug.security import generate_password_hash
print(generate_password_hash('VeryStrongPassword123!'))
PY
```

### Можно ли через браузер увидеть код входа в админку?
- Логин/пароль в шаблоны не выводятся.
- На фронте нет секретов, только форма.
- Проверка происходит на сервере.
- Если использовать переменные окружения + HTTPS + долгий пароль, админку нельзя "вытащить" через просмотр исходника страницы.

## Как разместить на GitHub
Репозиторий можно хранить на GitHub, но сам Flask-сервер нужно деплоить на Render/Railway/Fly.io (GitHub Pages не запускает Python backend).

## Подключение кассы (рекомендованный путь)
1. Клиент жмёт **Add to cart**.
2. На checkout вводит контакты.
3. Сервер создаёт заказ в БД со статусом `pending_payment`.
4. Сервер создаёт платёж в YooKassa/Tinkoff и возвращает `confirmation_url`.
5. Клиент уходит на оплату.
6. Касса шлёт webhook -> сервер верифицирует подпись и обновляет заказ в `paid`.
7. Опционально: отправить уведомление в Telegram бота/CRM.

