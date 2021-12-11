![Foodgram](https://github.com/I-Iub/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

## Оглавление
- [Описание](#description)
- [Установка с помощью GitHub](#setup_with_github)
- [Установка с помощью Dockerhub](#setup_with_dockerhub)
- [Команда для добавления данных в базу](#command)
- [Ссылка на сервис в интернете](#link)

<a id=description></a>
## Описание
Foodgram - проект, выполненый с использованием библиотеки [Django REST Framework](https://www.django-rest-framework.org/) фреймворка [Django](https://www.djangoproject.com/). Проект позволяет пользователям публиковать рецепты блюд, просматривать рецепты других пользователей, подписываться на других пользователей, добавлять рецепты в список избранных и список покупок, скачивать файл со списком покупок. На главной странице можно фильтровать рецепты по тегам, есть пагинация. Фронтенд -- одностраничное приложение на базе React. Обмен информацией между фронтендом и бэкэндом происходит посредством интерфейса API.
Автор бэкенда - https://github.com/I-Iub. Ревьюер проекта - Михаил Иванов. Благодаря ему код стал на столько идеальным, насколько он может быть идеальным при таком криворуком авторе. :smile: Автор фронтенда - Яндекс.Практикум.

---
<a id=setup_with_github></a>
## Установка с помощью GitHub
Установите Docker, если он не установлен. Инструкция по установке, например, на Ubuntu по этой [ссылке](https://docs.docker.com/engine/install/ubuntu/).
Все нижеследующие инструкции выполняйте в консоли. Если не вносить изменения в соответствующие файлы, то проект будет доступен на локальном хосте 127.0.0.1.
Первым делом необходимо клонировать проект с github.com. В консоли выполните:
```
https://github.com/I-Iub/foodgram-project-react.git
```
Перейдите в папку проекта "foodgram-project-react/infra" (в ней находится файл docker-compose). В корневой папке необходимо создать файл ".env". Содержание файла должно быть таким:
```
SECRET_KEY=***                              # <--ваш SECRET_KEY
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=***                       # <--ваш пароль
DB_HOST=db
DB_PORT=5432
```
Последующие команды скорее всего потребуется вводить команды от имени администратора, т.е. перед каждой командой нужно писать "sudo".
Запустите создание образов и развертывание контейнеров:
```
docker-compose up
```
В консоли можно будет увидеть, что создано и запущено три контейнера: "infra_web_1", "infra_nginx_1", "infra_db_1". Если всё прошло успешно, в используемом терминале нельзя будет вводить команды, можно только просматривать логи. Откройте новый терминал, перейдите в папку "foodgram-project-react/infra". Последовательно выполните команды:
 - создания миграций
```
docker-compose exec infra_web python manage.py makemigrations
```
 - применения миграций
```
docker-compose exec infra_web python manage.py migrate --noinput
```
 - создания суперпользователя
После этой команды потребуется ввести имя пользователя, адрес электронной почты и пароль.
```
docker-compose exec infra_web python manage.py createsuperuser
```
 - сбора статики
```
docker-compose exec web python manage.py collectstatic --no-input
```
Приложение готово к работе.
Для того, чтобы остановить контейнеры, необходимо выполнить:
```
docker-compose down
```
---
<a id=setup_with_dockerhub></a>
## Установка с помощью Dockerhub
Данная инструкция описывает как развернуть проект на примере сервера. И применима для установки на других машинах, которые не обязательно являются сервером. Чтобы этот способ сработал на машине, на которой разварачивается проект, должен быть установлен Docker. Инструкция по установке Docker, например, на сервере с операционной системой Ubuntu по этой [ссылке](https://docs.docker.com/engine/install/ubuntu/).
Для того, чтобы развернуть проект используя образ, сохраненный на DockerHub необходимо скачать на сервер файлы "docker-compose.yaml" и папку с файлом "nginx.conf". Эти файлы находятся в папке foodgram-project-react/infra [репозитория](https://github.com/I-Iub/foodgram-project-react) на GitHub. Указанные файл и папку необходимо поместить в одной директории на сервере. Запистите терминал, перейдите в папку с этими файлами. Выполните команду:
```
sudo docker-compose up
```
В консоли можно будет увидеть, что создано и запущено три контейнера: "infra_web_1", "infra_nginx_1", "infra_db_1". Если всё прошло успешно, в используемом терминале нельзя будет вводить команды, можно только просматривать логи. Откройте новый терминал, снова перейдите в папку c файлами "docker-compose.yaml" и "nginx.conf". Последовательно выполните команды:
 - создания миграций
```
docker-compose exec infra_web python manage.py makemigrations
```
 - применения миграций
```
docker-compose exec infra_web python manage.py migrate --noinput
```
 - создания суперпользователя
После этой команды потребуется ввести имя пользователя, адрес электронной почты и пароль.
```
docker-compose exec infra_web python manage.py createsuperuser
```
 - сбора статики
```
docker-compose exec infra_web python manage.py collectstatic --no-input
```
Приложение готово к работе.
Для того, чтобы остановить контейнеры, необходимо выполнить:
```
docker-compose down
```
---
<a id=command></a>
## Команда для добавления данных в базу
Для переноса ингредиентов из файлов формата .csv в базу данных в консоли введите команду:
```
python manage.py load_ingredients
```
При этом в папке foodgram-project-react/backend/foodgram/data/ должен быть файл ingredients.csv.

---
<a id=link></a>
## Ссылка на сервис в интернете
Адрес развернутого проекта в интернете: [http://www.eduserver.xyz/recipes/](http://www.eduserver.xyz/recipes/).
