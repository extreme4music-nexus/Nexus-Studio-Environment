# WP-001 — Модулски костур

Статус: одобрен од корисникот и имплементиран локално. 24 тестови и offline wheel build/install поминаа. Remote Linux/macOS проверки остануваат gate во FRAME-09; види [verification](../../runtime/VERIFICATION.md). Поврзани задачи: FRAME-01 до FRAME-10 во MASTER_CHECKLIST.

## Корисничка и инженерска цел

Да имаме едно место каде што независните модули се приклучуваат преку договор, со предвидлив старт, запирање, грешки и комуникација. Додавање модул не бара препишување на соседните модули.

## Предложени конкретни избори

- Python >=3.12, според постојниот scaffold; stdlib за првиот runtime, без нов transport/UI framework.
- Нов nse_runtime пакет и docs/runtime област; contracts остануваат во nse_contracts.
- Експлицитна регистрација на factories/instances во composition root; нема filesystem plugin scan.
- Еден in-process runtime. Module descriptor има module_id, version, contract_major, required dependency IDs и capabilities. Во првиот пакет точно совпаѓање на поддржаниот contract major; нема општ semver solver.
- Descriptor/config валидација без import на произволно име од корисничка конфигурација. Factory mapping е од познат код.
- За првиот пакет lifecycle е едноставен и последователен; идните async/worker jobs се посебна граница. Нема fake гаранции за прекин на произволен блокиран third-party код.
- Пробни модули во tests/examples, со јасен demo статус. Реален Nexus и NeuraFS не се стартуваат.

## Редослед на чекори

1. Прочитај применливи AGENTS/проектни насоки; запиши точен Git HEAD, status и постојните документациски промени. Не ги препокривај.
2. Разработи ги lifecycle транзициите и descriptor/health/error DTO-ата во contracts. Оддели installation/capability discovery од runtime state каде што е потребно; не користи ист enum за неповрзани состојби.
3. Имплементирај registry со duplicate ID и валидирани descriptors.
4. Пресметај dependency graph, missing dependency/version checks и topological order; откриј cycles пред initialize.
5. Вбризгај service references преку ports во composition root. Runtime смее да ги познава concrete factories; соседните business модули не.
6. Имплементирај initialize/start, reverse stop и release/dispose ресурси. При partial initialize/start неуспех зачувај ја првата грешка, исчисти ги веќе стекнатите ресурси и пријави и cleanup грешки без да ја сокриеш првичната.
7. Дефинирај repeat start/stop и операција по failed state; експлицитно однесување, без двојно стартување или заборавени ресурси.
8. Додај health/status snapshots, stable error codes и correlation IDs. Diagnostics не создава чувствителни memory записи.
9. Додај минимална конфигурација и команда за list/validate/demo. Нема credentials, network listeners или зависност од Z:.
10. Два fake модули докажуваат dependency wiring и еден типизиран service резултат. Потоа failure demo докажува cleanup и неуспешен статус.
11. Изврши релевантни тестови и Windows smoke; прошири CI matrix без тврдење дека remote CI е помината додека нема резултат.
12. Ажурирај architecture/module authoring упатство, checklist и session log. Commit/push е одделно експлицитно наведено во испораката на имплементацискиот пакет, а не подразбран исход на овој план.

## Предвидени датотеки и граници

contracts: module descriptor/protocols/errors; runtime: registry/dependencies/container/lifecycle/config/CLI; tests: contracts/registry/lifecycle/demo и постојните boundary проверки. Точната распределба се избира за читливост, не за однапред фиксен број фајлови. Постојниот boundary тест мора да дозволи composition root легитимно да поврзува имплементации, но да задржи забрана за business-to-business implementation imports.

## Acceptance сценарија

| Сценарио | Очекуван резултат |
|---|---|
| A бара B, и двата се валидни | B се иницијализира/стартува пред A; A добива само јавен port. |
| Duplicate module_id | Јасна грешка пред lifecycle. |
| Missing dependency / неподдржан major | Validation failed; нема partial start. |
| Cycle A→B→A | Cycle е пријавен пред initialize. |
| B стартува, A откажува | B се стопира; иницијализираните ресурси се ослободуваат; root cause е зачуван. |
| Cleanup исто откажува | Се пријавуваат и root и cleanup проблемите; нема лажен healthy статус. |
| Двоен start / двоен stop | Договорено deterministic однесување, проверено со тест. |
| Service повик меѓу fake модули | Реален очекуван demo резултат; јасно означено дека е fake. |
| Legacy директориум е присутен | Нема негово откривање/import/извршување. |
| CLI се извршува надвор од NAS | Костурот работи со конфигуриран workspace; нема hardcoded NAS path. |

## Надвор од опфат

Реални модели/провајдери, DAW, звук, NeuraFS поправки, UI toolkit избор, persistent project DB, distributed event bus, marketplace и самоинсталирање plugins.

## Ризици и враќање

Главни ризици: претерано општ framework, мешање module/version со contract/version, нетестиран partial failure и нарушување на постојниот boundary тест. Ги ограничуваме со мал descriptor, два fake модули и конкретни acceptance сценарија. Промените се прават во нови runtime/contract области со посебен commit; враќањето го отстранува само тој пакет, не стари проекти или кориснички документи.

## Завршено кога

FRAME-01–10 имаат докази; success и failure demo се повторливи; документацијата објаснува додавање нов модул; нема legacy промени и нерешени критични lifecycle проблеми. Unexecuted remote/platform проверки се јасно означени и се планираат пред release тврдење.
