# WP-002 — Workspace и продолжување проекти

Датум: 2026-10-22. Имплементирано и проверено локално со 51 тест, NAS smoke и offline wheel install; remote CI чека потврда. Корисникот го одобри почетокот по завршениот костур. Почетна ревизија: 75f9a95083cea33520efbeae5eb14f3486e89e95. Опфат: WORK-01–05 за метаподатоци, без UI или вистински media storage.

## Редослед

1. Contracts за project/session/decision/asset-reference, schema version и грешки.
2. Backend одлука: immutable JSON revision записи и head pointer, без SQLite на непроверено network share.
3. Create/open/save/list со optimistic revision check и exclusive writer lock.
4. Сесии, одлуки и asset provenance со project isolation и валидирани врски.
5. History и metadata-only backup/restore; restore е експлицитна нова ревизија и не брише историја.
6. Workspace модул приклучен на Runtime преку јавен port и diagnostics CLI.
7. Failure/concurrency/schema/integrity/reopen тестови, isolated package smoke и CI на трите платформи.
8. Документација, чек-листа и Git синхронизација со точни докази.

## Прифаќање

- Проект со Unicode име, brief, сесија и одлука се отвора во нова service/runtime инстанца со истите податоци.
- Стара revision не препокрива понова. Два concurrent writers со иста base revision имаат еден успех и еден conflict/busy резултат.
- Неуспех пред промена на HEAD ја остава претходната committed состојба читлива. Orphan snapshot не станува автоматски тековен.
- Corrupt checksum/schema, missing project, lock и IO failure имаат видлив код; нема тивок reset на празен проект.
- Metadata backup може да се провери и врати во нов workspace; restore врз постоен проект бара очекувана актуелна ревизија.
- History ја следи само committed parent chain. Restore ја задржува историјата и создава нова ревизија.
- Asset references и derived links се валидираат; датотеките не се копираат, читаат или препокриваат.
- Старите проекти и legacy архивите се недопрени. Нема NeuraFS, модел, audio processing или UI тврдења.

## Ограничувања

Backend е за cooperating single-writer операции со exclusive lock и revision CAS. Поддршката на секој NAS зависи од неговите filesystem/SMB guarantees и бара сопствена проверка. Stale lock по crash не се отстранува автоматски; нема опасно „force unlock“ дејство. Schema v1 е прва верзија; понова непозната верзија се одбива, не се downgrade-ира. Backup содржи само метаподатоци, не аудио/MIDI bytes.

## Враќање

Пакетот е во нови contract/workspace/CLI области. Нема автоматска migration на постојни кориснички проекти. Проблематичен save не смее да ја смени HEAD пред новиот snapshot да е запишан и flush-нат. Завршувањето се означува само по тестови и evidence.
