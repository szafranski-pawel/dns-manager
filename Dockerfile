FROM python:3

WORKDIR /app
COPY flask_app flask_app/
COPY setup.py .
COPY MANIFEST.in .
RUN pip3 install .
RUN pip3 install gunicorn

EXPOSE 8000

CMD ["python3", "-m" , "gunicorn", "--bind", "0.0.0.0:8000", "-w", "2", "flask_app:create_app()"]
# CMD ["tail", "-f", "/dev/null"]
