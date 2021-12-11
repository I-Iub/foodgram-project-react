FROM python:3.8-slim
WORKDIR /code

COPY backend/foodgram/requirements.txt .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . .

CMD gunicorn foodgram/foodgram.wsgi:application --bind 0.0.0.0:8000
