# Workspace boundary

Зависности: stdlib и `nse_contracts`. Другите business модули го користат WorkspacePort; concrete поврзувањето е во runtime composition root. Проектната метаподаточна состојба има еден авторитативен repository backend и верзионирани snapshots; Nexus нема да води паралелен project DB.

Деталите за схемата, write протоколот, lifecycle, грешките и storage ограничувањата се во [заедничката архитектура](../../docs/workspace/ARCHITECTURE.md) и [ADR 0002](../../docs/adr/0002-workspace-metadata.md).
