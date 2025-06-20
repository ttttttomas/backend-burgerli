FROM python

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev build-essential pkg-config

WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]