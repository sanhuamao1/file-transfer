# Codelink · 文件中转站

带密码保护的临时文件分享工具，支持本地存储和阿里云 OSS。

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

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ACCESS_CODE` | `123456` | 页面访问密码 |
| `OSS_ENABLED` | `false` | 设为 `true` 启用阿里云 OSS |
| `OSS_ACCESS_KEY_ID` | — | OSS AccessKey ID |
| `OSS_ACCESS_KEY_SECRET` | — | OSS AccessKey Secret |
| `OSS_BUCKET_NAME` | — | OSS Bucket 名称 |
| `OSS_ENDPOINT` | — | OSS 地域节点（如 `https://oss-cn-beijing.aliyuncs.com`） |

> `ACCESS_CODE`、`UPLOAD_DIR`、`DB_PATH`、`MAX_SIZE` 也可通过 `docker-compose.yml` 的 `environment` 或 `app.py` 中的环境变量覆盖。
