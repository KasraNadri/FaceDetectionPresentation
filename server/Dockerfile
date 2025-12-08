FROM reg.daneshrefah.ir/modernization/python:3.9.0-slim-pytorch

WORKDIR /app
COPY . .

EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]