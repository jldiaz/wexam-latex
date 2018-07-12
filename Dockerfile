FROM python:3.6

RUN apt-get update && apt-get install -y \
       pandoc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Instalar dependencias del proyecto examtool
RUN pip install -e .

EXPOSE 5000

# Lanza un worker
CMD [ "./docker-entrypoint.sh" ]

