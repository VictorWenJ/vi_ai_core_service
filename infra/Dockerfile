FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

# 先安装依赖，利用 Docker 层缓存提升重复构建速度。
COPY requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r /workspace/requirements.txt

# 复制业务代码；infra 文件由 compose 管理，不进入业务包。
COPY app /workspace/app

EXPOSE 8000

# 使用项目正式 HTTP 入口启动服务。
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
