"""Single-use lifecycle: validate, initialize, start, stop, dispose."""
from uuid import uuid4
from nse_contracts.modules import (
    ErrorCode, ModuleContext, ModuleError, ModuleHealth, ModuleState, RuntimeIssue,
)
from .registry import ModuleRegistry, dependency_order


class Runtime:
    def __init__(self, registry: ModuleRegistry):
        self._entries = registry.snapshot()
        self.correlation_id = uuid4().hex
        self._states = {name: ModuleState.REGISTERED for name in self._entries}
        self._issues: dict[str, list[RuntimeIssue]] = {name: [] for name in self._entries}
        self._initialized: list[str] = []
        self._started: list[str] = []
        self._status = 'new'

    def validate(self) -> tuple[str, ...]:
        return dependency_order(self._entries, self.correlation_id)

    def _issue(self, name: str, phase: str, code: ErrorCode, exc: BaseException) -> RuntimeIssue:
        # Raw exception messages may contain credentials or private paths.
        issue = RuntimeIssue(code, name, phase, f'{name}: {phase} failed ({type(exc).__name__})')
        self._issues[name].append(issue)
        self._states[name] = ModuleState.FAILED
        return issue

    def start(self) -> None:
        if self._status == 'running':
            return
        if self._status != 'new':
            raise ModuleError((RuntimeIssue(
                ErrorCode.INVALID_STATE, None, 'start',
                'A stopped or failed runtime cannot restart; create fresh module instances',
            ),), self.correlation_id)
        order = self.validate()  # No lifecycle side effects on validation failure.
        phase = 'initialize'
        try:
            for name in order:
                entry = self._entries[name]
                context = ModuleContext(self.correlation_id, {
                    dep: self._entries[dep].module.service for dep in entry.descriptor.dependencies
                })
                # Include the failing initializer: it may have acquired resources.
                self._initialized.append(name)
                entry.module.initialize(context)
                self._states[name] = ModuleState.INITIALIZED
            phase = 'start'
            for name in order:
                self._started.append(name)  # A failed start may be partial.
                self._entries[name].module.start()
                self._states[name] = ModuleState.RUNNING
        except BaseException as exc:
            code = ErrorCode.INITIALIZE_FAILED if phase == 'initialize' else ErrorCode.START_FAILED
            primary = self._issue(name, phase, code, exc)
            cleanup = self._cleanup()
            self._status = 'failed'
            if not isinstance(exc, Exception):
                raise
            raise ModuleError((primary, *cleanup), self.correlation_id) from exc
        self._status = 'running'

    def _cleanup(self) -> tuple[RuntimeIssue, ...]:
        issues = []
        for name in reversed(self._started):
            try:
                self._entries[name].module.stop()
                if not self._issues[name]:
                    self._states[name] = ModuleState.STOPPED
            except BaseException as exc:
                issues.append(self._issue(name, 'stop', ErrorCode.STOP_FAILED, exc))
        self._started.clear()
        for name in reversed(self._initialized):
            try:
                self._entries[name].module.dispose()
                if not self._issues[name]:
                    self._states[name] = ModuleState.DISPOSED
            except BaseException as exc:
                issues.append(self._issue(name, 'dispose', ErrorCode.DISPOSE_FAILED, exc))
        self._initialized.clear()
        return tuple(issues)

    def stop(self) -> None:
        if self._status in ('new', 'stopped', 'failed'):
            return
        issues = self._cleanup()
        self._status = 'failed' if issues else 'stopped'
        if issues:
            raise ModuleError(issues, self.correlation_id)

    def health(self) -> tuple[ModuleHealth, ...]:
        snapshots = []
        for name, entry in sorted(self._entries.items()):
            issues = list(self._issues[name])
            healthy = False
            if self._states[name] == ModuleState.RUNNING:
                try:
                    healthy = entry.module.health() is True
                except Exception as exc:
                    issues.append(RuntimeIssue(
                        ErrorCode.HEALTH_FAILED, name, 'health',
                        f'{name}: health failed ({type(exc).__name__})',
                    ))
            snapshots.append(ModuleHealth(entry.descriptor, self._states[name], healthy,
                                          self.correlation_id, tuple(issues)))
        return tuple(snapshots)
