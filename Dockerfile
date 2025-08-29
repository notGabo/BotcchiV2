FROM python:3.13.3

ENV PYTHONUNBUFFERED=1

WORKDIR /app
RUN git clone https://github.com/notGabo/BotcchiV2.git /app 
RUN pip install -r requeriments.txt
RUN apt-get update && apt-get install -y software-properties-common && apt-get install -y ffmpeg
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser
CMD ["python", "main.py"]