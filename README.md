# Codelink · 文件中转站

带密码保护的文件分享工具，支持文件存储于阿里云 OSS 或本地文件系统。

## 目录

- [快速开始（Windows 本地开发）](#快速开始windows-本地开发)
- [Docker 部署（推荐用于生产）](#docker-部署推荐用于生产)
- [配置说明](#配置说明)
- [项目结构](#项目结构)

---

## 快速开始（Windows 本地开发）

### 前置条件

- Python 3.10+
- pip

### 一键启动

```bat
dev.bat
```

脚本会自动：
1. 从 `.env.example` 生成 `.env`（若不存在）
2. 创建 Python 虚拟环境（`venv/`）
3. 安装依赖
4. 创建 `data/` 和 `storage/` 目录
5. 启动开发服务器（默认 `http://localhost:5000`）

### 手动启动

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
REM 编辑 .env 修改 ACCESS_CODE 和存储模式
python app.py
```

---

## Docker 部署（推荐用于生产）

### 1. 拉取代码

```bash
git clone git@github.com:sanhuamao1/file-transfer.git
cd file-transfer/codelink
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，修改 ACCESS_CODE，设置 STORAGE_BACKEND=oss 并填写 OSS 配置
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

## 配置说明

项目通过 `.env` 文件或环境变量加载配置。

| 变量 | 必填 | 说明 |
|------|------|------|
| `ACCESS_CODE` | 是 | 页面访问密码 |
| `STORAGE_BACKEND` | 否 | 存储模式：`local`（本地）或 `oss`（阿里云 OSS，默认） |
| `LOCAL_STORAGE_PATH` | 否 | 本地存储路径，默认 `./storage`（仅 local 模式） |
| `OSS_ACCESS_KEY_ID` | 依赖 | OSS AccessKey ID（仅 oss 模式必填） |
| `OSS_ACCESS_KEY_SECRET` | 依赖 | OSS AccessKey Secret（仅 oss 模式必填） |
| `OSS_BUCKET_NAME` | 依赖 | OSS Bucket 名称（仅 oss 模式必填） |
| `OSS_ENDPOINT` | 依赖 | OSS 地域节点，如 `https://oss-cn-beijing.aliyuncs.com`（仅 oss 模式必填） |

### 存储模式说明

- **`local` 模式**：文件存储在本地 `./storage/` 目录，适合开发或个人使用，无需任何云服务配置
- **`oss` 模式**：文件存储在阿里云 OSS，适合生产环境多实例部署，需填写 OSS 凭据

---

## 项目结构

```
codelink/
├── app.py                 # Flask 应用主入口
├── storage/               # 存储后端模块
│   ├── __init__.py        # 工厂：根据 STORAGE_BACKEND 返回对应实例
│   ├── base.py            # 抽象基类
│   ├── oss.py             # 阿里云 OSS 实现
│   └── local.py           # 本地文件系统实现
├── static/
│   └── style.css
├── templates/
│   └── index.html
├── .env.example           # 环境变量模板
├── requirements.txt
├── dev.bat                # Windows 开发启动脚本
└── Dockerfile
```

---

## 开发说明

### 从 OSS 切换到本地存储

编辑 `.env`，设置：

```
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./storage
```

无需配置任何 OSS 凭据即可运行。

### 从本地切换到 OSS

编辑 `.env`，设置：

```
STORAGE_BACKEND=oss
OSS_ACCESS_KEY_ID=your-key-id
OSS_ACCESS_KEY_SECRET=your-key-secret
OSS_BUCKET_NAME=my-bucket
OSS_ENDPOINT=https://oss-cn-beijing.aliyuncs.com