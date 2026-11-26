#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared download, M3U conversion and atomic file writing helpers."""

import os
import time
import urllib.request


DOWNLOAD_TIMEOUT = 30

# ============================================================
# 日志
# ============================================================
def log(message):
    print(
        "[{}] {}".format(
            time.strftime("%Y-%m-%d %H:%M:%S"),
            message
        ),
        flush=True
    )
# ============================================================
# 下载TXT
# ============================================================
def download_txt(url):
    log(
        "下载：{}".format(
            url
        )
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "IPTV-Updater/1.0",
            "Accept": "text/plain",
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=DOWNLOAD_TIMEOUT
    ) as response:
        data = response.read()

    log(
        "下载完成：{} bytes".format(
            len(data)
        )
    )

    return data.decode("utf-8-sig")


# ============================================================
# TXT -> M3U
# ============================================================
def txt_to_m3u(txt):
    output = [
        "#EXTM3U"
    ]

    current_group = "未分组"
    group_count = 0
    channel_count = 0

    for raw_line in txt.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # ----------------------------------------------------
        # 分组
        #
        # 央视,#genre#
        # 卫视,#genre#
        # ----------------------------------------------------

        if line.endswith(",#genre#"):
            group = line[
                :-len(",#genre#")
            ].strip()

            if group:
                current_group = group
                group_count += 1
            continue

        # ----------------------------------------------------
        # 频道
        #
        # CCTV1,http://...
        # ----------------------------------------------------

        if "," not in line:
            continue

        name, url = line.split(",", 1)
        name = name.strip()
        url = url.strip()

        if not name:
            continue

        if not url:
            continue

        safe_group = (
            current_group
            .replace('"', "'")
            .strip()
        )

        safe_name = (
            name
            .replace("\r", "")
            .replace("\n", "")
            .strip()
        )

        output.append(
            '#EXTINF:-1 group-title="{}",{}'.format(
                safe_group,
                safe_name
            )
        )

        output.append(url)
        channel_count += 1

    # 防止GitHub返回错误页面等异常情况，
    # 导致正常M3U被空文件覆盖
    if channel_count == 0:
        raise RuntimeError(
            "转换结果为0个频道，拒绝覆盖现有M3U"
        )
    
    log(
        "转换完成：{} 个分组，{} 个频道".format(
            group_count,
            channel_count
        )
    )

    return "\n".join(output) + "\n"

# ============================================================
# 原子写文件
# ============================================================

def atomic_write(filename, content):
    tmp_file = filename + ".tmp"
    try:
        with open(
            tmp_file,
            "w",
            encoding="utf-8",
            newline="\n"
        ) as f:
            f.write(content)
            f.flush()
            os.fsync(
                f.fileno()
            )

        # 原子替换
        os.replace(
            tmp_file,
            filename
        )

    except Exception:
        try:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)

        except Exception:
            pass

        raise
