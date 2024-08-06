FROM python:3.9-slim

WORKDIR /app

COPY . /app

# Installing nodejs to be able to use bootstrap inside the container
RUN apt-get update && apt-get install -y nodejs npm
# Install bootstrap
RUN npm install bootstrap@5.3.3
# Install the python libraries
RUN pip install --no-cache-dir -r requirements.txt
# Install git
RUN apt-get update && apt-get install -y git

EXPOSE 5000

CMD ["python", "app/app.py"]
