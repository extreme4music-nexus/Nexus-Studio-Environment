# Backup и recovery на метаподатоци

## Backup

Export содржи тековен Project DTO, backup_version=1 и SHA-256 на canonical project metadata. Нема целосна revision history, audio/MIDI bytes, credentials или model caches. Asset locations остануваат референци; корисникот мора посебно да ги зачува материјалите. Backup е point-in-time snapshot, не continuous backup сервис.

## Restore

- Во нова metadata root: истиот project_id и project creation identity, сите вклучени session/decision/asset metadata; локалната revision започнува од 1.
- Во постоен здрав проект: експлицитна current revision и совпаѓачка creation identity; backup содржината станува нова revision, со зачуван parent chain.
- Corrupt checksum, несоодветна шема или stale revision не се препокриваат автоматски.
- За corrupt HEAD/историја во стар root: зачувај ја локацијата недопрена, провери надворешен backup и restore во нов root. Пакетот нема команда што наслепо ја „поправа“ HEAD или избира најнов snapshot по filename.

## Прекинат write

Orphan snapshot што не е врзан од HEAD/parent chain не е committed history и не се отвора автоматски. Постоечкиот committed проект останува читлив ако HEAD и неговиот snapshot се здрави. Cleanup на orphan revisions не е автоматизиран во WP-002.

## Stale lock

Readers може да читаат веќе committed HEAD додека writer работи. Writers добиваат workspace_busy ако lock постои. Ако crash оставил lock, Runtime рестарт не го брише. Не преземај force unlock само по PID или време: друг компјутер/процес може сè уште да пишува. Прво запреј ги сите writers и направи копија за дијагноза; потоа одделна договорена recovery интервенција. Нема auto-unlock алатка во овој пакет.

## Проверки на нова storage локација

Пушти metadata smoke на празна тест локација, провери simultaneous writer conflict, reboot/reconnect однесување и server/share гаранции пред production употреба. Успешен smoke на една NAS share не е доказ за сите mounts, client OS или power-loss случаи.
