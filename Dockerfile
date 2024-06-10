# 使用官方 Python 镜像作为基础镜像
FROM python:3.11.3-slim

# 设置工作目录
WORKDIR /FreeChat

# 复制项目的依赖文件
COPY requirements.txt .

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露应用运行的端口
EXPOSE 8765

# 运行服务器
CMD ["python", "server.py"]

