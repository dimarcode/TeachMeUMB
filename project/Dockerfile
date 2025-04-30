FROM python:slim

WORKDIR /app

COPY requirements.txt .
COPY boot.sh .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn
RUN chmod a+x boot.sh

COPY . .

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]