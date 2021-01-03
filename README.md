# kuzya volume slider

Микшер звуков windows через python + websockets + windows core audio, сделанный на HTML

## demo

[![Watch the video](https://img.youtube.com/vi/3AZCA7A8h_g/maxresdefault.jpg)](https://youtu.be/3AZCA7A8h_g)

## релиз

см страницу [релизов на гитхабе](https://github.com/ColCh/Kuzya-volume-slider/releases)

## установка для разработки

в зависимостях есть `pywin32` и `pycaw` - могут быть проблемы с тем, чтобы установить модули на mac

для окружения используется pipenv (`pip install -U pipenv`).

войти в окружение можно через команду `pipenv shell` в директории проекта

установить зависимости можно через `pipenv install`

## сборка exe

делается через pyinstaller.

для сборки, надо через pip удалить enum34:

`pip uninstall enum34`

и запустить `build.bat`

## запуск собранного файла

можно запустить `run.bat` из проводника (после сборки)
