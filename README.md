# Codelink · 文件中转站

带密码保护的文件分享工具，文件存储于阿里云 OSS。

## 目录

- [Docker 部署（推荐）](#docker-部署推荐)
- [本地开发](#本地开发)
- [配置说明](#配置说明)

---

## Docker 部署（推荐）

### 1. 拉取代码

```bash
git clone git@github.com:sanhuamao1/file-transfer.git
cd file-transfer/codelink
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，修改 ACCESS_CODE 和 OSS 配置（可选）
```

### 3. 启动

```bash
docker compose up -d
```

访问 `http://你的IP:5000`。

### 更新

```bash
git pull
docker compose up -d --build
```

---

## 本地开发

### 前置条件

- Python 3.11+
- pip

### 快速启动

```bash
chmod +x dev.sh
./dev.sh
```

脚本会自动创建虚拟环境、安装依赖、创建必要目录，然后启动开发服务器（默认 `http://localhost:5000`）。

### 手动启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p files data
cp .env.example .env   # 编辑 .env 修改 ACCESS_CODE
ACCESS_CODE=123456 python app.py
```

---

## 配置说明

| 变量 | 必填 | 说明 |
|------|------|------|
| `ACCESS_CODE` | 是 | 页面访问密码 |
| `OSS_ACCESS_KEY_ID` | 是 | OSS AccessKey ID |
| `OSS_ACCESS_KEY_SECRET` | 是 | OSS AccessKey Secret |
| `OSS_BUCKET_NAME` | 是 | OSS Bucket 名称 |
| `OSS_ENDPOINT` | 是 | OSS 地域节点（如 `https://oss-cn-beijing.aliyuncs.com`） |
