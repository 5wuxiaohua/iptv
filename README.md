# IPTV M3U Updater

定期从 GitHub 获取山西移动和北京移动 IPTV 直播源，将 TXT 转换为 M3U，并保存到项目的 `data/` 目录。
容器仅运行 Python 更新程序，不运行 Nginx，也不监听 HTTP 端口。

## 数据源与输出

| 地区 | TXT 数据源 | M3U 输出 | SHA256 文件 |
| --- | --- | --- | --- |
| 山西移动 | [mobile.txt](https://raw.githubusercontent.com/xisohi/CHINA-IPTV/main/Unicast/shanxi/mobile.txt) | `data/shanxi_mobile.m3u` | `data/shanxi_mobile.sha256` |
| 北京移动 | [mobile.txt](https://raw.githubusercontent.com/xisohi/CHINA-IPTV/main/Unicast/beijing/mobile.txt) | `data/beijing_mobile.m3u` | `data/beijing_mobile.sha256` |

## 启动

在项目目录执行：

```bash
docker compose up -d --build
```

从旧版升级也使用上述命令，以重建镜像和容器，移除原来的 Nginx 和端口映射。
代码复制在镜像中，修改代码后需要重新执行该命令。

查看更新日志：

```bash
docker compose logs -f iptv
```

立即重新检查所有源：

```bash
docker compose restart iptv
```

停止服务：

```bash
docker compose down
```

`data/` 通过相对路径挂载到容器的 `/opt/iptv/data`，停止或删除容器不会删除生成的文件。
M3U 文件可交给播放器或其他文件服务使用。

## 更新流程

- 容器启动后立即依次检查山西、北京两个源，每轮完成后等待 24 小时。
- 每个地区独立计算和保存 SHA256；源内容未变化且 M3U 存在时跳过写入。
- 识别 `分组名,#genre#` 和 `频道名,URL`，保留分组与多个播放地址。
- 通过临时文件、`fsync()` 和 `os.replace()` 原子替换每个输出文件。
- M3U 成功写入后才更新对应 SHA256 文件。
- 下载失败、转换失败或频道数为零时保留该地区的原文件，继续处理其他地区。
- 不检测直播地址的可播放性，不代理视频流。

## 项目结构

```text
.
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── iptv_updater.py
└── data/
    ├── shanxi_mobile.m3u
    ├── shanxi_mobile.sha256
    ├── beijing_mobile.m3u
    └── beijing_mobile.sha256
```

`data/` 中缺失的文件会在对应源首次成功更新时生成。
