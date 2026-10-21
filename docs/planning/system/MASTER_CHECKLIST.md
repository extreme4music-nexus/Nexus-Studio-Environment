# Главна чек-листа

Ова е единствениот оперативен системски список. Стариот BACKLOG е историски/модулски контекст; неговите ставки се врзуваат за ID подолу кога ќе станат активни. [x] значи завршен наведен резултат со доказ, а не општо одобрение на цела архитектура. За секоја активна задача се додава owner, точна ревизија, verification evidence и ограничувања во session log/пакетот.

## PLAN — Основа и голема слика

- [x] PLAN-01: Нов проект и приватен Git репозиториум — docs/SETUP_REPORT.md, почетна ревизија f536a7b.
- [x] PLAN-02: Изолирани Nexus/NeuraFS референци и provenance — локални manifests и setup report.
- [x] PLAN-03: Статичка Nexus анализа и селекција — modules/nexus_core/docs/LEGACY_REVIEW.md.
- [x] PLAN-04: Системски план, архитектура, каталог, фази и прв пакет се документирани — овој директориум. Завршува по документарната проверка на овој пакет.
- [x] PLAN-05: Кориснички преглед на големата слика и забележани корекции/приоритети.

## FRAME — Заеднички костур, WP-001

- [x] FRAME-01: Module descriptors, contract version и lifecycle/error/health модели.
- [x] FRAME-02: Registry со експлицитни регистрации и duplicate проверки.
- [x] FRAME-03: Missing dependency, cycle и version compatibility проверки.
- [x] FRAME-04: Dependency injection/composition root без туѓи implementation imports.
- [x] FRAME-05: Initialize/start по ред; stop/cleanup по обратен ред; partial failure semantics.
- [x] FRAME-06: Конфигурација и CLI diagnostics со вистински статуси.
- [x] FRAME-07: Два означени fake модули со проверлив service повик.
- [x] FRAME-08: Success/failure/lifecycle тестови и legacy exclusion проверки.
- [x] FRAME-09: Windows smoke; CI evidence за Windows/Linux/macOS или експлицитно непроверено.
- [x] FRAME-10: Runtime документација, module authoring пример и затворен пакет со докази.

## WORK/UI — Проекти и работна средина

- [ ] WORK-01: Project/asset/session/decision шеми, IDs и versioning.
- [ ] WORK-02: Metadata backend ADR, atomicity/concurrency и локална/NAS граница.
- [ ] WORK-03: Create/open/save/reopen и conflict detection без overwrites.
- [ ] WORK-04: Assets/revisions/derived artifacts и provenance.
- [ ] WORK-05: Backup/export/recovery правило за project metadata.
- [ ] UI-01: UI toolkit prototype и Windows/Linux/macOS compatibility evidence.
- [ ] UI-02: Заеднички design tokens, bundled fonts, navigation и state model.
- [ ] UI-03: Project browser/workspace и module diagnostics преку SDK.
- [ ] UI-04: Conversation/jobs/preview shell со чесни loading/error/cancel состојби.

## NFS — Проверена интеграција со NeuraFS

- [ ] NFS-01: Read-only capabilities/API/SDK/CLI попис и нов Git статус.
- [ ] NFS-02: Договорен авторитативен branch/commit; divergence од main документирана без автоматски merge.
- [ ] NFS-03: Познати багови репродуцирани и одвоени од интеграцискиот опфат.
- [ ] NFS-04: Standalone baseline на тест податоци.
- [ ] NFS-05: StoragePort adapter само за навистина поддржаните операции.
- [ ] NFS-06: Missing service/timeout/permission/error mapping и договорени retries.
- [ ] NFS-07: Потребни поправки на посебна работна гранка, регресиска проверка и верзионирана интеграција.

## CORE — Nexus мозок

- [ ] CORE-01: ModelPort, provider selection ADR, hardware и cost/latency мерења.
- [ ] CORE-02: Реален provider и чесно однесување при недостапност.
- [ ] CORE-03: Session/context со budget и project isolation.
- [ ] CORE-04: MemoryPort со извори, одлуки, корекција, бришење и migration проверки.
- [ ] CORE-05: Structured plan/tool proposal, runtime validation и дозволи.
- [ ] CORE-06: Observe/act/verify loop со реален ToolResult, cancellation и ограничен retry.
- [ ] CORE-07: Нема измислени мерења/артефакти; неподдржаната способност е експлицитна.
- [ ] CORE-08: Повторно отворање сесија ја задржува прифатената проектна одлука и не меша друг проект.

## AUDIO — Вистинска перцепција и preview

- [ ] AUDIO-01: Избрани input формати, decode/validation и недопрени оригинали.
- [ ] AUDIO-02: Measurements со единици, алгоритам/верзија и познати fixtures.
- [ ] AUDIO-03: Tempo/key/structure проценки означени со ограничувања и user override каде што се воведени.
- [ ] AUDIO-04: Background jobs со cancel/error/recovery без блокирање на UI.
- [ ] AUDIO-05: Playback/render contract и валиден вистински preview.
- [ ] AUDIO-06: Content references, timebase и source-to-output provenance.

## MUSIC — Ко-компонирање и ко-продукција

- [ ] MUSIC-01: Договорена прва корисничка задача, brief и тест материјал.
- [ ] MUSIC-02: MIDI/music data model, tempo map, meter и ограничувања.
- [ ] MUSIC-03: Две смислено различни варијанти со опис што е сменето.
- [ ] MUSIC-04: Уредлив артефакт + вистински render преку избран renderer.
- [ ] MUSIC-05: A/B споредба со соодветно ниво/playback услови; не се прогласува погласно за подобро автоматски.
- [ ] MUSIC-06: Избор/одбивање и причина со project scope; нема глобално правило од еден избор.
- [ ] MUSIC-07: Цел alpha тек: open → context → анализирај → предложи → preview → избери → save → reopen.

## DAW/EXT — Интеграција и подоцнежни способности

- [ ] DAW-01: Избран DAW/верзија и проверена официјална API површина.
- [ ] DAW-02: Read-only project snapshot и capability detection.
- [ ] DAW-03: Ограничено дејство врз тест копија, revision check и verification.
- [ ] DAW-04: Undo/rollback каде што постои; експлицитни ограничувања каде што не постои.
- [ ] EXT-01: Приоритети за следна музичка способност според употреба, не според број модули.
- [ ] EXT-02: Ако се избере audio генератор: capability/licence/hardware/data-use проверка и control evaluation.
- [ ] EXT-03: Ако се избере live input: посебен real-time bridge, latency budget и callback isolation.
- [ ] EXT-04: Ако се избере проактивност: bounded jobs, quiet mode и проверливи корисни triggers.

## QA/REL — Квалитет, паритет и испорака

- [ ] QA-01: Договорена compatibility матрица и CI проверки по пакет.
- [ ] QA-02: Функционален/визуелен паритет, DPI/fonts/keyboard/accessibility на поддржаните текови.
- [ ] QA-03: NAS offline, диск/permission грешки, partial write, crash/restart и project conflict проверки.
- [ ] QA-04: Backup/restore и schema migration со зачувани project assets.
- [ ] QA-05: Credentials/permissions/audio egress/log redaction и зависности/лиценци.
- [ ] QA-06: Измерени performance цели и cancellation/resource cleanup; нема измислен SLA.
- [ ] QA-07: Standalone NeuraFS regression gate за неговите засегнати промени.
- [ ] REL-01: Versioned packages, fresh install/uninstall и upgrade/rollback по платформа.
- [ ] REL-02: Корисничко упатство, познати ограничувања, release notes и diagnostics export без secrets.
- [ ] REL-03: Корисничка acceptance сесија за договорениот release опфат и означено издание.

Условните EXT задачи не се задолжителни за првото издание ако останат надвор од договорениот опфат. Тогаш се означуваат „одложено/не е во изданието“, не „завршено“.

## WP001-LOCAL-EVIDENCE — 2026-10-21

PLAN-05 е потврден со корисничкото „Ајде започни. Ми се допаѓа“. FRAME-01–08 и FRAME-10 се имплементирани и проверени локално: 24 тестови, offline wheel build/install и изолирано demo. FRAME-09 е делумно: Windows е проверен, CI matrix е конфигурирана, Linux/macOS remote резултати сè уште не се потврдени. Докази: [runtime verification](../../runtime/VERIFICATION.md).

## WP001-CLOSED-20261021

Сите FRAME-01–10 се завршени. Windows/Linux/macOS install, tests, validate и demo се потврдени во [CI evidence](../../runtime/VERIFICATION.md) за кодната ревизија 905f520. Претходната белешка дека FRAME-09 чека CI е историска; CI сега е помината.
