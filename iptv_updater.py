#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import os
import time
import urllib.request


# ============================================================
# 配置
# ============================================================

SOURCES = (
    {"id": "shanxi_mobile", "name": "山西移动", "region": "shanxi"},
    {"id": "beijing_mobile", "name": "北京移动", "region": "beijing"},
)

DATA_DIR = "/opt/iptv/data"

# 每24小时检查一次
CHECK_INTERVAL = 24 * 60 * 60
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
# SHA256
# ============================================================
def calculate_sha256(text):
    text = (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()

def read_old_hash(hash_file):
    if not os.path.exists(hash_file):
        return None

    try:
        with open(
            hash_file,
            "r",
            encoding="utf-8"
        ) as f:
            return f.read().strip()

    except Exception as e:
        log(
            "读取HASH失败：{}".format(e)
        )
        return None

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


# ============================================================
# 更新
# ============================================================

def update(source):
    url = (
        "https://raw.githubusercontent.com/xisohi/CHINA-IPTV/"
        "main/Unicast/{}/mobile.txt".format(source["region"])
    )
    m3u_file = os.path.join(DATA_DIR, source["id"] + ".m3u")
    hash_file = os.path.join(DATA_DIR, source["id"] + ".sha256")

    log(
        "========================================"
    )
    log(
        "开始检查 IPTV 源：{}".format(source["name"])
    )
    # --------------------------------------------------------
    # 下载
    # --------------------------------------------------------

    try:
        txt = download_txt(url)

    except Exception as e:
        log(
            "下载失败：{}".format(e)
        )
        log(
            "保留当前M3U"
        )
        return False

    # --------------------------------------------------------
    # HASH
    # --------------------------------------------------------

    new_hash = calculate_sha256(txt)
    old_hash = read_old_hash(hash_file)
    log(
        "远端SHA256：{}".format(
            new_hash
        )
    )

    if old_hash:
        log(
            "本地SHA256：{}".format(
                old_hash
            )
        )
    # --------------------------------------------------------
    # 没变化
    # --------------------------------------------------------
    if (
        old_hash == new_hash
        and
        os.path.exists(m3u_file)
    ):
        log(
            "TXT没有变化，不更新"
        )
        return False

    # --------------------------------------------------------
    # 转换
    # --------------------------------------------------------

    log(
        "检测到变化，开始生成M3U"
    )

    try:
        m3u = txt_to_m3u(txt)
    except Exception as e:
        log(
            "转换失败：{}".format(e)
        )
        log(
            "保留当前M3U"
        )
        return False

    # --------------------------------------------------------
    # 更新M3U
    # --------------------------------------------------------

    try:
        atomic_write(
            m3u_file,
            m3u
        )

    except Exception as e:
        log(
            "M3U更新失败：{}".format(e)
        )
        return False

    # --------------------------------------------------------
    # M3U成功以后再更新HASH
    # --------------------------------------------------------

    try:
        atomic_write(
            hash_file,
            new_hash + "\n"
        )

    except Exception as e:
        log(
            "HASH更新失败：{}".format(e)
        )
    log(
        "M3U更新成功：{}".format(
            m3u_file
        )
    )

    return True

# ============================================================
# Main
# ============================================================

def main():
    log(
        "========================================"
    )
    log(
        " IPTV Updater"
    )
    log(
        "========================================"
    )

    os.makedirs(
        DATA_DIR,
        exist_ok=True
    )

    while True:
        # 容器启动后立即更新一次
        for source in SOURCES:
            try:
                update(source)
            except Exception as e:
                log(
                    "{}更新异常：{}".format(source["name"], e)
                )
        log(
            "下一次检查：24小时后"
        )

        time.sleep(
            CHECK_INTERVAL
        )

if __name__ == "__main__":
    main()
