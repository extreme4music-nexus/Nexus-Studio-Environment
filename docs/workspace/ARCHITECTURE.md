# Workspace архитектура

`nse_contracts.workspace` е јавниот contract. `nse_workspace` има DTO use cases, JSON repository и lifecycle модул. Единствениот concrete import од Runtime е во composition root: `compose_workspace(root)` враќа Runtime и стабилен WorkspacePort-compatible service reference. Constructor не создава metadata. Initialize ја подготвува папката; service повици се дозволени само додека модулот работи. Референцата може да се вбризга во dependency initialize, пред start.

## Податоци

Project има UUID-hex ID, name, creative brief, позитивна revision, UTC timestamps и schema_version=1. Sessions, Decisions и AssetReferences се immutable DTOs во tuples; IDs и project-local links се валидираат. Decision има source и status, а не автоматска ознака „вистина“. Asset provenance мора да има постоечки извори и да нема cycle. Проектите се изолирани; session од друг проект не е дозволена decision врска.

## Фајлови

```text
metadata-root/
  <project-uuid>/
    HEAD.json
    r00000001-<unique-suffix>.json
    r00000002-<unique-suffix>.json
    .write.lock  (само за време на write, или stale по crash)
```

Snapshot е immutable JSON envelope со project и parent pointer. HEAD упатува на filename/revision/SHA-256. Parent chain определува committed history; glob редоследот на датотеки никогаш не определува што е последно. Snapshot limit е 8 MiB; HEAD е ограничен на 64 KiB. JSON со duplicate keys се одбива. Непозната schema верзија не се downgrade-ира. Checksum открива случајна корупција, не е потпис или authentication механизам.

## Write протокол

Exclusive create на project lock → проверка на current HEAD/snapshot → compare со expected revision → write нов уникатен snapshot, flush/fsync → write temporary HEAD sibling, flush/fsync → same-directory replace на HEAD → ослободување само на сопствениот lock. Snapshot или temporary-head failure пред replace не ја менува претходната HEAD. Ако IO грешка се јави откако replace можеби веќе завршил, исходот е неизвесен: отвори го проектот пред повторен write, не retry слепо.

Ова е cooperating single-writer-per-project протокол, не distributed database. Не спречува надворешна програма рачно да менува metadata. Filesystem exclusive-create/replace guarantees мора да бидат проверени за конкретната storage локација. Не е дадена општа NAS power-loss durability гаранција. Архитектонската одлука е во [ADR 0002](../adr/0002-workspace-metadata.md).

## Грешки и lifecycle

Invalid input → invalid_data; missing project → not_found; stale revision → revision_conflict; existing lock или locked initial commit без HEAD → workspace_busy; checksum/missing committed data/invalid schema structure → corrupt_metadata; понова schema → unsupported_schema; filesystem exception → workspace_io_error. Не се враќа празен проект како fallback.

Runtime health проверува дека модулот работи и root е папка; не тврди дека секој проект е здрав или секој write ќе успее. Runtime.stop ја затвора јавната service граница; директниот WorkspaceService останува одделна библиотечна употреба. Синхроните операции немаат distributed cancellation или concurrent Runtime lifecycle гаранција.

## Одложено

UI, SDK transport, file import/copy, byte hashing на материјали, automatic lock recovery, automatic pruning, asset media migration, NeuraFS, model memory semantics и повеќе writers без serialization се надвор од овој пакет. Future schema upgrade бара посебен migration пакет и fixtures.
