# Каталог на модули и одговорности

Постојните осум scaffold области се основа. Следните логички области не се тврдење дека веќе имаат имплементација или посебен сервис. Нови пакети се создаваат кога нивната фаза ќе започне.

| Област | Постојна/предложена локација | Влез → излез | Што поседува / што не прави |
|---|---|---|---|
| Contracts | modules/nse_contracts | Типизирани DTO, ports, errors, descriptors | Јавни договори. Не увезува runtime, UI, модели или OS implementations. |
| Runtime | Предлог: modules/nse_runtime | Конфигурација и registrations → активни services/status | Composition, dependency graph, lifecycle, diagnostics. Не прави музички одлуки. |
| Workspace | Предлог: modules/nse_workspace | Project команди → manifest/revisions/assets/decisions | Авторитативна проектна metadata состојба. Не е нов DAW или storage engine. |
| Nexus Core | modules/nse_nexus_core | Намера + контекст + tool results → одговор/план/предлог | Session orchestration, retrieval policy и verification. Не чита туѓи DB internals и не самододелува дозволи. |
| Memory repository | Прво Workspace service зад MemoryPort | Изворни факти/одлуки → релевантни scoped записи | Перзистенција на одлуки со provenance, корекција и бришење. Посебен пакет само ако има оправдана потреба. |
| NeuraFS adapter | modules/nse_neurafs | StoragePort → потврдени NeuraFS операции | Преведување и errors/capabilities. Постoјниот NeuraFS останува независен репозиториум/производ. |
| Audio services | Предлог: modules/nse_audio | Audio references + параметри → анализи/playback/render | Decode/validation, DSP measurements, jobs и preview. Не прогласува вкус за физички факт. |
| Music services | Предлог: modules/nse_music | Brief + music context → MIDI/музички кандидати | Notes/rhythm/harmony/constraints. Rendering користи Audio/RenderPort; не измислува готово аудио. |
| API | modules/nse_api | Надворешно request → validated service command/result | Transport, auth каде што е потребна, schema/error mapping. Без деловни правила дуплирани од core. |
| SDK | modules/nse_sdk | UI/client операции → API/service договор | Стабилна клиентска граница и serialization. Без директно увезување core implementations. |
| Connectors | modules/nse_connectors | Provider/DAW payloads ↔ општи contracts | AI provider adapters, DAW и други оправдани integrations. Секој има capability profile и failure mapping. |
| Studio UI | modules/nse_studio_ui | Кориснички дејства → commands; state → екрани | Заеднички design system, navigation, project browser, разговор, jobs, preview и settings. Без business policy во widget callbacks. |
| Platform adapters | modules/nse_platform_adapters | Општи OS requests → normalized резултати | Paths, processes, credentials, уреди/notifications според потреба. Без OS-specific копии на цели екрани. |

## Заеднички правила

- Self-contained модул значи јасна граница, зависности и тестирање; не значи дека секој мора да работи како standalone executable.
- NeuraFS standalone однесувањето е посебно потврдено барање и се зачувува.
- API, SDK и connector имаат различни улоги; не се три имиња за ист слој.
- Composition root смее да ги поврзува имплементациите. Другите модули зависат од ports, а не од внатрешни пакети на соседот.
- Пробен модул секогаш е означен како fake/demo. Неговиот успешен резултат докажува wiring, не storage, model или музичка способност.
- Нема circular imports, auto-execution од legacy или generic import на доверливост непроверени extensions.

## Задолжителен модулски документ кога модулот се активира

README.md; ARCHITECTURE.md; public contract/capabilities; lifecycle/dependencies; configuration/credentials; errors; verification и limitations. Изворите на API и верзиите се запишуваат кај конкретниот connector, без да се препишува целата документација во master планот.

## Планирани кориснички површини

Project browser → Project workspace → Nexus conversation → Assets/versions → Job status → MIDI/audio preview → Module/settings diagnostics. Ова е информациска структура, не конечен визуелен дизајн. Timeline во првата верзија е преглед на материјал/секции, а не ветување за целосен multitrack sequencer.
