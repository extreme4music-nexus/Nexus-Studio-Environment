# Квалитет, ризици и услови за испорака

## Што проверуваме и кога

| Област | Проверка | Почеток / gate |
|---|---|---|
| Contracts/runtime | Верзии, зависности, lifecycle, failure/cleanup, public boundaries | P1; пред затворање WP-001. |
| Workspace/data | Open/save/reopen, migration, conflict, source preservation и restore | P2; пред вистински проекти. |
| NeuraFS | Standalone baseline, adapter mapping и засегнати регресии | P3; пред реален adapter release. |
| Nexus | Project isolation, source-aware memory, tool validation, нема лажен успех | P4; пред intelligence milestone. |
| Audio | Познати fixtures, единици, sample/timebase, unsupported/corrupt input | P5; пред продукциски материјал. |
| Music | MIDI валидност, constraints, вистински preview, A/B и човечки избор | P6; пред music alpha. |
| DAW | Capability detection, revision mismatch, ограничени дејства и потврден исход | P7; пред write integration. |
| Cross-platform | Исти contracts/action traces, UI flow, screenshots, keyboard/focus, DPI/fonts и accessibility | Smoke од P1; UI prototype P2; цел supported-flow gate пред beta/release. |
| Reliability | NAS offline, permission/disk failure, прекин, restart, partial output и cancellation | Како се воведува секоја IO граница; повторно пред release. |
| Distribution | Fresh install, configuration, upgrade/migration, rollback и uninstall | P10; по платформа. |

## Мерки без измислени резултати

CPU/GPU/RAM, model latency, UI responsiveness, render time, cancellation и storage throughput се мерат на документиран hardware/OS со познат test set. По pilot се поставуваат прифатливи прагови со корисникот. За визуелен паритет се фиксираат viewport, DPI, fonts и locale и се договараат допустливи rendering разлики; 100% идентичност не се тврди од Windows-only тест.

Музичката вредност се оценува со слушање и авторски избор. Техничката валидност, усогласеноста со brief и личната преференција се различни оценки. Не ги заменуваме со една самододелена confidence бројка.

## Главни ризици и одговор

| Ризик | Одговор / контролна точка |
|---|---|
| Системот станува framework без корисничка вредност | Мал WP-001; потоа workspace и еден реален музички тек. |
| Nexus само зборува за музика, без реални резултати | ToolResult/artifact validation и render gate; јасно разделени факти/проценки/предлози. |
| Моделот е слаб/скап за корисничкиот hardware | Заменлив ModelPort, pilot мерења, ограничен context и explicit budgets. |
| NeuraFS гранките дивергираат | Авторитативна ревизија, read-only audit, посебни fixes и без автоматски merge. |
| NAS губи врска или backend нема потребни guarantees | Проверен storage contract, local temporary data каде што е соодветно, conflict/recovery tests и чесен unavailable статус. |
| Промени во туѓ проект/DAW состојба | Resource scopes, revision checks, нови артефакти/тест копии и проверен rollback каде што постои. |
| Различни UI/OS можности | Shared UI/state, platform adapters, capability profile и исти видливи fallback правила. |
| Музички преференции стануваат крути правила | Project scope, correction/delete и разграничување „оваа песна“ од „општа преференција“. |
| Непроверени models/plugins/license terms | Проверка на конкретен кандидат пред интеграција; одделна белешка за weights, code и излезна употреба. |
| Документацијата се разминува со кодот | Еден master checklist, активен пакет и session log по секој завршен пакет. |

## Release gate

- Договорениот опфат е запишан; условните/одложените features се означени.
- Секое завршено тврдење има testcase, демонстрација или друг соодветен доказ.
- Поддржаните OS/DAW/model/NeuraFS верзии се наведени и проверени.
- Нема нерешени критични data loss, permissions, lifecycle или лажно-success проблеми.
- Backup/restore и migration/rollback тековите се проверени на тест копии.
- Packages се инсталирани во чисти околини; uninstall не брише кориснички проекти.
- Secrets и приватни reference payloads не се во Git/release artifacts; logs/support bundle се соодветно ограничени.
- Познатите ограничувања и корисничкото упатство се достапни.
- Корисничката acceptance сесија го потврдува реалниот договорен резултат.

## Следење по пакет

Статус: предложено/договорено/во тек/блокирано/завршено/одложено. Секој запис има ID, цел, предуслови, acceptance, точна ревизија и докази. Блокада се запишува со причина, засегнат опфат и следен чекор. Не се прогласува завршена цела фаза по еден поминат unit тест.
