# 第一阶段：构建阶段
FROM python:3.11.3-alpine AS builder

# 安装构建依赖
RUN apk add --no-cache gcc musl-dev linux-headers

# 设置工作目录
WORKDIR /app

# 复制并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 第二阶段：运行阶段
FROM python:3.11.3-alpine

# 设置工作目录
WORKDIR /app

# 复制已安装的依赖
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制项目文件
COPY . .

# 暴露应用运行的端口
EXPOSE 8765

# 运行服务器
CMD ["python", "server.py"]

