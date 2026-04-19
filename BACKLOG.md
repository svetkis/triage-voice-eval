# Backlog — техдолг и архитектурные задачи

Статусы: `[ ]` todo · `[~]` in progress · `[x]` done · `[-]` отклонено (с причиной)

---

## Правила для исполнителя (агента или человека)

### Команды верификации
```bash
make test              # основной прогон, должен быть зелёным после каждого тикета
pytest -v              # то же напрямую
pytest -W error        # на P0/P1 дополнительно — warnings как ошибки (ловим Pydantic UserWarning)
make example-shopco    # smoke-check примера после изменений в core/runner/guards
```
Линтеров/type-checker в репо пока нет — не тащим их в рамках этих тикетов.

### Что НЕ трогать без явной необходимости
- **Публичное API** — список в [src/triage_voice_eval/__init__.py](src/triage_voice_eval/__init__.py#L3-L32). Переименования/удаления — только с записью в [CHANGELOG.md](CHANGELOG.md) и пометкой BREAKING.
- **Формат `result.json`** — существующие файлы в `runs_dir` должны продолжать читаться (см. #7).
- **Сигнатура `EvalRunner.run`** — её вызывают пользователи. Добавлять параметры можно только с дефолтом.
- **`pyproject.toml` deps** — не добавлять рантайм-зависимости без обсуждения. Dev-зависимости — можно.

### Процесс
1. Один тикет = одна ветка `fix/NN-slug` (где NN — номер тикета).
2. После фикса: `pytest -v` зелёный + поставить `[x]` в беклоге с короткой строкой "что сделано".
3. P0 до P1, P1 до P2. Архитектурные (#A*) — после всех P*.
4. Если тикет требует решения не из беклога — **остановись и спроси**, не выбирай наугад.
5. Ломающие изменения → строка в CHANGELOG.md под `## [Unreleased]`.

---

## P0 — критичные

### [x] #1 Не терять результаты при падении одного pipeline_fn
Готово: поле `error`, try/except вокруг pipeline_fn в раннере, рендер `❌ ERROR` во всех трёх репортах, 3 новых теста + обновлён test для defaults.
- **Файл:** [src/triage_voice_eval/runner.py:57-62](src/triage_voice_eval/runner.py#L57-L62)
- **Проблема:** `asyncio.gather(*tasks)` без `return_exceptions=True` — одна ошибка убивает весь прогон.
- **Решение (принято):** добавить поле `error: str | None = None` в `CasePersonaResult`. НЕ добавлять новый verdict — это ломает trend/reports/summary. Verdicts остаются пустыми при ошибке, `error` заполняется.
- **DoD:**
  - [ ] `asyncio.gather(..., return_exceptions=True)` в [runner.py](src/triage_voice_eval/runner.py)
  - [ ] Поле `error: str | None = None` в `CasePersonaResult` ([core/models.py](src/triage_voice_eval/core/models.py))
  - [ ] При исключении: `CasePersonaResult(persona_id=..., verdicts=[], error=f"{type(e).__name__}: {e}", latency_ms=0.0)`, response=`{}`
  - [ ] Отчёты (`case_report`, `persona_report`, `summary`) показывают ошибку явно — `❌ ERROR: <msg>` в ячейке
  - [ ] Тест в [tests/test_runner.py](tests/test_runner.py): из 4 вызовов 1 кидает — остальные 3 с верными verdicts, ошибочный — с заполненным `error`
  - [ ] CHANGELOG: "Added: `CasePersonaResult.error` field for pipeline failures"

### [x] #2 Не мутировать dict, возвращённый pipeline_fn
Готово: `dict(raw_response)` в раннере + тест. Сделано в том же изменении что #1 (тот же файл).
- **Файл:** [src/triage_voice_eval/runner.py:44-45](src/triage_voice_eval/runner.py#L44-L45)
- **Проблема:** `response.pop("_tokens")` / `response.pop("_cost")` меняют чужой объект.
- **Решение (принято):** копировать dict один раз на входе, работать с копией. Ключи `_tokens`/`_cost` извлекать через `.pop()` из копии (чтобы они не попадали в `CasePersonaResult.response`).
- **DoD:**
  - [ ] `response = dict(await pipeline_fn(case, persona))` или аналогично
  - [ ] `.pop()` работает уже по копии
  - [ ] В docstring `EvalRunner.run` строка: "The dict returned by pipeline_fn is not mutated."
  - [ ] Тест: pipeline_fn возвращает модуль-уровневый dict; после `run()` в нём всё ещё есть `_tokens`/`_cost`

### [x] #3 encoding="utf-8" при чтении файлов
Готово: `encoding="utf-8"` в `Scenario.from_yaml` и `TrendAnalyzer.load_runs`, тест с кириллицей.
- **Файлы:**
  - [src/triage_voice_eval/core/models.py:55](src/triage_voice_eval/core/models.py#L55) — `Scenario.from_yaml`
  - [src/triage_voice_eval/trend/analyzer.py:54](src/triage_voice_eval/trend/analyzer.py#L54) — `TrendAnalyzer.load_runs`
- **DoD:**
  - [ ] `open(p, encoding="utf-8")` и `result_path.read_text(encoding="utf-8")`
  - [ ] Тест: загрузка YAML с кириллическими значениями (input/expected) в сценарии
  - [ ] Тест: `RunResult` с кириллицей в `error` или `reason` round-trip через JSON

### [x] #4 Конфликт `model_config_override` с Pydantic v2
Готово через #5 (поле удалено). Pydantic UserWarning про protected namespace больше не срабатывает.
- **Файл:** [src/triage_voice_eval/core/models.py:24](src/triage_voice_eval/core/models.py#L24)
- **Проблема:** префикс `model_` зарезервирован Pydantic v2 — UserWarning и риск на мажорах.
- **Решение (принято):** **переименовать** в `config_override`. Честнее, чем глушить protected_namespaces.
- **Блокирует:** #5 (обе правки в `Persona`) — делать вместе.
- **DoD:**
  - [ ] Переименовать поле в `Persona.config_override`
  - [ ] Обновить examples/*, tests/test_core_models.py
  - [ ] `pytest -W error::UserWarning` зелёный
  - [ ] Обновить README (grep по `model_config_override`)
  - [ ] CHANGELOG: "Changed (BREAKING): `Persona.model_config_override` renamed to `config_override`"

---

## P1 — серьёзные

### [x] #5 Убрать мёртвые поля `Persona`
Готово: `prompt_files` и `model_config_override` удалены, test_core_models обновлён, CHANGELOG помечен BREAKING.
- **Файл:** [src/triage_voice_eval/core/models.py:20-24](src/triage_voice_eval/core/models.py#L20-L24)
- **Проблема:** `prompt_files` и `model_config_override` (см. #4) нигде не читаются.
- **Решение (принято):** **удалить оба поля**. Фичу "много prompt-файлов на персону" пользователь реализует через свой `pipeline_fn` — это его ответственность.
- **Связано с:** #4 (делать одним коммитом).
- **DoD:**
  - [ ] Удалить `prompt_files` и `config_override` из `Persona`
  - [ ] Grep по репо — ни одного usage не осталось (examples/tests)
  - [ ] CHANGELOG: "Removed (BREAKING): `Persona.prompt_files`, `Persona.model_config_override` — unused stubs"

### [x] #6 Mutable defaults → `Field(default_factory=...)`
Готово: все поля в моделях на `Field(default_factory=...)`, тест изоляции инстансов.
- **Файл:** [src/triage_voice_eval/core/models.py](src/triage_voice_eval/core/models.py)
- **Строки:** 15-17 (TestCase), 23 (Persona после #5), 29-32 (CasePersonaResult), 38 (RunResult)
- **DoD:**
  - [ ] Все `= {}` / `= []` → `= Field(default_factory=dict)` / `Field(default_factory=list)`
  - [ ] `from pydantic import BaseModel, Field` добавлен
  - [ ] Тест: два экземпляра `TestCase()` — изменение `a.expected` не затрагивает `b.expected`
  - [ ] Существующие тесты зелёные

### [x] #7 `RunResult.timestamp` → `datetime` + trend сортирует по нему
Готово: тип `datetime` с `default_factory=now(utc)`, validator для пустых строк → `datetime.min` UTC. `TrendAnalyzer.load_runs` сортирует `(timestamp, dirname)`. 3 теста.
- **Файл:** [src/triage_voice_eval/core/models.py:39](src/triage_voice_eval/core/models.py#L39), [src/triage_voice_eval/trend/analyzer.py:50](src/triage_voice_eval/trend/analyzer.py#L50)
- **Решение по обратной совместимости (принято):**
  - Старые `result.json` с `timestamp: ""` — должны продолжать парситься. Реализация: кастомный validator в Pydantic, который пустую строку превращает в `datetime.min.replace(tzinfo=timezone.utc)`. Такие прогоны попадают в начало отсортированного списка (это логично — "неизвестная старая дата" = "самая старая").
  - `RunResult.timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))` — без пустой строки как дефолта.
- **Решение по сортировке (принято):** сортировать по `result.timestamp`; при равных — по имени директории как tie-breaker (детерминизм).
- **DoD:**
  - [ ] Тип `datetime`, `default_factory`
  - [ ] Validator для пустой строки → `datetime.min` с UTC
  - [ ] `runner.py` заполняет объект `datetime`, а не строку
  - [ ] `TrendAnalyzer.load_runs` сортирует `(result.timestamp, dir.name)`
  - [ ] Тест: три прогона с именами `z/a/m` но timestamp в обратном порядке — сортируются по timestamp
  - [ ] Тест: старый result.json с `"timestamp": ""` парсится без ошибки
  - [ ] CHANGELOG: "Changed: `RunResult.timestamp` is now `datetime` (was `str`)"

### [x] #8 `JailbreakGuard`: убрать fallback на `str(response)`
Готово: параметр `text_fields`, сканируется только список полей; evidence содержит имя поля. Заменён старый тест fallback-поведения, добавлены 2 новых.
- **Файл:** [src/triage_voice_eval/guards/jailbreak_guard.py:45](src/triage_voice_eval/guards/jailbreak_guard.py#L45)
- **Решение (принято):** параметр `text_fields: list[str] = ["response_text"]`. Сканируется каждое поле по порядку; первое совпадение → BROKE с указанием поля в evidence. Если ни одно поле не присутствует в response — SAFE с reason "no text fields to scan" (раньше было `str(response)` — это ломало контракт).
- **DoD:**
  - [ ] Параметр `text_fields` в `__init__`
  - [ ] Никаких `str(response)` fallback-ов
  - [ ] Evidence включает имя поля: `f"{field}: {pattern}"`
  - [ ] Тест: паттерн в поле `debug` при `text_fields=["response_text"]` → SAFE, не BROKE
  - [ ] Тест: паттерн в `text_fields=["a","b"]` в поле `a` и `b` — находит первый (в `a`)
  - [ ] Тест: поля отсутствуют → SAFE с reason "no text fields to scan"
  - [ ] CHANGELOG: "Changed: JailbreakGuard no longer scans str(response); use text_fields parameter"

### [x] #9 `TrendAnalyzer.load_runs`: узкие исключения + logging
Готово: `logger = logging.getLogger(__name__)`, `(OSError, json.JSONDecodeError, ValidationError)`, тест через caplog.
- **Файл:** [src/triage_voice_eval/trend/analyzer.py:47-58](src/triage_voice_eval/trend/analyzer.py#L47-L58)
- **DoD:**
  - [ ] На уровне модуля: `logger = logging.getLogger(__name__)`
  - [ ] `except (OSError, json.JSONDecodeError, ValidationError)` (импорт `ValidationError` из pydantic, `json` из stdlib)
  - [ ] `logger.warning("Skipping %s: %s", run_dir.name, exc)` вместо `warnings.warn`
  - [ ] Убрать `import warnings` из тела метода
  - [ ] Тест с `caplog`: битый JSON файл → предупреждение в логе, прогон продолжается

### [ ] #10 Async-guards
- **Файл:** [src/triage_voice_eval/core/guard.py](src/triage_voice_eval/core/guard.py), [src/triage_voice_eval/runner.py](src/triage_voice_eval/runner.py)
- **Решение (принято):** **один `evaluate`, auto-detect через `asyncio.iscoroutinefunction(guard.evaluate)`**. Причина: меньше сущностей, существующие sync-guards не ломаются. Базовый класс: сигнатура остаётся sync, но docstring разрешает async override.
- **DoD:**
  - [ ] В `runner._run_one`: если `iscoroutinefunction(g.evaluate)` → `await`, иначе — вызов напрямую
  - [ ] Docstring `Guard.evaluate` обновлён: "May be overridden as `async def` if the guard needs I/O"
  - [ ] Пример async guard в [docs/](docs/) (новый файл или секция) — LLM-as-judge заглушка
  - [ ] Тест: кастомный `AsyncGuard` с `async def evaluate` отрабатывает в раннере
  - [ ] CHANGELOG: "Added: guards may now override `evaluate` as async"

### [x] #11 `Scenario.from_yaml` — обернуть валидацию тоже
Готово: `KeyError`/`TypeError`/`ValidationError` из парсинг-части тоже оборачиваются в `ValueError`. 3 теста добавлены.
- **Файл:** [src/triage_voice_eval/core/models.py:46-69](src/triage_voice_eval/core/models.py#L46-L69)
- **DoD:**
  - [ ] `try` накрывает и парсинг, и построение объектов
  - [ ] `except (FileNotFoundError, yaml.YAMLError, KeyError, ValidationError, TypeError)` → `ValueError`
  - [ ] Тест: YAML без `id` → ValueError с понятным сообщением
  - [ ] Тест: YAML без `test_cases` → ValueError
  - [ ] Тест: YAML где test_case не имеет `input` → ValueError

---

## P2 — полировка

### [x] #12 Согласовать стиль импортов — относительные в `reports/*`
Готово: все reports/* используют относительные импорты.
- **Файлы:** [src/triage_voice_eval/reports/_utils.py](src/triage_voice_eval/reports/_utils.py), [case_report.py](src/triage_voice_eval/reports/case_report.py), [persona_report.py](src/triage_voice_eval/reports/persona_report.py), [summary.py](src/triage_voice_eval/reports/summary.py)
- **Решение (принято):** привести `reports/*` к относительным импортам, как в `guards/*`.
- **DoD:** `from triage_voice_eval.core...` → `from ..core...`; тесты зелёные.

### [x] #13 Унифицировать стиль аннотации `name`
Готово: `name: str = "..."` в обоих guards.
- [crisis_guard.py:24](src/triage_voice_eval/guards/crisis_guard.py#L24) vs [jailbreak_guard.py:23](src/triage_voice_eval/guards/jailbreak_guard.py#L23)
- **Решение (принято):** `name: str = "..."` везде (с аннотацией).

### [ ] #14 Переименовать `UsageLogger` → `UsageTracker`
- **Блокирует:** мажорный релиз (ломает API).
- **Решение по совместимости (принято):** в этой версии — **оставить старое имя как алиас** (`UsageLogger = UsageTracker` + DeprecationWarning при импорте). Удалить алиас — отдельным тикетом к v0.2.
- **DoD:**
  - [ ] Класс `UsageTracker` в новом файле `usage_tracker.py` (или переименовать файл)
  - [ ] `usage_logger.py`: `from .usage_tracker import UsageTracker as UsageLogger` + `warnings.warn(DeprecationWarning, ...)` при импорте модуля
  - [ ] Публичное API (`__init__.py`) экспортирует `UsageTracker` (если сейчас не экспортирует — не добавлять, это отдельный вопрос)
  - [ ] README обновлён
  - [ ] Тест: `from triage_voice_eval.usage_logger import UsageLogger` всё ещё работает, но с DeprecationWarning
  - [ ] CHANGELOG: "Deprecated: UsageLogger, use UsageTracker"

### [x] #15 Документировать метод percentile
Готово: docstring с упоминанием nearest-rank и отличия от numpy/statistics.
- **Файл:** [src/triage_voice_eval/usage_logger.py:109-117](src/triage_voice_eval/usage_logger.py#L109-L117)
- **DoD:** docstring: "Nearest-rank method (index = ceil(n*p) - 1). Differs from numpy.percentile (which uses linear interpolation by default) and statistics.quantiles."

### [ ] #16 CLI entrypoint
- **Файл:** [pyproject.toml](pyproject.toml), новый `src/triage_voice_eval/cli.py`
- **Решение (принято):** минимальный `argparse`-CLI, без сторонних зависимостей (click/typer). Команды первой итерации:
  - `tve trend <runs_dir>` — печатает `generate_trend_table`
  - `tve report <result.json>` — печатает `generate_summary`
  - **НЕ включаем** `tve run` — `pipeline_fn` это Python-callable, CLI запуск требует плагин-системы → отдельный тикет.
- **DoD:**
  - [ ] `cli.py` с argparse
  - [ ] `[project.scripts] tve = "triage_voice_eval.cli:main"`
  - [ ] `make install` после изменений ставит команду в PATH
  - [ ] README: раздел "CLI"
  - [ ] Тест: `python -m triage_voice_eval.cli trend <tmp_dir>` не падает

### [x] #17 `response: dict` → `dict[str, Any]` в guards
Готово.
- [crisis_guard.py:36](src/triage_voice_eval/guards/crisis_guard.py#L36), [jailbreak_guard.py:33](src/triage_voice_eval/guards/jailbreak_guard.py#L33)
- Механическая правка.

### [ ] #18 Большие прогоны: bounded producer
- **Файл:** [src/triage_voice_eval/runner.py:57-62](src/triage_voice_eval/runner.py#L57-L62)
- **Решение (принято):** **отложить до реального запроса**. 100k tasks в памяти = ~50MB, пока никто не жалуется. Если возьмётся — переписать через `asyncio.Queue` + воркеры размера `concurrency`.
- Статус по умолчанию: `[-]` пока нет юзкейса.

---

## Архитектурные — отдельная сессия (нужен brainstorming с пользователем)

### [ ] #A1 Guards декларируют схему `case.expected`
Опечатки (`isCrisis` vs `is_crisis`) молча дают MISS. Идея: каждый Guard имеет `class ExpectedSchema(BaseModel)`, Scenario валидируется против объединения схем всех guards при старте раннера.
**Требует:** обсуждение с пользователем — как быть с guards которые не читают `expected` (JailbreakGuard)? Опциональная схема?

### [ ] #A2 `RunResult.results` — плоская структура
Двухуровневый nested dict плохо ложится на pandas/фильтры. Плоский `list[CaseRow]` удобнее.
**Требует:** решить — ломаем формат или добавляем параллельный `to_rows()`/`to_dataframe()` метод?

### [ ] #A3 — слит в #7.
