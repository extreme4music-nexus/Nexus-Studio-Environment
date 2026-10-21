# ADR 0002 — Верзионирани JSON метаподатоци за првиот Workspace

Датум: 2026-10-22. Избрано за одобрениот WP-002; ова не е универзален backend за сите идни случаи.

## Контекст и опции

Ни треба мал, зависност-free project backend што работи преку contract и може да се тестира локално и на конкретниот NAS. SQLite би дал трансакции локално, но network filesystem режимот бара посебна проценка; не го поставуваме автоматски на Z:. Самостоен database сервер е прерано за овој пакет. Прост mutable JSON фајл без ревизии/lock создава ризик од изгубени измени.

## Избор

Project directory именуван со UUID; immutable snapshot фајлови со project schema v1, parent pointer и checksum; мал HEAD pointer. Секој write зема exclusive lock, ја проверува current revision, запишува snapshot со flush/fsync и ја заменува HEAD од temporary sibling фајл. Snapshot имињата имаат уникатен suffix, па orphan од неуспешен write не се препокрива или меша со нов обид.

History следи само parent pointers од HEAD. Неизвршено или прекинато запишување не се прогласува за commit. Непознати schema верзии, corrupt snapshots и checksum несогласувања се одбиваат. Backup содржи проверен тековен snapshot; restore додава нова ревизија или создава експлицитно обновен проект во празна локација.

## Ограничувања и последици

Ова е cooperating-writer протокол, не distributed consensus или security sandbox. Се потпираме на filesystem exclusive create и same-directory replace; не ветуваме еднаква crash durability на секој NAS, disk/controller или mount. File fsync не е гаранција за секој network server/power-loss случај. Stale locks се пријавуваат, не се бришат автоматски. Не чуваме media bytes, credentials или model cache во project metadata. Нема автоматски schema migration од измислена v0.

Следна backend промена мора да го зачува WorkspacePort и да обезбеди посебно проверена migration. Оригиналните материјали остануваат недопрени.

## Примарни API извори

[Python 3.12 os.replace](https://docs.python.org/3.12/library/os.html#os.replace) и [os.fsync](https://docs.python.org/3.12/library/os.html#os.fsync) ги опишуваат примитивите; тие не се доказ за конкретна NAS конфигурација. Нашите резултати се запишуваат одделно во Workspace verification.
