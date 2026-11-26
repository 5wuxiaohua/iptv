# IPTV

使用 GitHub Actions 生成 M3U 播放列表，通过 GitHub Pages 提供访问链接，并自动删除到期的用户目录。

## 实现流程

### 生成和发布

手动运行 `Generate IPTV playlist`，传入省份、运营商、用户名和失效日期。

Action 使用 Python 下载对应的 TXT 播放列表：

```text
https://raw.githubusercontent.com/xisohi/CHINA-IPTV/main/Unicast/{省份}/{运营商}.txt
```

程序将 TXT 转换为 M3U，保留频道分组和多个播放地址，保存到：

```text
data/省份-运营商-用户名-失效日期/playlist.m3u
```

生成后清理到期目录，将数据变更提交到仓库默认分支，再把 `data/` 的内容部署到 Pages 站点根目录。

### 自动清理

`Clean expired IPTV playlists` 每天北京时间 **00:00** 自动运行。

程序识别用户目录中的失效日期，删除日期小于或等于当天的目录，再提交变更并重新发布 Pages。这样也能补清之前漏跑任务留下的过期目录。

例如：失效日期为 `2026-12-31`，表示从北京时间 12 月 31 日 00:00 开始失效。如果希望当天全天有效，应填写 `2027-01-01`。

## 使用方法

### 1. 配置仓库

将项目推送到 GitHub 默认分支，然后配置：

- **Settings → Actions → General**：启用 Actions，允许工作流申请仓库写入权限。
- **Settings → Pages → Build and deployment → Source**：选择 **GitHub Actions**。
- 如默认分支有保护规则，确保工作流可以推送数据变更。

工作流已声明 `contents: write`、`pages: write` 和 `id-token: write` 权限，分别用于数据提交和 Pages 发布。

### 2. 生成播放列表

进入 **Actions → Generate IPTV playlist → Run workflow**，选择默认分支，填写参数：

| 参数 | 含义 | 示例 |
| --- | --- | --- |
| `province` | 上游省份目录名，自动去除首尾空格并转为小写英文字母 | `beijing`、`shanxi` |
| `operator` | 移动 `mobile`、联通 `unicom`、电信 `telecom` | `mobile` |
| `username` | 用户名，仅支持英文字母、数字、下划线 | `zhangsan` |
| `expires` | 失效日期，格式为 `YYYY-MM-DD`，必须晚于北京时间今天 | `2026-12-31` |

上游必须存在对应省份和运营商的 TXT 文件。

点击运行，等待生成和部署步骤全部完成。上述示例生成的文件是：

```text
data/beijing-mobile-zhangsan-2026-12-31/playlist.m3u
```

### 3. 使用播放链接

当前工作流将 `data/` 的内容发布到站点根目录，因此链接格式为：

```text
https://<GitHub用户名>.github.io/<仓库名>/省份-运营商-用户名-失效日期/playlist.m3u
```

本仓库示例：

```text
https://5wuxiaohua.github.io/iptv/beijing-mobile-zhangsan-2026-12-31/playlist.m3u
```

**链接不包含 `/data/`。** 将完整链接填入支持 M3U 网络播放列表的播放器。

### 4. 更新或续期

- 使用相同参数再次生成：更新列表内容，链接不变。
- 修改失效日期重新生成：创建新目录和新链接，需将新链接发给用户；原目录按原日期到期清理。

当前仅在手动生成时下载上游内容，不会每天自动刷新列表。

### 5. 手动清理

进入 **Actions → Clean expired IPTV playlists → Run workflow**，选择默认分支运行，无需参数。

任务会立即删除到期目录并重新发布 Pages。日常自动清理无需手动操作。

## 注意事项

- 在 Actions 运行记录中查看生成路径、删除记录和部署结果。数据已提交但发布失败时，可以修复配置后运行清理 Action 重新发布。
- 用户目录只是独立链接，没有用户鉴权；知道完整链接的人均可访问。
- 到期删除无法撤回已下载的列表，也不能使原始直播地址失效。
- 定时任务和 Pages 发布可能延迟，不保证零点准时停止访问。
- 本项目不代理视频流、不检测直播地址可用性，播放器需能直接访问直播源。
