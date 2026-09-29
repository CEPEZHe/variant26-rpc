# Практическое задание №1 — вариант 26

Прототип серверной части веб-приложения с удалённым вызовом процедур по TCP.
Данные хранятся только в оперативной памяти и на диск не сохраняются.

## Модель данных

Табличные записи представлены **списками**.

### Profile

`key, created, ip, locale, platform, user_agent`

### Query

`key, created, parameter, profile, description, tags, status`

Поле `profile` ссылается на `Profile.key`.

### Feedback

`key, created, response, status, exception, query, cache_hit`

Поле `query` ссылается на `Query.key`.

Для каждой сущности реализованы четыре операции:

1. создание новой записи;
2. получение всех записей;
3. получение одной записи по идентификатору;
4. редактирование записи.

Дополнительно реализована выборка `recent_feedback_projection` для варианта 26:

- выбираются записи `Query`, созданные за последние 8 минут;
- выполняется полное внешнее соединение `Query` и `Feedback` по условию
  `Query.key = Feedback.query`;
- возвращаются поля `Feedback.cache_hit`, `Feedback.exception` и `Query.tags`.

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
│   └── test_model.py # тест выборки
├── .gitignore
├── Makefile
├── requirements.txt
└── run.sh
```

## Установка

### Windows CMD

```bat
python3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Linux / macOS / Git Bash

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Этап 1 — модель и REPL

### Запуск в Windows CMD

```bat
set PYTHONPATH=src
python3 src\repl.py
```

### Запуск в Linux / macOS / Git Bash

```bash
make repl
```

### Пример работы REPL

```text
variant26> create_profile '{"key":1,"created":1000,"ip":"127.0.0.1","locale":"ru_RU","platform":"windows","user_agent":"demo"}'
variant26> get_profiles
variant26> get_profile 1
variant26> edit_profile 1 '{"locale":"en_US"}'

variant26> create_query '{"key":10,"created":995,"parameter":"x","profile":1,"description":"demo","tags":"test","status":"new"}'
variant26> get_queries
variant26> get_query 10
variant26> edit_query 10 '{"status":"done"}'

variant26> create_feedback '{"key":100,"created":996,"response":"ok","status":"success","exception":"","query":10,"cache_hit":0}'
variant26> get_feedback
variant26> get_feedback_item 100
variant26> edit_feedback 100 '{"cache_hit":1}'

variant26> recent_feedback_projection 1000
```

Пример обработки ошибки:

```text
variant26> get_profile 999
error: 'record with key=999 not found'
```

## Этап 2 — RPC по TCP

Порядок байт: **little-endian**.
Тело запроса и ответа передаётся в формате JSON.

### Формат запроса

| Поле | Смещение | Размер |
|---|---:|---:|
| Код операции | 0 | 2 байта |
| Размер тела запроса | 2 | 4 байта |
| JSON-тело | 6 | переменный |

### Формат ответа

| Поле | Смещение | Размер |
|---|---:|---:|
| Версия протокола | 0 | 1 байт |
| Код операции | 1 | 2 байта |
| Размер тела ответа | 3 | 5 байт |
| JSON-тело | 8 | переменный |

Версия протокола: `1`.

Все запросы и ответы журналируются в файл `journal.log`.

### Запуск сервера в Windows CMD

```bat
set PYTHONPATH=src
python3 src\server.py
```

Сервер слушает `127.0.0.1:9000`.

### Запуск сервера в Linux / macOS / Git Bash

```bash
./run.sh
```

или:

```bash
make server
```

### Пример RPC-клиента

```python
from rpc import RPCClient

client = RPCClient()
profile = client.create_profile(
    key=1,
    created=1000,
    ip="127.0.0.1",
    locale="ru_RU",
    platform="windows",
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

Тестирование RPC реализовано с помощью `RuleBasedStateMachine` из библиотеки
`hypothesis`.

State machine вызывает все 13 RPC-операций через настоящий путь:

```text
Hypothesis -> RPCClient -> TCP -> RPCServer -> RPCDispatcher -> DataModel
```

### Запуск тестов в Windows CMD

```bat
pytest -v
```

### Branch coverage

```bat
coverage run --branch -m pytest
coverage report -m
```

Тесты должны завершаться без ошибок, а отчёт `coverage` используется для
подтверждения покрытия RPC-методов тестами Hypothesis.

## Git-история

Работа разделена на отдельные коммиты по этапам:

```text
feat(model): implement variant 26 data model
feat(rpc): implement TCP RPC server and client
test(mbt): add Hypothesis model-based tests
```

## Публикация

Репозиторий должен быть публичным. После публикации на GitHub необходимо:

1. открыть `README.md`;
2. сохранить его в PDF через печать браузера;
3. загрузить PDF в СДО;
4. добавить в СДО URL публичного репозитория.
