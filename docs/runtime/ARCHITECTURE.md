# Runtime архитектура

## Граници

`nse_contracts.modules` ги дефинира descriptor, lifecycle protocol, context, health и стабилните errors. `nse_runtime.registry` чува експлицитни registrations. `composition` избира познати factories и вбризгува зависности. `runtime` управува со lifecycle; `__main__` е diagnostics CLI. `demo` содржи само јасно означени fake компоненти.

Нема filesystem discovery, dynamic imports од конфигурација, HTTP listener или автоматско стартување legacy фајлови. Composition root е единствената дозволена граница за имплементациски imports од други NSE пакети; business модули користат contracts. Public descriptor е immutable; runtime зема registration snapshot и подоцнежни registry промени не му го менуваат графот.

## Validation

Пред lifecycle: duplicate IDs при регистрација; contract major точно 1; сите dependencies присутни; нема cycles, вклучувајќи self-cycle. Topological редоследот е deterministic со лексички tie-break. `module.version` е одделна ознака од `contract_major`; нема semver resolver.

## Lifecycle

Состојби на модул: registered → initialized → running → stopped → disposed. Failed се зачувува кога lifecycle/cleanup откажува. Достапноста на plugin на диск не е дел од овој enum. `healthy` е посебна моментална оценка, true само за running модул чиј health повик експлицитно враќа True. Health exception дава healthy=false и issue, без да го прескокне подоцнежниот cleanup.

Сите модули прво се initialize-ираат по dependency order, па сите се start-уваат по истиот ред. Initialize добива read-only mapping само на декларираните dependency services; dependency е иницијализирана, но не мора сè уште да е стартувана. Во initialize задржи референци и стекни свои ресурси; повици што бараат running сервис прави во start или подоцна.

При initialize/start неуспех, се прави stop во обратен ред на сите обидени starts, вклучувајќи делумно неуспешниот. Потоа dispose во обратен ред на сите обидени initializers, вклучувајќи го оној што делумно откажал. Другите initialize-ирани но нестартувани модули исто добиваат dispose. Неиницијализирани модули не добиваат cleanup.

Првата грешка е прва во ModuleError.issues; stop/dispose грешките се додаваат и не го прекинуваат остатокот од cleanup. Python exception cause се зачувува за локална дијагностика, додека јавните issues прикажуваат само exception type, не raw message со потенцијални credentials/патишта. KeyboardInterrupt/SystemExit при startup иницира cleanup и потоа повторно се подига.

Cleanup е best effort, не гаранција дека произволен модул ги ослободил ресурсите. Ако dispose откаже, failed состојбата останува видлива. Нема автоматски втор обид за cleanup; потребна е нова runtime инстанца и, ако останат надворешни ресурси, соодветна експлицитна интервенција.

## Повторени операции

- start на running runtime е no-op; нема двојно стекнување ресурси.
- stop пред start е no-op; start потоа е дозволен.
- stop по stop или startup failure е no-op; автоматски не повторува неуспешен cleanup.
- start по завршен stop или startup failure дава invalid_state; користи нови module instances.
- Validation failure нема lifecycle side effects и оставa runtime во new состојба, со непроменлив registration snapshot.

## Ограничувања

Runtime е за еден thread/control flow, без reentrant lifecycle повици. Нема isolation sandbox за plugin код, async jobs, network retry, hard timeout за блокиран third-party код или real-time гаранција. Factories/constructors мора да бидат без resource side effects; тие почнуваат во initialize. Овие граници се намерни за WP-001 и не се тврдат како идни готови способности.
