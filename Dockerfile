FROM python:3-onbuild
EXPOSE 8080
ENV RUN_ON_RASPBERRY 0
CMD ["python3", "-m", "app.main"]
