import requests
from pathlib import Path
import urllib3
import re
import time
import concurrent.futures
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)

# ============ 配置 ============
CONNECT_TIMEOUT = 5
READ_TIMEOUT = 5
MAX_WORKERS = 20
MAX_PER_CHANNEL = 10
FETCH_TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


# ============ 频道名处理 ============
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
            # CCTV 数字频道精确匹配
            if clean_name == ch:
                return ch
        else:
            if clean_name.startswith(ch):
                return ch
    return None


# ============ 测速 ============
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
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
        if response.status_code != 200:
            return float("inf")

        # 读取第一块数据，确认真的能出内容
        chunk = b""
        for c in response.iter_content(chunk_size=1024):
            chunk = c
            break

        if not chunk:
            return float("inf")

        # m3u8 内容校验：应以 #EXTM3U 开头
        clean_url = url.split("?", 1)[0].lower()
        if clean_url.endswith(".m3u8") and b"#EXTM3U" not in chunk:
            return float("inf")

        return time.time() - start_time
    except Exception:
        return float("inf")
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass


# ============ 主流程 ============
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
        "https://raw.githubusercontent.com/gzj7003/myzb/refs/heads/main/itvlist.txt",
        "https://raw.githubusercontent.com/gzj7003/iptvz/refs/heads/main/txt/%E6%B9%96%E5%8D%97%E7%94%B5%E4%BF%A1.txt",
    ]

    # channel -> {test_url: raw_url}
    channel_sources = {}

    for source_url in urls:
        try:
            response = requests.get(
                source_url,
                verify=False,
                timeout=FETCH_TIMEOUT,
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()

            # 编码处理：优先使用声明编码，避免 apparent_encoding 误判
            enc = response.encoding
            if not enc or enc.lower() in ("iso-8859-1", "windows-1252"):
                enc = "utf-8"
            response.encoding = enc

            live_sources = response.text.splitlines()
            print(f"成功获取源: {source_url}，共 {len(live_sources)} 行")
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
            # 用 test_url 去重，保留原始 raw_url（可能带 $分组）
            channel_sources[matched].setdefault(test_url, channel_url.strip())

    if not channel_sources:
        print("未获取到任何直播源，请检查URL或网络")
        return []

    # 统计
    total_sources = sum(len(v) for v in channel_sources.values())
    print(f"匹配到 {len(channel_sources)} 个频道，共 {total_sources} 个源待测速...")

    # 一次性提交所有测速任务
    tasks = []
    for channel, url_map in channel_sources.items():
        for test_url, raw_url in url_map.items():
            tasks.append((channel, test_url, raw_url))

    results = {}  # channel -> list[(raw_url, speed)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(test_url_speed, test_url): (channel, test_url, raw_url)
            for channel, test_url, raw_url in tasks
        }

        done = 0
        total = len(tasks)
        for future in concurrent.futures.as_completed(future_map):
            channel, test_url, raw_url = future_map[future]
            try:
                speed = future.result()
            except Exception as e:
                print(f"测试URL {test_url} 时出错: {e}")
                speed = float("inf")

            results.setdefault(channel, []).append((raw_url, speed))
            done += 1
            if done % 50 == 0 or done == total:
                print(f"  已测速 {done}/{total}")

    # 按模板顺序输出，保证顺序稳定
    filtered_sources = []
    for channel in template_channels:
        items = results.get(channel)
        if not items:
            print(f"  频道 [{channel}] 无可用源")
            continue

        # 过滤掉 inf，再排序
        valid_items = [(u, s) for u, s in items if s < float("inf")]
        valid_items.sort(key=lambda x: x[1])

        if not valid_items:
            print(f"  频道 [{channel}] 无可用源")
            continue

        kept = 0
        for raw_url, speed in valid_items:
            if kept >= MAX_PER_CHANNEL:
                break
            filtered_sources.append(f"{channel},{raw_url}")
            print(f"  保留 [{channel}]: {raw_url} (响应时间: {speed:.2f}s)")
            kept += 1

    # 追加苏州本地源
    filtered_sources.extend(suzhou_sources)

    return filtered_sources


# ============ 入口 ============
def main():
    filtered_sources = filter_live_sources()
    output_path = Path(__file__).parent / "zubo.txt"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(filtered_sources) + "\n")
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
