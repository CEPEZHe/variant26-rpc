# Практическое задание №1 — вариант 26

Прототип серверной части веб-приложения с удалённым вызовом процедур по TCP.
Данные хранятся только в оперативной памяти.

## Модель данных

Записи представлены **списками**.

### Profile

`key, created, ip, locale, platform, user_agent`

### Query

`key, created, parameter, profile, description, tags, status`

`profile` ссылается на `Profile.key`.

### Feedback

`key, created, response, status, exception, query, cache_hit`

`query` ссылается на `Query.key`.

Для каждой сущности реализованы четыре операции: создание, получение всех
записей, получение одной записи по идентификатору и редактирование.
Дополнительно реализована выборка `recent_feedback_projection`, соответствующая
формуле варианта 26: выбираются Query за последние 8 минут, выполняется полное
внешнее соединение с Feedback по `Query.key = Feedback.query`, после чего
возвращаются `Feedback.cache_hit`, `Feedback.exception`, `Query.tags`.

Всего модель содержит 13 RPC-операций.

## Структура проекта

```text
.
├── src/
│   ├── model.py      # модель слоя доступа к данным
│   ├── repl.py       # интерактивный режим
│   ├── rpc.py        # протокол, сервер, диспетчер и клиент
│   └── server.py     # точка запуска TCP-сервера
├── tests/
│   ├── test_mbt.py   # Model-Based Testing на Hypothesis
│   └── test_model.py # небольшой локальный тест выборки
├── .gitignore
├── Makefile
├── requirements.txt
└── run.sh
```

## Установка

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Этап 1 — модель и REPL

Запуск:

```bash
make repl
```

Пример:

```text
variant26> create_profile '{"key":1,"created":1000,"ip":"127.0.0.1","locale":"ru_RU","platform":"linux","user_agent":"demo"}'
variant26> create_query '{"key":10,"created":1000,"parameter":"x","profile":1,"description":"demo","tags":"test","status":"new"}'
variant26> get_queries
variant26> get_query 10
variant26> edit_query 10 '{"status":"done"}'
variant26> recent_feedback_projection 1100
```

Ошибки (например, неизвестный ключ или дублирующий идентификатор) выводятся с
префиксом `error:`.

## Этап 2 — RPC по TCP

### Формат запроса

Порядок байт — **little-endian**.

| Поле | Смещение | Размер |
|---|---:|---:|
| Код операции | 0 | 2 байта |
| Размер тела | 2 | 4 байта |
| JSON-тело | 6 | переменный |

### Формат ответа

| Поле | Смещение | Размер |
|---|---:|---:|
| Версия протокола | 0 | 1 байт |
| Код операции | 1 | 2 байта |
| Размер тела | 3 | 5 байт |
| JSON-тело | 8 | переменный |

Версия протокола: `1`.

Сервер журналирует **все запросы и ответы** в `journal.log`.

Запуск сервера:

```bash
./run.sh
```

или:

```bash
make server
```

Сервер слушает `127.0.0.1:9000`.

Пример клиента:

```python
from rpc import RPCClient

client = RPCClient()
profile = client.create_profile(
    key=1,
    created=1000,
    ip="127.0.0.1",
    locale="ru_RU",
    platform="linux",
    user_agent="demo",
)
print(profile)
print(client.get_profiles())
```

## Коды RPC-операций

| Код | Метод |
|---:|---|
| 1 | `create_profile` |
| 2 | `get_profiles` |
| 3 | `get_profile` |
| 4 | `edit_profile` |
| 5 | `create_query` |
| 6 | `get_queries` |
| 7 | `get_query` |
| 8 | `edit_query` |
| 9 | `create_feedback` |
| 10 | `get_feedback` |
| 11 | `get_feedback_item` |
| 12 | `edit_feedback` |
| 13 | `recent_feedback_projection` |

## Этап 3 — Model-Based Testing

Тестирование выполнено через `RuleBasedStateMachine` из `hypothesis`.
State machine вызывает все 13 RPC-операций через `RPCDispatcher`.

Запуск:

```bash
make test
```

Отчёт о покрытии с учётом ветвей:

```bash
make coverage
```

Для проверки именно требования о 13 RPC-операциях используется
`tests/test_mbt.py`.

## Рекомендуемая история коммитов

```text
feat(model): implement variant 26 in-memory data model
feat(rpc): implement TCP RPC protocol and client
feat(tests): add hypothesis model-based tests
```

## Публикация на GitHub

```bash
git init
git add .
git commit -m "feat(model): implement variant 26 in-memory data model"
# После добавления RPC и тестов лучше сделать отдельные коммиты по этапам.
git branch -M main
git remote add origin https://github.com/USERNAME/variant26-rpc.git
git push -u origin main
```

Перед сдачей убедитесь, что репозиторий публичный. Затем откройте README на
GitHub, нажмите `Ctrl+P` и сохраните его как PDF. В СДО загрузите PDF и URL
репозитория.
