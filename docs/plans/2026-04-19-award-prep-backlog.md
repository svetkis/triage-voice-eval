# Бэклог: подготовка к Generation AI Awards

Дедлайн заявки: **27 апреля 2026**
Номинация: "Самый полезный open-source проект"

---

## Critical — блокируют подачу

- [x] **C1. Сломанный пример `generate_persona_report` в README**
  — Унифицированы сигнатуры: `generate_case_report` и `generate_persona_report` теперь принимают `RunResult` (как `generate_summary`). README и пример обновлены.

- [x] **C2. `expected: dict = {}` без типизации ключей**
  — Все `dict` в моделях типизированы как `dict[str, Any]`. Docstrings в CrisisGuard и JailbreakGuard документируют ожидаемые ключи.

- [x] **C3. Guard.evaluate вне семафора — гонка для stateful guard-ов**
  — Добавлен docstring в `Guard` с явным требованием stateless контракта. Документация `evaluate` расширена.

## Major — серьёзные проблемы

- [x] **M1. Нет реального LLM-примера**
  — Добавлен `examples/openai_crisis/` с реальным OpenAI вызовом, crisis-detection сценариями и usage tracking.

- [x] **M2. Пустой `__init__.py` — нет re-exports**
  — Добавлены re-exports всех публичных имён в `__init__.py`.

- [x] **M3. `UsageLogger` не интегрирован в `EvalRunner`**
  — Runner извлекает `_tokens` и `_cost` из response dict. Pipeline-функции возвращают usage metadata, runner автоматически заполняет CasePersonaResult.

- [x] **M4. `TrendAnalyzer.load_runs` — один сломанный файл роняет всё**
  — Добавлен try/except с `warnings.warn` + skip.

- [x] **M5. `_repair_truncated` может создать ложный LEAK**
  — Документировано в docstrings `parse()` и `_repair_truncated()`: предупреждение о truncated values и влиянии на safety guards.

- [x] **M6. Приоритет MISS vs LEAK в CrisisGuard не задокументирован**
  — Добавлен комментарий с объяснением приоритета.

- [x] **M7. Дублирование `_verdict_icon` в 3 файлах reports**
  — Вынесен в `reports/_utils.py`, дубликаты заменены на импорт.

- [x] **M8. Смешение абсолютных/относительных импортов в `guards/`**
  — `crisis_guard.py` приведён к относительным импортам.

## Minor — мелкие улучшения

- [x] **m1. CI тестирует только Python 3.11**
  — Добавлен matrix: Python 3.11 + 3.12.

- [x] **m2. Нет `py.typed` маркера**
  — Добавлен `py.typed` в пакет.

- [x] **m3. `Scenario.from_yaml` — сырые ошибки**
  — Обёрнуто в ValueError с понятным сообщением.

- [ ] **m4. `Guard.name` — class variable вместо abstractproperty**
  — Контракт неочевиден. Сделать `@property @abstractmethod def name(self) -> str`.

- [x] **m5. CHANGELOG: сломанные relative links**
  — Заменены на абсолютные GitHub URLs.

- [x] **m6. `UsageLogger` не задокументирован как asyncio-only**
  — Добавлен docstring с предупреждением о thread safety.

- [ ] **m7. `summary.py` — метрика pass rate не объясняет семантику**
  — `passed` = кейсы где ВСЕ персоны прошли ВСЕ guards. Это не очевидно, добавить пояснение.

- [ ] **m8. Нет тестов для `reports/` модулей**
  — `case_report`, `persona_report`, `summary` — 0 тестов.

- [ ] **m9. Дублирование логики обхода строк в `robust_json.py`**
  — `_extract_json_object` и `_repair_truncated` содержат одинаковый блок `in_string + escape`.

## Award-заявка

- [ ] **A1. Подготовить нарратив "БЫЛО → СТАЛО"**
  — Проблема с цифрами: почему `safety_score=0.73` опасен, сколько MISS/LEAK ловит framework в реальном BetweenTheLines.

- [ ] **A2. Скриншоты/демо eval прогона**
  — Matrix report, trend analysis, summary — визуальные артефакты для заявки.

- [ ] **A3. Метрики эффективности**
  — Стоимость одного eval run, latency, сколько регрессий поймано за время использования.
