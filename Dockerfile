FROM python:3

RUN apt-get update && apt-get upgrade && apt-get -y install git htop nano && apt-get autoremove
RUN git clone https://github.com/szafranski-pawel/dns-manager.git /app

WORKDIR /app
RUN pip3 install .
RUN pip3 install gunicorn

EXPOSE 8000

CMD ["python3", "-m" , "gunicorn", "--bind", "0.0.0.0:8000", "-w", "2", "dns_manager:create_app()"]
# CMD ["tail", "-f", "/dev/null"]
