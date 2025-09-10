### Облачный деплой ASIC Profit Bot (Render)

Ниже — максимально подробная пошаговая инструкция, что и где нажимать.

1) Подготовка локально
- Установите Git (если нет): https://git-scm.com/downloads
- Авторизуйтесь в GitHub (создайте репозиторий, если его нет): https://github.com/new

2) Создание репозитория и загрузка кода
- В Проводнике откройте папку проекта `Asic_profit_bot`.
- Щелкните правой кнопкой мыши в пустом месте → "Open in Terminal".
- Выполните команды:

```
git init
git branch -M main
git remote add origin https://github.com/ВАШ_АККАУНТ/asic-profit-bot.git

# Рекомендуется НЕ коммитить локальные БД и venv
echo "# Added by assistant" >> .gitignore
echo "Bot/venv/" >> .gitignore
echo "venv/" >> .gitignore
echo "*.db" >> .gitignore
echo "*.sqlite3" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "**/__pycache__/" >> .gitignore
echo ".env*" >> .gitignore
echo "Bot/error.log" >> .gitignore
echo "error.log" >> .gitignore

git add .
git commit -m "Deploy: Render worker with BOT_TOKEN env"
git push -u origin main
```

3) Render Blueprint deploy
- Откройте сайт: https://render.com
- Войдите через GitHub.
- Нажмите "New" → "Blueprint".
- Укажите ссылку на ваш репозиторий `asic-profit-bot` и подтвердите.
- Render увидит файл `render.yaml`. Нажмите "Apply".
- В проекте появится сервис с типом Worker.

4) Настройка переменной окружения
- Откройте созданный Worker-сервис.
- Вкладка "Environment" → "Add Environment Variable".
- Key: `BOT_TOKEN`
- Value: (ваш токен бота из @BotFather)
- Сохраните.

5) Деплой
- На странице сервиса нажмите "Manual Deploy" → "Deploy latest commit".
- Откройте вкладку "Logs" и дождитесь строки вида:
  - `Run polling for bot @...`
  - если видите ошибки, скопируйте их и пришлите в чат.

6) Проверка
- Откройте Telegram → найдите вашего бота → отправьте `/start`.
- Кнопки должны быть активны, меню закреплено внизу, ответы приходят быстро.

Примечания
- Файл `Bot/config.py` уже читает токен из переменной окружения `BOT_TOKEN`.
- Если нужен постоянный сторедж (на бесплатном плане Render файловая система эфемерная), переведу `users.db` на бесплатный Postgres (Neon/ElephantSQL) — скажите, подключу.

