# Workspace — проекти и континуитет

WP-002 е вистинска metadata функционалност, приклучена на Runtime. Нема UI, audio processing, model provider или NeuraFS adapter во овој пакет.

## Команди

По инсталација на проектот (`python -m pip install -e .`), користи `nexus-workspace` или `python -m nse_runtime.workspace_cli`:

```text
nexus-workspace --root <metadata-folder> create --name "Мој проект" --brief "Зачувај го groove-от"
nexus-workspace --root <metadata-folder> list
nexus-workspace --root <metadata-folder> show <project-id>
nexus-workspace --root <metadata-folder> update <project-id> --revision 1 --name "Ново име"
nexus-workspace --root <metadata-folder> session <project-id> --revision 2 --title "Сесија 1"
nexus-workspace --root <metadata-folder> decision <project-id> --revision 3 --text "Задржи мотив A" --source "кориснички избор"
nexus-workspace --root <metadata-folder> history <project-id>
nexus-workspace --root <metadata-folder> backup <project-id> --output <new-backup-file>
nexus-workspace --root <new-metadata-folder> restore --input <backup-file>
```

Заменувај ги ID/revision вредностите со актуелните од претходниот JSON резултат. Секое успешно зачувување ја зголемува ревизијата. Restore врз постоен проект бара `--revision <current>` и создава нова ревизија, без бришење историја. Backup не препокрива постоечки output фајл. Командите бараат експлицитна metadata локација, нема вградена Z: патека.

JSON резултатите содржат project/session/decision IDs, creative brief, timestamps и revision. Exit=0 значи успех, 1 значи структурирана Workspace/runtime грешка, а 2 значи CLI/data/IO грешка. Stale revision враќа `revision_conflict`, а lock враќа `workspace_busy`; отвори ја актуелната состојба пред нов обид и не бриши lock на активен writer.

## Безбедно демо

`python -B examples/workspace-smoke.py` користи сопствени привремени папки и проверува create/session/decision/reopen/conflict/backup/restore. `--parent <existing-folder>` ја сместува таа привремена проверка под избрана локација, на пример NAS тест папка. Демо податоците се отстрануваат по проверката; не се користат стари проекти или аудио снимки.

## Што се зачувува

Project metadata; сесии и summaries; одлуки со source/status/session link; asset references со declared hash и derived-from врски. Не се читаат или копираат media bytes. Declared hash е metadata, не тврдење дека Workspace го измерил материјалот.

Види [архитектура](ARCHITECTURE.md), [recovery](RECOVERY.md) и [проверки](VERIFICATION.md).
