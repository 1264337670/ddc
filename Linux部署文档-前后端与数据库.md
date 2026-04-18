# 心屿项目 Linux 部署文档（前后端 + 数据库）

本文档给出一套可直接落地的部署方案，重点覆盖：

1. 数据库使用 Docker 拉取 MySQL 镜像并持久化。
2. 后端 FastAPI 在 Linux 服务器长期运行，具备日志输出与自动拉起能力。
3. 前端 Vue 打包后由 Nginx 提供静态服务。

## 1. 部署目标与建议版本

1. 操作系统：Ubuntu 22.04 LTS（Debian 系同理）
2. Docker：24+
3. Python：3.10 或 3.11
4. Node.js：20+
5. Nginx：1.20+

## 2. 服务器目录规划

建议统一使用如下目录（可按实际调整）：

```bash
/opt/mind-island/
  backend/        # 后端代码
  frontend/       # 前端代码（含 dczzq）
  logs/           # 后端日志
  mysql-data/     # MySQL 数据卷
  mysql-conf/     # MySQL 自定义配置
```

创建目录：

```bash
sudo mkdir -p /opt/mind-island/{backend,frontend,logs,mysql-data,mysql-conf}
sudo chown -R $USER:$USER /opt/mind-island
```

## 3. 数据库部署（Docker MySQL）

### 3.1 拉取镜像并启动容器

```bash
docker pull mysql:8.0

docker run -d \
  --name mind-island-mysql \
  --restart unless-stopped \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD='12345' \
  -e TZ='Asia/Shanghai' \
  -v /opt/mind-island/mysql-data:/var/lib/mysql \
  mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci
```

### 3.2 初始化数据库结构

把项目中的 [database_schema.sql](database_schema.sql) 上传到服务器后执行：

```bash
docker exec -i mind-island-mysql mysql -uroot -p'请替换为强密码' < /opt/mind-island/database_schema.sql
```

### 3.3 验证数据库状态

```bash
docker ps | grep mind-island-mysql
docker logs --tail 100 mind-island-mysql
```

## 4. 后端部署（FastAPI 长期运行 + 日志）

## 4.1 上传代码并创建虚拟环境

假设后端代码目录是 /opt/mind-island/backend：

```bash
cd /opt/mind-island/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 4.2 配置后端环境变量

在后端目录准备 .env（示例）：

```env
APP_NAME=Mind Island API
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=False

DATABASE_URL=mysql+pymysql://root:请替换为强密码@127.0.0.1:3306/mind_island?charset=utf8mb4

JWT_SECRET_KEY=请替换为高强度密钥
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=120

CORS_ORIGINS=http://你的前端域名:3000,https://你的前端域名

SILICONFLOW_API_KEY=你的Key
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=THUDM/GLM-4-9B-0414
```

字段名可参考 [backend/app/core/config.py](backend/app/core/config.py)。

## 4.3 使用 systemd 常驻运行（推荐）

创建服务文件：

```bash
sudo nano /etc/systemd/system/mind-island-backend.service
```

写入以下内容：

```ini
[Unit]
Description=Mind Island FastAPI Service
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/mind-island/backend
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/mind-island/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=5
StandardOutput=append:/opt/mind-island/logs/backend.out.log
StandardError=append:/opt/mind-island/logs/backend.err.log

[Install]
WantedBy=multi-user.target
```

说明：

1. 使用 StandardOutput 和 StandardError 持久化日志到文件。
2. Restart=always 保证异常退出后自动拉起。
3. User 可按实际代码目录权限改为你的部署账号。

启动并设置开机自启：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mind-island-backend
sudo systemctl status mind-island-backend
```

查看日志：

```bash
tail -f /opt/mind-island/logs/backend.out.log
tail -f /opt/mind-island/logs/backend.err.log
journalctl -u mind-island-backend -f
```

## 5. 前端部署（Vite 打包 + Nginx）

## 5.1 安装依赖并打包

假设前端目录为 /opt/mind-island/frontend/dczzq：

```bash
cd /opt/mind-island/frontend/dczzq
npm install
npm run build
```

## 5.2 配置前端 API 地址

生产环境建议在 .env.production 指向后端外网地址：

```env
VITE_API_BASE_URL=https://api.your-domain.com
```

## 5.3 Nginx 托管静态文件

将 dist 拷贝到 Nginx 站点目录：

```bash
sudo mkdir -p /var/www/mind-island
sudo cp -r /opt/mind-island/frontend/dczzq/dist/* /var/www/mind-island/
```

Nginx 配置示例：

```nginx
server {
    listen 3000;
    server_name _;

    root /var/www/mind-island;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /avatar-files/ {
        proxy_pass http://127.0.0.1:8000/avatar-files/;
    }
}
```

重载 Nginx：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 6. 部署后联调检查清单

1. 数据库容器运行正常，能连接 mind_island。
2. 后端 systemd 服务状态为 active (running)。
3. 后端日志持续写入 /opt/mind-island/logs。
4. 前端页面可打开，登录、资料、树洞、导师、分析接口返回正常。
5. 管理端可进入 [dczzq/src/pages/AdminView.vue](dczzq/src/pages/AdminView.vue) 对应功能并完成操作。

## 7. 常见问题排查

1. 后端启动失败：先看 /opt/mind-island/logs/backend.err.log，再看 journalctl。
2. 数据库连接失败：检查 DATABASE_URL 密码、端口映射、容器状态。
3. 前端接口 404/跨域：检查 VITE_API_BASE_URL 与后端 CORS_ORIGINS。
4. 刷新 404：确认 Nginx 使用 try_files ... /index.html。

## 8. 升级发布建议

1. 先备份数据库：

```bash
docker exec mind-island-mysql mysqldump -uroot -p'请替换为强密码' mind_island > /opt/mind-island/backup_$(date +%F_%H%M%S).sql
```

2. 先更新后端代码并重启服务，再更新前端静态文件。
3. 升级后执行冒烟：登录、树洞发帖、导师预约、管理审核。