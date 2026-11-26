# IPTV playlists with GitHub Actions and Pages

通过 GitHub Actions 按省份、运营商、用户名、失效日期生成 M3U，发布到 GitHub Pages；每天北京时间 00:00 清理到期目录并重新发布。
Python 仅使用标准库，无需常驻服务器或 Docker。

## 首次配置

1. 将代码提交到 GitHub 仓库的默认分支。
2. 在 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
3. 允许 Actions 使用 `contents: write`、`pages: write`、`id-token: write` 权限。工作流会提交 `data/` 的变动；如果默认分支保护规则禁止 Actions 直接推送，需要调整对应规则。
4. 在 **Actions → Generate IPTV playlist → Run workflow** 填入参数，选择默认分支运行。

代码在本地修改后不会自动上传；需要自行提交、推送。只有默认分支允许执行这两个工作流。

## 生成播放列表

| 参数 | 格式 | 示例 |
| --- | --- | --- |
| `province` | 上游 `Unicast/` 下的省份目录名，小写拼音 | `beijing`、`shanxi` |
| `operator` | `mobile`（移动）、`unicom`（联通）、`telecom`（电信） | `mobile` |
| `username` | 英文字母、数字、下划线 | `zhangsan` |
| `expires` | `YYYY-MM-DD`，必须晚于北京时间今天 | `2026-12-31` |

数据源按以下格式构造，是否可用取决于上游是否存在对应文件：

```text
https://raw.githubusercontent.com/xisohi/CHINA-IPTV/main/Unicast/{province}/{operator}.txt
```

例如上述参数会生成：

```text
data/beijing-mobile-zhangsan-2026-12-31/playlist.m3u
```

发布时将 `data/` 的内容作为站点根目录，播放地址为：

```text
https://<GitHub用户名>.github.io/<仓库名>/beijing-mobile-zhangsan-2026-12-31/playlist.m3u
```

使用自定义域名或用户主页仓库时，以 Pages 实际站点地址为准。工作流部署步骤会显示站点地址。
同一组参数再次运行会更新原文件；修改日期会创建新目录，旧目录保留到原日期到期。
生成后不会自动刷新用户播放列表内容，需要再次运行生成工作流。

## 到期清理

`Clean expired IPTV playlists` 工作流支持定时和手动运行。

- `0 16 * * *` 使用 UTC，等于北京时间次日 00:00。
- 失效日期表示**该日期开始时失效**。`2026-12-31` 将在北京时间 12 月 31 日 00:00 的任务中清理；如需当天全天有效，应填 `2027-01-01`。
- 删除日期小于或等于执行当天的匹配目录，补清漏跑任务遗留的过期数据。
- 仅处理 `省份-运营商-用户名-YYYY-MM-DD` 格式的直接子目录，不跟随符号链接，不处理历史根目录 M3U/SHA256 文件。
- 删除后提交仓库，并重新部署整个 Pages 站点；只删除仓库文件不足以更新已发布的站点。
- 两个工作流共用串行并发组，避免互相覆盖数据和部署。GitHub 默认并发队列可能替换较早的待运行任务，批量触发时请检查每次运行结果。

GitHub 定时任务可能延迟、漏跑；公开仓库长期无活动时定时工作流也可能被自动停用。失效时间不是严格的访问截止时间，还受部署和缓存影响。

## 访问范围与边界

用户名只是目录标识，公开 Pages 不提供用户登录和鉴权，持有链接的人均可下载。
不要在用户名中使用敏感信息。到期删除无法撤回已下载的 M3U，也无法禁止用户继续访问其中的原始直播 URL；提交历史仍可能保留旧播放列表。
本工具不代理直播、不检测可播放性。播放器仍需具备访问直播源的网络条件，例如 IPv6 或对应运营商网络。
当前 `data/` 中原有的北京、山西 M3U 和 SHA256 也会随站点发布，不受用户目录到期规则管理。

## 本地使用与验证

```bash
python3 playlist_manager.py generate --province beijing --operator mobile --username zhangsan --expires 2026-12-31
python3 playlist_manager.py cleanup
python3 -m unittest discover -s tests -v
```

可在子命令前加 `--data-dir /path/to/data` 指定数据目录。
下载或转换失败时不会覆盖已有 M3U；转换保留分组和重复频道的不同地址，使用临时文件原子替换。

## 文件说明

| 文件 | 用途 |
| --- | --- |
| `playlist_manager.py` | 单次生成、参数校验和到期清理 |
| `iptv_updater.py` | 复用下载、转换和原子写入函数；保留原 Docker 定时更新入口 |
| `.github/workflows/generate-playlist.yml` | 手动生成、提交、发布 |
| `.github/workflows/cleanup-playlists.yml` | 定时或手动清理、提交、发布 |
| `tests/test_playlist_manager.py` | 离线验证生成、校验、失败保留和清理边界 |

原 Docker 方式仍可通过 `docker compose up -d --build` 运行，仅更新根目录的山西、北京移动列表，不执行新的用户目录管理。`nginx/default.conf` 是未启用的旧配置。
