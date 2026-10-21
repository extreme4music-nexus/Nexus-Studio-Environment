# Модулски Runtime — WP-001

Првиот функционален костур е синхрон и in-process, со stdlib зависности. Регистрацијата е експлицитна. Нема AI provider, вистински storage, NeuraFS, DAW или UI во демото.

## Стартување

Од проектот, по editable инсталација (`python -m pip install -e .`):

```text
nexus-runtime list
nexus-runtime validate --config examples/runtime-demo.json
nexus-runtime demo
nexus-runtime failure-demo
```

Алтернативно: `python -m nse_runtime demo`. За source checkout без инсталација постави PYTHONPATH на апсолутната `modules` папка во својата околина. Патеката не е вградена во runtime-от.

`list` и `validate` не стартуваат модули. `demo` враќа `FAKE module connection verified`, running snapshots и disposed snapshots по stop. `failure-demo` намерно враќа exit code 1 со `start_failed`; fake Nexus е failed, а fake storage е disposed. Конфигурацијата смее да избира само познати module IDs, не Python import paths. Lifecycle demos ги бараат двата fake модули.

Излезот е JSON со `simulation: true`. Кодови: 0 = успешна команда, 1 = module/runtime failure, 2 = неисправна/нечитлива конфигурација. `failure-demo` е успешна проверка на обработката на грешки кога враќа 1, не 0.

Види [архитектура](ARCHITECTURE.md), [додавање модул](MODULE_AUTHORING.md) и [проверки](VERIFICATION.md).
