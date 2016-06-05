# PythonServer

The simple TCP and UDP Python server


Простой TCP и UDP сервер на питоне.
TCP сервер - это простой многопоточный файловый сервер.
Нужен для приема и передачи файлов, с примитивными командами аля:
- создать временный файл и записать входящие данные в него;
- переименовать файл созданый ранее;
- послать файл клиенту.

UDP сервер - тут все сложнее. Он создаёт, удаляет комнаты. Держит список пользователей каждой комнаты, рассылает сообщения по комнатам.
В отличии от TCP сервера, он работает в одном потоке, потому собственно используется UDP.

Для всего этого добра есть клиент написанный на C#.
Фишки:
- прием и передача сообщений;
- создание и удаление комнат;
- подключение к комнатам;
- прием и передача файлов.


P.S. Надеюсь все это комуто пригодиться.