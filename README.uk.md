# Кондиціонери HiSense

Це форк [deiger/AirCon](https://github.com/deiger/AirCon), у якому MQTT-міст замінено на
нативний сервер [ESPHome] API (через [aioesphomeserver]) — кондиціонер(и) з'являються в
інтеграції ESPHome Home Assistant напряму: без брокера, з push-оновленнями стану та
автоперепідключенням, яке вже реалізоване в тому самому клієнті, яким HA користується для всіх
інших ESPHome-пристроїв. Деталі — у розділі [Інтеграція з ESPHome](#інтеграція-з-esphome) нижче.

Ця програма реалізує LAN API Ayla Networks для взаємодії з модулем Wi-Fi кондиціонера HiSense
моделей AEH-W4B1 та AEH-W4E1, а також Fujitsu FGLair.

Як зазначено [тут](../../issues/1), програма, схоже, не підходить для модуля AEH-W4A1, який
використовує зовсім інший протокол (реалізований додатками [Hi-Smart Life](https://play.google.com/store/apps/details?id=com.qd.android.livehome), [AirConnect](https://play.google.com/store/apps/details?id=com.oem.android.airconnect), [Smart Cool](https://play.google.com/store/apps/details?id=com.oem.android.livehome), [AC WIFI](https://play.google.com/store/apps/details?id=com.oem.android.ecold) та [טורנדו WiFi](https://play.google.com/store/apps/details?id=com.oem.android.tornadowifi)). Дайте знати, якщо у вас інший досвід або ви пробували з іншими модулями.

Цей модуль встановлюється в кондиціонери та зволожувачі, які виробляють або лише брендують під
своєю маркою багато інших компаній, зокрема Beko, Westinghouse, Winia, Tornado, York та інші.

**Ця програма не пов'язана з Ayla Networks, HiSense, Fujitsu, жодною з їхніх дочірніх компаній чи реселерів.**

## Передумови

1. Кондиціонер із встановленим модулем HiSense AEH-W4B1 або AEH-W4E1, або Fujitsu FGLair.
1. Встановлений Python 3.14 або новіший (потрібен для залежності ESPHome-сервера). Якщо
   використовуєте Raspberry Pi — візьміть свіжу версію Raspberry Pi OS, що вже має його, або
   скористайтесь методом через Docker нижче.
1. Налаштуйте кондиціонер(и) через відповідний фірмовий додаток. Посилання на кожен додаток — у
   таблиці нижче. Увійдіть у додаток, прив'яжіть кожен кондиціонер і підключіть його до мережі,
   як описано в документації додатка.
1. Після налаштування кондиціонер(и) можна заблокувати від виходу в інтернет, оскільки він більше
   не потрібен. Призначте їм статичні IP-адреси на роутері та запишіть їх.
   * Примітка: _щоб уникнути потреби в ручних змінах пізніше, переконайтесь, що додаток знає про
     нові IP-адреси до відключення кондиціонерів від інтернету._
1. Знайдіть код свого додатка в списку нижче:

   | Код        | Назва додатка       | Посилання
   |------------|---------------------|---------|
   | beko-eu    | Beko?               | |
   | haxxair    | HAXXAIR WIFI REMOTE | [![](https://lh3.googleusercontent.com/-9FX7-sYlE2xDwG9uymjPejV-P8nI_hQ9zN7QDu6OgyYILbjdg5o38nQTvAmFTPyiw=s50-rw)](https://play.google.com/store/apps/details?id=com.aylanetworks.accontrol.haxxair) |
   | denali-us  | Denali Aire         | [![](https://lh3.googleusercontent.com/8NYl3eNN7M_cXmvo4ywj9al5794Ci_dzGYxYZopHd96Z4yr1M12e8xzk9mkz5cMELQ=s50-rw)](https://play.google.com/store/apps/details?id=com.smart.internationalus.denaliaire) |
   | fglair-eu  | FGLair              | [![](https://lh3.googleusercontent.com/LcrpWfFdRi3GriCV3MqPhkKsxV-IkwFHxZHHDugC__iaO1HE-7UyKuQj-bEWyggo8DFP=s50-rw)](https://play.google.com/store/apps/details?id=com.fujitsu.fglair) |
   | field-us   | HiSmart Air         | [![](https://lh3.googleusercontent.com/9p4SUOklfccVzJdrbhHZW8MlmioF-YgfLWOQBtad2N_A5AWtcyNv7X-M3QT1e2Fdam00=s50-rw)](https://play.google.com/store/apps/details?id=com.aylanetworks.accontrol.hisense) |
   | hisense-eu | HiSmart Life        | [![](https://lh3.googleusercontent.com/AbCPfEScNDwgsKozku6jmItFPVq9WJCl30jZKlSDFDAtlAiC3WRZZ4MlWEEWR8ZxKA=s50-rw)](https://play.google.com/store/apps/details?id=com.hisense.hismartinternationalforandroid) |
   | hisense-us | HiSmart Home        | [![](https://lh3.googleusercontent.com/Qs9UJVhczWYk-ij7UiRWoCDi2pYIoOUYuU5pBwOKQSD_07KHyAnLGg-myF7U9a387w=s50-rw)](https://play.google.com/store/apps/details?id=com.hisense.hismartinternationalus) |
   | hismart-eu | Smart-Living        | [![](https://lh3.googleusercontent.com/k9p0RMiW_xax5FIU5tpwSZav1In7tu6szGQopRWhSyRd2dIr0_L0IWHPVLSHxbrWrA=s50-rw)](https://play.google.com/store/apps/details?id=com.smart.international2) |
   | hismart-us | AI-Home             | [![](https://lh3.googleusercontent.com/eUJicIOk50rP391IFs0Xw6306adghQuiQtaLgUkxImuP6bAdHvQjS1gbIKY75Bd2mkA=s50-rw)](https://play.google.com/store/apps/details?id=com.smart.internationalus) |
   | huihe-us   | SunHome             | [![](https://lh3.googleusercontent.com/3tI6Nbx4ZlphD_b5O7bW3XcMEKnFkViOKMS9-cL9K9OQVyGJRjRmKu67JU8_t_w93iZs=s50-rw)](https://play.google.com/store/apps/details?id=com.sunvalley.sunhome) |
   | mid-eu     | WiFi AC             | [![](https://lh3.googleusercontent.com/LWmnlcSnT2hYmdwB2vq5SoBuaawkS8eu0F6n9Tytowrftp7kflmUXRAt_uWg7C0Fgspn=s50-rw)](https://play.google.com/store/apps/details?id=com.accontrol.mid.europe.hisense) |
   | mid-us     | Smiling Air         | [![](https://lh3.googleusercontent.com/op7-cqkm6N3JinyViCONKKgIVeMWI4BGO4TP3atRheGKG_vzsufh1PmEa-v9b8OAEPI=s50-rw)](https://play.google.com/store/apps/details?id=com.accontrol.mid.america.hisense) |
   | oem-eu     | Hi-Smart AC         | [![](https://lh3.googleusercontent.com/-HdiS1L18OjviXxGY68fvuBO3I4J1XGEEPOIc0f8p268f0ZJYkADHVvOgzH2wttsBwnk=s50-rw)](https://play.google.com/store/apps/details?id=com.accontrol.europe.hisense) |
   | oem-us     | Hisense?            | |
   | tornado-us | &#x2067;טורנדו WIFI גרסה 2&#x2069; | [![](https://lh3.googleusercontent.com/M9kU7oYeZTU8hVLChdJQL4giJacgUT2yFw-pqNk8JR4kbqbvl9x8dT88BC0admZrrQ=s50-rw)](https://play.google.com/store/apps/details?id=com.accontrol.tornado.america.hisense) |
   | winia-us   | 위니아 에어컨 홈스마트        | [![](https://lh3.googleusercontent.com/IGIkHlnLbFxTFGOk_aql3sVGgL9DLOtc3Ti_oDhQLUT8_-8PGmXjVBcQnmgqWxitB_U=s50-rw)](https://play.google.com/store/apps/details?id=com.accontrol.winia.america.hisense) |
   | wwh-us     | Westinghouse?       | |
   | york-us    | YORK Smart          | [![](https://lh3.googleusercontent.com/udf-qe7lXPJ5d7pi96WC8ex20-DuzAvAfyYX1i9B0zyvKjj0TLqoWwZmju-M5y0dQwE=s50-rw)](https://play.google.com/store/apps/details?id=com.accontrol.york.america.hisense) |

## Запуск сервера керування кондиціонером як додатка Home Assistant

Якщо ви користуєтесь [Home Assistant], це кращий спосіб.

1. У веб-інтерфейсі Home Assistant перейдіть у **Supervisor → Add-on Store**.
1. Натисніть **⋮ меню → Repositories**.
1. Додайте `https://github.com/vetalkordyak/AirCon` до списку.
1. Виберіть **HiSense Air Conditioner** та встановіть.
1. Налаштуйте конфігурацію, як описано всередині додатка.
1. Запустіть додаток. Не забудьте увімкнути **Start on boot** і **Watchdog**.

## Запуск сервера керування кондиціонером у Docker

Використовуйте цей спосіб, якщо не користуєтесь Home Assistant, або хочете налаштувати сервер
окремо від нього.

1. Завантажте [`docker-compose.yaml`](docker-compose.yaml) і [`options.json`](options.json).
   Оновіть відповідні поля в `options.json`:
   - Для кожного додатка (підтримується декілька) вкажіть `username` і `password` — облікові
     дані для входу в додаток, та `code` — код додатка зі списку вище.
     Вони використовуються для пошуку ваших кондиціонерів і отримання LAN-ключів, якщо у
     теці конфігурації (`/opt/hisense`) ще немає файлів конфігурації.
   - Встановіть `esphome_port` (за замовчуванням `6053`) та `esphome_web_port` (за замовчуванням
     `6052`), якщо потрібно їх змінити, або встановіть `esphome_port` в `0`, щоб повністю
     вимкнути ESPHome-сервер.
   - За бажанням вкажіть `esphome_name`, щоб перевизначити назву, під якою анонсується
     віртуальний ESPHome-пристрій (за замовчуванням — назва першого кондиціонера).
   - За бажанням вкажіть `esphome_advertise_ip`, якщо Home Assistant не може достукатись до
     реальної LAN-адреси цього сервера напряму (наприклад, HA працює на Docker macvlan-мережі,
     а цей сервер — на host/bridge мережі) — див.
     [Інтеграція з ESPHome](#інтеграція-з-esphome) нижче.
   - Встановіть `port` — порт, який використовуватиме веб-сервер.
   - Встановіть `log_level` — бажаний рівень деталізації логів.

1. Запустіть:
   ```bash
   docker-compose up -d
   ```
1. Перевірте логи й переконайтесь, що все гаразд:
   ```bash
   journalctl CONTAINER_NAME=hisense_ac
   ```

1. Готово! Додайте пристрій у Home Assistant через **Налаштування → Пристрої та служби → Додати
   інтеграцію → ESPHome**, вказавши IP-адресу сервера та `esphome_port` (докладніше — у розділі
   [Інтеграція з ESPHome](#інтеграція-з-esphome) нижче).
   Для [SmartThings] потрібне ручне налаштування через
   [groovy-файл](devicetypes/deiger/hisense-air-conditioner.src/hisense-air-conditioner.groovy), див. нижче.

## Запуск сервера керування кондиціонером вручну

Використовуйте цей спосіб, якщо налаштування через Docker вище не спрацювало.

1. Завантажте та встановіть модуль aircon:
   ```bash
   python3.14 -m pip install .
   ```

1. Запустіть команду виявлення пристроїв, щоб отримати LAN-ключі, потрібні для підключення до
   кондиціонера. Передайте їй свої облікові дані та код додатка зі списку вище:

   Наприклад:
   ```bash
   python3.14 -m aircon discovery tornado-us foo@example.com my_pass
   ```
   CLI згенерує файл конфігурації для кожного кондиціонера — його потрібно передати серверу
   керування кондиціонером нижче. Ви можете вибрати кондиціонер, для якого генерується
   конфігурація, за допомогою прапорця `--device` із назвою пристрою, як налаштовано в додатку.

* Примітка: _щоб оновити сервер до останньої версії, виконайте `git pull` в репозиторії та
  повторно встановіть. Можливо, знадобиться також повторно запустити виявлення._

1. Перевірте, що сервер запускається, наприклад:
   ```bash
   python3.14 -m aircon run --port 8888 --config config.json
   ```
   Параметри:
   - `--port` або `-p` — порт веб-сервера.
   - `--config` — файл конфігурації з обліковими даними для підключення до кондиціонера.
   - `--esphome_port` — порт нативного API ESPHome. За замовчуванням 6053. Встановіть 0, щоб
     вимкнути.
   - `--esphome_web_port` — порт веб-панелі налагодження ESPHome. За замовчуванням 6052.
   - `--esphome_name` — назва, під якою анонсується віртуальний ESPHome-пристрій. За замовчуванням
     — назва першого налаштованого кондиціонера.
   - `--log_level` — мінімальний рівень логування, що надсилається в syslog. За замовчуванням
     WARNING.
   - `--local_ip` — локальна IP-адреса, яку сервер повідомляє кондиціонеру(ам) як цільову.
     Корисно, якщо сервер має декілька IP-адрес (наприклад, у різних VLAN), оскільки деякі (чи
     більшість?) кондиціонерів відмовляються повідомляти на адресу поза своєю підмережею.
1. Доступ, наприклад, через curl:
   ```bash
   curl -ik 'http://localhost:8888/hisense/status'
   curl -ik 'http://localhost:8888/hisense/command?property=t_power&value=ON'
   ```

### Декілька кондиціонерів
Щоб використовувати з кількома кондиціонерами, просто додайте декілька параметрів --config.
Кожен кондиціонер представлений як окрема сутність climate (з назвою, яку кондиціонер має в
додатку) в межах єдиного віртуального ESPHome-пристрою.

### Запуск як служби
Припускаючи, що ваш користувач — "pi"

1. Створіть окрему теку для файлів скрипта та перенесіть туди файли.
   Передайте право власності root, напр.:
   ```bash
   sudo mkdir /opt/hisense
   sudo mv config*.json /opt/hisense
   sudo chown pi:pi /opt/hisense/*
   ```
1. Створіть файл конфігурації служби (від імені root), напр. `/lib/systemd/system/hisense.service`:
   ```INI
   [Unit]
   Description=Hisense A/C server
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3.14 -m aircon run --port 8888 --config config.json
   WorkingDirectory=/opt/hisense
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   User=pi

   [Install]
   WantedBy=multi-user.target
   ```
1. Створіть символьне посилання на неї з `/etc/systemd/system/`:
   ```bash
   sudo ln -s /lib/systemd/system/hisense.service /etc/systemd/system/multi-user.target.wants/hisense.service
   ```
1. Увімкніть і запустіть нову службу:
   ```bash
   sudo systemctl enable hisense.service
   sudo systemctl start hisense.service
   ```
1. [Home Assistant] тепер має знайти кондиціонер(и) через свою інтеграцію ESPHome, див.
   [Інтеграція з ESPHome](#інтеграція-з-esphome) нижче.

## Доступні властивості

Нижче наведено властивості, доступні через API для стандартних кондиціонерів
(FGLair і зволожувачі мають інші властивості):

| Властивість      | Лише читання | Значення                               | Коментар                                                                 |
|------------------|:------------:|-----------------------------------------|--------------------------------------------------------------------------|
| f_electricity    | x            | Ціле число                             |                                                                          |
| f_e_arkgrille    | x            | 0, 1                                   | Тривога захисту решітки корпусу                                          |
| f_e_incoiltemp   | x            | 0, 1                                   | Несправність датчика температури внутрішнього змійовика                 |
| f_e_incom        | x            | 0, 1                                   | Несправність зв'язку між внутрішнім і зовнішнім блоками                 |
| f_e_indisplay    | x            | 0, 1                                   | Несправність зв'язку між панеллю керування і дисплеєм внутрішнього блока |
| f_e_ineeprom     | x            | 0, 1                                   | Помилка EEPROM панелі керування внутрішнього блока                      |
| f_e_inele        | x            | 0, 1                                   | Несправність зв'язку між панеллю керування і силовою платою внутрішнього блока |
| f_e_infanmotor   | x            | 0, 1                                   | Аномальна робота двигуна вентилятора внутрішнього блока                 |
| f_e_inhumidity   | x            | 0, 1                                   | Несправність датчика вологості внутрішнього блока                       |
| f_e_inkeys       | x            | 0, 1                                   | Несправність зв'язку між панеллю керування і клавіатурою                |
| f_e_inlow        | x            | 0, 1                                   |                                                                          |
| f_e_intemp       | x            | 0, 1                                   | Несправність датчика температури внутрішнього блока                     |
| f_e_invzero      | x            | 0, 1                                   | Несправність виявлення переходу напруги через нуль всередині блока      |
| f_e_outcoiltemp  | x            | 0, 1                                   | Несправність датчика температури зовнішнього змійовика                  |
| f_e_outeeprom    | x            | 0, 1                                   | Помилка EEPROM зовнішнього блока                                        |
| f_e_outgastemp   | x            | 0, 1                                   | Несправність датчика температури вихлопу                                |
| f_e_outmachine2  | x            | 0, 1                                   |                                                                          |
| f_e_outmachine   | x            | 0, 1                                   |                                                                          |
| f_e_outtemp      | x            | 0, 1                                   | Несправність датчика температури довкілля зовнішнього блока             |
| f_e_outtemplow   | x            | 0, 1                                   |                                                                          |
| f_e_push         | x            | 0, 1                                   | Несправність зв'язку між Wi-Fi панеллю і панеллю керування внутрішнього блока |
| f_filterclean    | x            | 0, 1                                   | Чи потребує фільтр очищення                                             |
| f_humidity       | x            | Ціле число                             | Відносна вологість у відсотках                                          |
| f_power_display  | x            | 0, 1                                   |                                                                          |
| f_temp_in        | x            | Дробове число                          | Температура довкілля у Фаренгейтах                                      |
| f_voltage        | x            | Ціле число                             |                                                                          |
| t_backlight      |              | ON, OFF                                | Увімкнення/вимкнення дисплея                                            |
| t_device_info    |              | 0, 1                                   |                                                                          |
| t_display_power  |              | 0, 1                                   |                                                                          |
| t_eco            |              | OFF, ON                                | Економний режим                                                         |
| t_fan_leftright  |              | OFF, ON                                | Горизонтальний потік повітря                                            |
| t_fan_mute       |              | OFF, ON                                | Тихий режим                                                             |
| t_fan_power      |              | OFF, ON                                | Вертикальний потік повітря                                              |
| t_fan_speed      |              | AUTO, LOWER, LOW, MEDIUM, HIGH, HIGHER | Швидкість вентилятора                                                    |
| t_ftkt_start     |              | Ціле число                             |                                                                          |
| t_power          |              | OFF, ON                                | Живлення                                                                |
| t_run_mode       |              | OFF, ON                                | Подвійна частота                                                        |
| t_setmulti_value |              | Ціле число                             |                                                                          |
| t_sleep          |              | STOP, ONE, TWO, THREE, FOUR            | Режим сну                                                               |
| t_temp           |              | Ціле число                             | Температура у Фаренгейтах                                               |
| t_temptype       |              | CELSIUS, FAHRENHEIT                    | Відображувана одиниця температури                                       |
| t_temp_eight     |              | OFF, ON                                | Режим "восьмиградусного" підігріву                                     |
| t_temp_heatcold  |              | OFF, ON                                | Швидке охолодження/нагрів                                               |
| t_work_mode      |              | FAN, HEAT, COOL, DRY, AUTO             | Робочий режим                                                           |

## Інтеграція з ESPHome

Замість MQTT-моста сервер представляє кожен кондиціонер як сутність `climate` через нативний
сервер API [ESPHome] (реалізовано за допомогою [aioesphomeserver]) — той самий протокол, яким
Home Assistant користується для спілкування зі справжніми ESPHome-пристроями.

- **Живлення / режим** (`t_power`, `t_work_mode`) відображаються у стандартні режими HVAC `off`
  / `fan_only` / `heat` / `cool` / `dry` / `auto`.
- **Цільова температура** (`t_temp`) і **поточна температура** (`f_temp_in`) відображаються у
  стандартні поля температури climate-сутності (конвертуються у Цельсій для пристроїв, що
  налаштовані на Фаренгейт, оскільки протокол ESPHome завжди працює у Цельсіях всередині).
- **Швидкість вентилятора** (`t_fan_speed`) представлена як *custom fan mode* з власними назвами
  швидкостей кондиціонера (`auto`, `lower`, `low`, `medium`, `high`, `higher`), а не втратно
  мапиться на фіксований набір режимів вентилятора ESPHome.
- Обдування (swing), вологість та інші менш поширені властивості (економний режим, режим сну
  тощо) поки що не представлені — тим часом користуйтесь безпосередньо
  [HTTP API](#запуск-сервера-керування-кондиціонером-вручну), або відкрийте issue/PR.

Щоб додати пристрій у Home Assistant: **Налаштування → Пристрої та служби → Додати інтеграцію →
ESPHome**, потім введіть IP-адресу сервера та `esphome_port` (за замовчуванням `6053`). Ключ
шифрування не потрібен — `aioesphomeserver` поки підтримує лише незашифрований (plaintext) API.

`aioesphomeserver` — сирий, alpha-якості проєкт, і його обробка з'єднань, як спостерігалось,
може "заклинити" після пакету одночасних перепідключень (наприклад, коли сам Home Assistant
перезапускається і всі відомі йому ESPHome-пристрої намагаються перепідключитись одночасно) —
процес лишається живим, порт відкритим, але нові клієнти не можуть пройти навіть початковий
handshake. `docker-compose.yaml` тут включає Docker `HEALTHCHECK`, який реально виконує цей
handshake, і sidecar-контейнер `autoheal`, що автоматично перезапускає `hisense_ac`, коли той
падає (політика рестарту самого Docker реагує лише на завершення процесу, а не на невдалий
healthcheck). На практиці цього вистачає для відновлення за ~30 секунд. Зверни увагу:
`autoheal` потребує доступу до Docker socket, що загалом дає контейнеру доволі широкий контроль
над іншими контейнерами хоста — прийнятно для домашньої установки, але варто про це знати, якщо
це працює десь у більш чутливому середовищі.

Якщо Home Assistant показує пристрій недоступним невдовзі після додавання (навіть якщо початкове
підключення спрацювало) — швидше за все, самоанонсування пристрою через Zeroconf/mDNS вказує
Home Assistant на адресу, до якої той насправді не може достукатись. Найчастіша причина: Home
Assistant працює в Docker-мережі macvlan (має власну LAN-адресу напряму), а цей сервер — з
`network_mode: host`, а контейнери в macvlan-мережі, як правило, не можуть достукатись до IP
самого Docker-хоста. Знайдіть адресу, до якої Home Assistant *може* достукатись до цього сервера
(наприклад, IP шлюзу тієї bridge-мережі, до якої також підключено Home Assistant), і вкажіть її
як `esphome_advertise_ip` в `options.json`, після чого видаліть і додайте інтеграцію в Home
Assistant заново.

Для SmartThings усе ще потрібне ручне налаштування через
[groovy-файл](devicetypes/deiger/hisense-air-conditioner.src/hisense-air-conditioner.groovy):
він знадобиться для інтеграції SmartThings з кондиціонером через описаний вище сервер керування.
Наразі він реалізує основну функціональність (увімкнення/вимкнення, режим кондиціонера,
швидкість вентилятора, димер тощо).

Groovy-файл доступний [тут](devicetypes/deiger/hisense-air-conditioner.src/hisense-air-conditioner.groovy) для завантаження та встановлення через [Groovy IDE](https://graph.api.smartthings.com). Оскільки скрипт постійно вдосконалюється, ефективніше користуватись github-інтеграцією IDE, щоб мати актуальну версію.

## Внесок у код
Pull request'и завжди вітаються.

Будь ласка, використовуйте [YAPF] з конфігурацією стилю, визначеною тут, для форматування коду.
У всій кодовій базі використовуються одинарні лапки. На жаль, YAPF поки не підтримує примусове
дотримання цього (підтримка є у [гілці fixers](https://github.com/google/yapf/tree/fixers)), тож,
будь ласка, майте це на увазі.

[Home Assistant]: https://www.home-assistant.io/
[ESPHome]: https://esphome.io/
[aioesphomeserver]: https://github.com/peterkeen/aioesphomeserver
[SmartThings]: https://www.smartthings.com/
[YAPF]: https://github.com/google/yapf

Read this document in English: [README.md](README.md).
