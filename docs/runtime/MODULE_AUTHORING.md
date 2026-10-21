# Додавање модул

1. Дефинирај јавен port во `nse_contracts` за способноста што ја изложуваш. Не го изложувај внатрешниот storage/model/runtime објект како општ јавен API.
2. Создај класа со immutable `ModuleDescriptor`, стабилен lowercase module_id, display_name, module version, contract_major, tuple dependencies и frozenset capabilities. Редоследот на регистрација не го диктира стартот.
3. Изложи `service` што го исполнува јавниот port. Конструкторот не отвора датотеки, sockets, модели или worker процеси.
4. Имплементирај initialize(context), start(), stop(), dispose(), health(). Stop мора да толерира делумно завршен start; dispose мора да толерира делумно initialize и да ги исчисти и ресурсите што не бараат start.
5. Во initialize користи `context.require('declared.dependency')`. Референцата е јавен service, не регистрација или соседна module имплементација. Непријавен dependency не е достапен во context.
6. Во composition root додај позната factory во allowlist и module ID во runtime конфигурацијата. Нема промени во соседните имплементации.
7. Додај success, missing-dependency и partial-failure тестови за своите ресурси. Документирај ги capabilities, errors, configuration и ограничувањата.

Проверлив пример е FakeStorage/FakeNexus во `modules/nse_runtime/demo.py`, со јавен DemoLookupPort во contracts. FakeNexus се поврзува со сервисот во initialize и прави lookup во start, кога dependency веќе е running. Примерот не пристапува до вистински датотеки и не повикува AI.

## Договор за конфигурација

```json
{
  "schema_version": 1,
  "modules": ["demo.nexus", "demo.storage"]
}
```

Не се дозволени непознати полиња, duplicate module names, неподдржана schema version или имиња што не постојат во factory allowlist. Descriptor ID мора да се совпаѓа со избраното factory име. Празен runtime е валиден за библиотечна употреба; lifecycle demo командите бараат целосна demo конфигурација.
