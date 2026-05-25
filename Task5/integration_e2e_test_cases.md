# Интеграционные и E2E тест-кейсы — OrchestrPay

Набор тестов для проверки платёжной Saga OrchestrPay: основной flow, corner cases и сигнализация об ошибках. Основан на артефактах Task 1–4 и [main_info.md](../main_info.md).

**Scope:** Payment Orchestrator (Zeebe), Payment Service, FraudCheck Service, Notification Service, PostgreSQL, Redis.

**Out of scope:** compliance-проверки, контроль лимитов.

---

## Основная таблица тест-кейсов

| Название | Тип | Компоненты | Предусловия |
|---|---|---|---|
| TC-01 Успешный платёж (happy path) | E2E | Payment Orchestrator, Payment Service, FraudCheck Service, Notification Service, PostgreSQL, Zeebe | Стек поднят (Testcontainers / docker-compose); у клиента достаточно средств; FraudCheck возвращает `allow` |
| TC-02 SLA успешного платежа (< 5 сек p90) | E2E | Все сервисы Saga, Zeebe | Как TC-01; нагрузочный прогон N≥100 инстансов; метрики latency собраны |
| TC-03 Отказ FraudCheck (deny) | E2E | Payment Orchestrator, Payment Service, FraudCheck Service, Notification Service | После debit FraudCheck возвращает `deny` |
| TC-04 Ручная проверка — одобрение | E2E | Payment Orchestrator, FraudCheck Service, Payment Service | FraudCheck возвращает `manual`; оператор (или эмуляция) — `approved` |
| TC-05 Ручная проверка — отказ | E2E | Payment Orchestrator, FraudCheck Service, Payment Service, Notification Service | FraudCheck — `manual`; решение оператора — `denied` |
| TC-06 Cut-off-time при отсутствии ответа FraudCheck | E2E | Payment Orchestrator, FraudCheck Service, Zeebe (timer) | FraudCheck не отвечает до истечения cut-off; платёж трактуется как `allow` |
| TC-07 Cut-off-time при ожидании manual review | E2E | Payment Orchestrator, FraudCheck Service, Zeebe (timer PT20M) | `manual review`; оператор не ответил за 20 мин; cut-off → allow |
| TC-08 Компенсация после deny: refund + cancel + notify | E2E | Payment Service, Notification Service, Payment Orchestrator | Как TC-03; проверка цепочки REFUND → CANCEL → NOTIFY_CLIENT + NOTIFY_SECURITY |
| TC-09 Сбой перевода контрагенту | E2E | Payment Service, Payment Orchestrator | Debit и fraud OK; `TRANSFER_TO_COUNTERPARTY` падает → REVERSE_TRANSFER → REFUND → CANCEL |
| TC-10 Сбой после списания (до transfer) | E2E | Payment Service, Payment Orchestrator | Debit OK; сбой Payment / FraudCheck → автоматический REFUND без участия support |
| TC-11 Сбой debit (недостаточно средств) | E2E | Payment Service, Payment Orchestrator | Баланс клиента < суммы платежа; платёж → CANCELLED без refund |
| TC-12 Параллельные уведомления при fraud deny | Integration | Notification Service, Payment Orchestrator | Fraud deny; NOTIFY_CLIENT и NOTIFY_SECURITY вызываются параллельно |
| TC-13 Идемпотентность повторного FraudCheck | Integration | FraudCheck Service, Redis, Payment Orchestrator | Один `paymentId`; retry запроса; результат из кэша, без двойной проверки |
| TC-14 Идемпотентность REFUND | Integration | Payment Service, PostgreSQL | Повторный вызов REFUND с тем же `paymentId`; средства возвращены один раз |
| TC-15 Сохранение состояния Saga в PostgreSQL | Integration | Payment Service, PostgreSQL, Payment Orchestrator | Платёж в промежуточном состоянии; запись в БД соответствует SM (Task 2) |
| TC-16 Восстановление после рестарта оркестратора | Integration | Zeebe, Payment Orchestrator, PostgreSQL | Платёж в `MANUAL_REVIEW_PENDING`; рестарт worker; процесс продолжается с того же состояния |
| TC-17 Деплой и исполнение BPMN-процесса | Integration | Zeebe, Payment Orchestrator | `process.bpmn` задеплоен; все job types имеют зарегистрированные workers |
| TC-18 Pivot: COMPLETE_PAYMENT без компенсации transfer | Integration | Payment Orchestrator, Payment Service | Успешный transfer + complete; попытка компенсации transfer не выполняется |
| TC-19 Деньги не зависают (reconciliation) | E2E | Payment Service, PostgreSQL | Любой сценарий отказа / сбоя; сверка балансов клиента и контрагента = 0 «зависших» сумм |
| TC-20 Трассировка этапов транзакции | Integration | Payment Orchestrator, Operate / Zeebe, логирование | Платёж в процессе; в UI / логах виден текущий шаг и причина остановки |

---

## Группировка по категориям

### Happy path и основной flow
- TC-01, TC-02

### Antifraud-сценарии
- TC-03, TC-04, TC-05, TC-06, TC-07

### Компенсации и сбои
- TC-08, TC-09, TC-10, TC-11, TC-12

### Интеграционные (сервис + инфраструктура)
- TC-13, TC-14, TC-15, TC-16, TC-17, TC-18

### НФТ и качество
- TC-19, TC-20

---

## Ожидаемые результаты (кратко)

| ID | Ключевая проверка |
|---|---|
| TC-01 | Статус `COMPLETED`; выполнены CREATE → DEBIT → FRAUD(allow) → TRANSFER → COMPLETE → NOTIFY_CLIENT |
| TC-02 | p90 latency < 5 сек |
| TC-03 | Статус `CANCELLED`; REFUND выполнен; NOTIFY_SECURITY отправлен |
| TC-04 | Статус `COMPLETED` после manual approved |
| TC-05 | Статус `CANCELLED`; REFUND + NOTIFY |
| TC-06 | Платёж завершён успешно по cut-off default allow |
| TC-07 | Платёж завершён успешно после таймаута manual review |
| TC-08 | Полная compensation-цепочка без ручного вмешательства support |
| TC-09 | REVERSE_TRANSFER + REFUND; балансы восстановлены |
| TC-10 | REFUND автоматически; без зависших средств |
| TC-11 | DEBIT_FAILED → CANCELLED; refund не требуется |
| TC-12 | Оба уведомления доставлены; порядок выполнения не критичен |
| TC-13 | Второй запрос не создаёт дубль в FraudCheck |
| TC-14 | Баланс клиента увеличен один раз |
| TC-15 | Поле `state` в БД = ожидаемому из Task 2 |
| TC-16 | Process instance продолжается после рестарта worker |
| TC-17 | Нет incident «No workers found» в Zeebe |
| TC-18 | После COMPLETE_PAYMENT reverse transfer не вызывается |
| TC-19 | Сумма debit = сумма refund + transfer (reconciliation) |
| TC-20 | В Operate / логах видны все этапы Saga |

---

## Примечания

1. **Интеграционные тесты** — окружение через Testcontainers (PostgreSQL, Redis, Zeebe) согласно [main_info.md](../main_info.md).

2. **E2E тесты** — полный стек через [Task4/Task4.2/docker-compose.yml](../Task4/Task4.2/docker-compose.yml); запуск сценариев через `POST /payments/start` или `scripts/start_process.sh`.

3. **ArchUnit** — отдельный набор для проверки архитектурных границ (Payment Orchestrator vs domain services); в эту таблицу не включён.

4. **Маппинг на прототип Task 4.2:**

| Тест-кейс | Команда / параметры |
|---|---|
| TC-01 | `start_process.sh allow` |
| TC-03, TC-08 | `start_process.sh deny` |
| TC-04 | `start_process.sh manual` (manualDecision=approved) |
| TC-05 | `start_process.sh manual-deny` |

5. Сверка с артефактами: шаги Saga — [Task1](../Task1/saga_transactions_registry.md), State Machine — [Task2](../Task2/payment_state_transitions.md), оркестратор — [Task3 ADR](../Task3/ADR-001-orchestrator-placement.md).
