import requests
from pathlib import Path
import urllib3
import re
import time
import concurrent.futures
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)

# 超时设置
CONNECT_TIMEOUT = 5
READ_TIMEOUT = 5
MAX_WORKERS = 20
MAX_PER_CHANNEL = 10


def process_channel_name(name):
    """把 CCTV-1 / CCTV 1 / CCTV1高清 等统一成 CCTV1"""
    name = name.strip()
    pattern = r"CCTV[\-\s]?(\d+)"
    match = re.search(pattern, name, re.IGNORECASE)
    if match:
        return f"CCTV{int(match.group(1))}"
    return name


def match_template(clean_name, templates):
    """返回匹配到的模板频道名，未匹配返回 None"""
    for ch in templates:
        if ch.startswith("CCTV") and ch[4:].isdigit():
            # CCTV 数字频道：精确匹配，允许 CCTV1-1 / CCTV1高清 等别名
            if clean_name == ch or clean_name.startswith(ch + "-"):
                return ch
        else:
            if clean_name.startswith(ch):
                return ch
    return None


def test_url_speed(url):
    """返回响应耗时（秒），失败返回 inf"""
    response = None
    try:
        start_time = time.time()
        response = requests.get(
            url,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            verify=False,
            stream=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if response.status_code == 200:
            # 读取一小段确认能出数据
            for _ in response.iter_content(chunk_size=1024):
                break
            return time.time() - start_time
        return float("inf")
    except Exception:
        return float("inf")
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass


def filter_live_sources():
    template_channels = [
        "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5", "CCTV6", "CCTV7", "CCTV8",
        "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15",
        "湖南卫视", "浙江卫视", "东方卫视", "北京卫视", "江苏卫视", "安徽卫视",
        "重庆卫视", "四川卫视", "天津卫视", "兵团卫视",
    ]

    suzhou_sources = [
        "苏州新闻综合,http://live-auth.51kandianshi.com/szgd/csztv1.m3u8$江苏苏州地方",
        "苏州社会经济,http://live-auth.51kandianshi.com/szgd/csztv2.m3u8$江苏苏州地方",
        "苏州文化生活,http://live-auth.51kandianshi.com/szgd/csztv3.m3u8$江苏苏州地方",
        "苏州生活资讯,http://live-auth.51kandianshi.com/szgd/csztv5.m3u8$江苏苏州地方",
        "苏州4K,http://live-auth.51kandianshi.com/szgd/csztv4k_hd.m3u8$江苏苏州地方",
    ]

    urls = [
        "https://raw.githubusercontent.com/gzj7003/tv/refs/heads/main/itvlist.txt",
        "https://raw.githubusercontent.com/gzj7003/iptvz/refs/heads/main/txt/%E6%B9%96%E5%8D%97%E7%94%B5%E4%BF%A1.txt",
    ]

    # channel -> {原始url: 测试url}
    channel_sources = {}

    for source_url in urls:
        try:
            response = requests.get(source_url, verify=False, timeout=15)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"
            live_sources = response.text.splitlines()
        except requests.RequestException as e:
            print(f"获取直播源失败 {source_url}: {e}")
            continue

        for line in live_sources:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "," not in line:
                continue
            try:
                name, channel_url = line.split(",", 1)
            except ValueError:
                continue

            clean_name = process_channel_name(name)
            matched = match_template(clean_name, template_channels)
            if not matched:
                continue

            test_url = channel_url.split("$", 1)[0].strip()
            if not test_url:
                continue

            channel_sources.setdefault(matched, {})
            # 保留原始格式（含 $分组），用测试url做 key 去重
            channel_sources[matched].setdefault(test_url, channel_url)

    if not channel_sources:
        print("未获取到任何直播源，请检查URL或网络")
        return []

    # 一次性提交所有测速任务
    tasks = []  # (channel, test_url, raw_url)
    for channel, url_map in channel_sources.items():
        for test_url, raw_url in url_map.items():
            tasks.append((channel, test_url, raw_url))

    print(f"共 {len(tasks)} 个源待测速...")

    results = {}  # channel -> list[(raw_url, speed)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(test_url_speed, test_url): (channel, test_url, raw_url)
            for channel, test_url, raw_url in tasks
        }
        done = 0
        for future in concurrent.futures.as_completed(future_map):
            channel, test_url, raw_url = future_map[future]
            try:
                speed = future.result()
            except Exception as e:
                print(f"测试URL {test_url} 时出错: {e}")
                speed = float("inf")
            results.setdefault(channel, []).append((raw_url, speed))
            done += 1
            if done % 50 == 0:
                print(f"  已测速 {done}/{len(tasks)}")

    filtered_sources = []
    for channel, items in results.items():
        items.sort(key=lambda x: x[1])
        kept = 0
        for raw_url, speed in items:
            if speed < float("inf") and kept < MAX_PER_CHANNEL:
                filtered_sources.append(f"{channel},{raw_url}")
                print(f"  保留 [{channel}]: {raw_url} (响应时间: {speed:.2f}s)")
                kept += 1
        if kept == 0:
            print(f"  频道 [{channel}] 无可用源")

    filtered_sources.extend(suzhou_sources)
    return filtered_sources


def main():
    filtered_sources = filter_live_sources()
    output_path = Path(__file__).parent / "zubo.txt"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(filtered_sources))
        print(f"成功保存到: {output_path}")
        print(f"总条目数: {len(filtered_sources)}")
        return True
    except IOError as e:
        print(f"文件写入失败: {e}")
        return False


if __name__ == "__main__":
    if main():
        print("执行成功")
    else:
        print("执行过程中遇到错误")
