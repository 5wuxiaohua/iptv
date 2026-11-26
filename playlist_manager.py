#!/usr/bin/env python3
"""Generate user playlists and remove expired playlists for GitHub Pages."""
import argparse
from datetime import date, datetime
from pathlib import Path
import re
import shutil
from zoneinfo import ZoneInfo

from iptv_updater import atomic_write, download_txt, txt_to_m3u

BASE_URL = 'https://raw.githubusercontent.com/xisohi/CHINA-IPTV/main/Unicast'
OPERATORS = {'移动': 'mobile', '联通': 'unicom', '电信': 'telecom',
             'mobile': 'mobile', 'unicom': 'unicom', 'telecom': 'telecom'}
DIRECTORY = re.compile(r'([a-z]+)-(mobile|unicom|telecom)-([A-Za-z0-9_]+)-(\d{4}-\d{2}-\d{2})')


def today():
    return datetime.now(ZoneInfo('Asia/Shanghai')).date()


def parse_date(value):
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError('日期必须为 YYYY-MM-DD')
    return parsed


def generate(data_dir, province, operator, username, expires):
    province = province.strip().lower()
    if not re.fullmatch(r'[a-z]+', province):
        raise ValueError('省份必须为上游目录的小写拼音，例如 beijing、shanxi')
    if operator not in OPERATORS:
        raise ValueError('运营商必须为 mobile、unicom、telecom 或移动、联通、电信')
    operator = OPERATORS[operator]
    if not re.fullmatch(r'[A-Za-z0-9_]+', username):
        raise ValueError('用户名仅支持英文字母、数字、下划线')
    if parse_date(expires) <= today():
        raise ValueError('失效日期必须晚于今天（北京时间，当天 00:00 失效）')
    directory = data_dir / f'{province}-{operator}-{username}-{expires}'
    if directory.is_symlink():
        raise ValueError('拒绝写入符号链接目录')
    # Download and convert before creating or replacing any output.
    m3u = txt_to_m3u(download_txt(f'{BASE_URL}/{province}/{operator}.txt'))
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / 'playlist.m3u'
    atomic_write(str(target), m3u)
    print(f'生成：{target}')
    return target


def cleanup(data_dir, cutoff=None):
    cutoff = cutoff or today()
    removed = []
    if not data_dir.exists():
        return removed
    for directory in sorted(data_dir.iterdir()):
        match = DIRECTORY.fullmatch(directory.name)
        if not match or directory.is_symlink() or not directory.is_dir():
            continue
        try:
            expires = parse_date(match.group(4))
        except ValueError:
            continue
        if expires <= cutoff:
            shutil.rmtree(directory)
            removed.append(directory.name)
            print(f'删除到期目录：{directory.name}')
    return removed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('generate')
    create.add_argument('--province', required=True)
    create.add_argument('--operator', required=True)
    create.add_argument('--username', required=True)
    create.add_argument('--expires', required=True)
    commands.add_parser('cleanup')
    args = parser.parse_args()
    if args.command == 'generate':
        generate(args.data_dir, args.province, args.operator, args.username, args.expires)
    else:
        cleanup(args.data_dir)


if __name__ == '__main__':
    main()
