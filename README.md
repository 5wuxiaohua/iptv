# Shanxi IPTV M3U Service

从 GitHub 定期获取山西移动 IPTV 直播源，将 TXT 格式转换为标准 M3U 文件，并通过 Nginx 提供 HTTP 访问。

项目使用 Docker Compose 部署，**Nginx 和 Python 更新程序运行在同一个容器中**。

---

# 1. 系统架构

整体流程：

```text
GitHub
  │
  │ HTTPS
  ▼
mobile.txt
  │
  ▼
Python Updater
  │
  │ TXT → M3U
  │ SHA256 检测变化
  │ os.replace() 原子替换
  ▼
/opt/iptv/data/shanxi_mobile.m3u
  │
  ▼
Nginx
  │
  │ HTTP :80
  ▼
Docker Port Mapping
  │
  │ Host :5678
  ▼
Internet
  │
  ▼
iPhone / APTV
```

Python updater：

- 容器启动时立即检查一次 GitHub 源文件。
- 每 24 小时重新检查一次。
- 使用 SHA256 判断源文件是否发生变化。
- 只有发生变化时才重新生成 M3U。
- 使用 `os.replace()` 原子替换 M3U。
- 下载或转换失败时保留上一次正常的 M3U。

Nginx：

- 只提供 `/shanxi_mobile.m3u`。
- 其他 URL 全部返回 `404`。
- 不提供目录浏览。
- 不提供上传接口。
- 不提供其他 HTTP API。

---

# 2. 项目目录

项目统一放在：

```text
/opt/iptv
```

目录结构：

```text
/opt/iptv/
├── README.md
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── iptv_updater.py
├── nginx/
│   └── default.conf
└── data/
    ├── shanxi_mobile.m3u
    └── shanxi_mobile.sha256
```

其中 `data/` 中的文件由程序自动生成。

# 5. Nginx 配置

文件：

```text
/opt/iptv/nginx/default.conf
```

内容：

```nginx
server {
    listen 80;
    server_name _;

    server_tokens off;

    location = /shanxi_mobile.m3u {

        alias /opt/iptv/data/shanxi_mobile.m3u;

        default_type application/vnd.apple.mpegurl;

        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";

        limit_except GET HEAD {
            deny all;
        }
    }

    location / {
        return 404;
    }
}
```

唯一允许访问的资源：

```text
/shanxi_mobile.m3u
```

例如：

```text
http://SERVER_IP:5678/shanxi_mobile.m3u
```

其他 URL：

```text
/
 /abc
 /test.txt
 /nginx.conf
```

全部返回：

```text
404 Not Found
```

---

# 6. entrypoint.sh

文件：

```text
/opt/iptv/entrypoint.sh
```

内容：

```sh
#!/bin/sh

set -e

echo "Starting IPTV updater..."

python3 -u /opt/iptv/iptv_updater.py &

echo "Starting nginx..."

exec nginx -g 'daemon off;'
```

赋予执行权限：

```bash
chmod +x /opt/iptv/entrypoint.sh
```

容器启动后同时运行：

```text
Python IPTV updater
        +
Nginx
```

其中 Nginx 作为容器前台进程运行。

---

# 7. IPTV 更新程序

文件：

```text
/opt/iptv/iptv_updater.py
```

数据源：

```text
https://raw.githubusercontent.com/xisohi/CHINA-IPTV/main/Unicast/shanxi/mobile.txt
```

输出文件：

```text
/opt/iptv/data/shanxi_mobile.m3u
```

HASH 文件：

```text
/opt/iptv/data/shanxi_mobile.sha256
```

检查周期：

```text
24 小时
```

工作流程：

```text
下载 mobile.txt
       │
       ▼
计算 SHA256
       │
       ├── 与上次相同
       │       │
       │       └── 不更新
       │
       └── 与上次不同
               │
               ▼
          TXT → M3U
               │
               ▼
     shanxi_mobile.m3u.tmp
               │
               │ fsync()
               ▼
           os.replace()
               │
               ▼
     shanxi_mobile.m3u
```

使用原子替换可以避免 Nginx 在文件更新过程中读取到半写入文件。

如果 GitHub 下载失败、TXT 格式异常或转换得到 0 个频道：

```text
不会覆盖原来的 M3U
```

---

# 13. HTTP 测试

服务器本地：

```bash
curl http://127.0.0.1:5678/shanxi_mobile.m3u
```

只看前几行：

```bash
curl -s \
    http://127.0.0.1:5678/shanxi_mobile.m3u \
    | head
```

应该看到：

```text
#EXTM3U
...
```

测试其他 URL：

```bash
curl -I http://127.0.0.1:5678/
```

应该：

```text
HTTP/1.1 404 Not Found
```

测试：

```bash
curl -I http://127.0.0.1:5678/test
```

同样应该：

```text
404 Not Found
```

---


# 20. 强制立即检查 IPTV

Updater 默认：

```text
启动时立即检查
       ↓
等待24小时
       ↓
再次检查
```

因此如果不想等 24 小时，最简单的方法是：

```bash
docker compose restart
```

容器重新启动后 Python updater 会立即执行一次检查。

也可以直接手动执行：

```bash
docker exec iptv \
    python3 /opt/iptv/iptv_updater.py
```

注意当前 Python 程序本身包含循环，因此这个命令不会执行一次后立即退出。

如果只是调试，推荐直接重启容器：

```bash
docker compose restart
```

---

# 21. 数据持久化

M3U 文件实际保存在 Host：

```text
/opt/iptv/data
```

因此：

```bash
docker compose down
```

甚至删除容器，都不会删除：

```text
shanxi_mobile.m3u
shanxi_mobile.sha256
```

重新：

```bash
docker compose up -d
```

即可继续使用。

---

# 22. 安全边界

当前服务使用：

```text
HTTP
```

而不是 HTTPS。

因此公网传输：

```text
iPhone
   │
   │ HTTP 明文
   ▼
Internet
   │
   ▼
Nginx
```

不具备 TLS 提供的：

- 传输加密
- 服务端身份认证
- 传输完整性保护

当前方案主要通过缩小 Nginx 暴露面降低服务端风险。

Nginx 只允许：

```text
GET /shanxi_mobile.m3u
HEAD /shanxi_mobile.m3u
```

没有：

```text
目录浏览
文件上传
管理接口
动态 Web 应用
Python HTTP Server
```

需要注意：

> 知道公网 IP 和端口的人仍然可以下载该 M3U 文件。

因此不要在 M3U 中保存账号、密码、Token 等敏感信息。

---

# 23. 最终运行关系

```text
                       Docker Host
                           │
                    TCP :5678
                           │
                           ▼
┌──────────────────────────────────────────┐
│              IPTV Container              │
│                                          │
│     ┌─────────────────────────────┐      │
│     │           Nginx             │      │
│     │           :80               │      │
│     └──────────────┬──────────────┘      │
│                    │                     │
│                    ▼                     │
│ /opt/iptv/data/shanxi_mobile.m3u         │
│                    ▲                     │
│                    │                     │
│     ┌──────────────┴──────────────┐      │
│     │      Python Updater         │      │
│     │                             │      │
│     │ 启动立即检查                 │      │
│     │ 每24小时检查                 │      │
│     │ SHA256变化检测               │      │
│     │ os.replace()原子更新         │      │
│     └──────────────┬──────────────┘      │
│                    │                     │
└────────────────────┼─────────────────────┘
                     │ HTTPS
                     ▼
                   GitHub
```

最终客户端访问地址：

```text
http://SERVER_PUBLIC_IP:5678/shanxi_mobile.m3u
```
