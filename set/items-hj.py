import requests
from pathlib import Path
import urllib3
import re
import time
import concurrent.futures
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)

def process_channel_name(name):
    pattern = r"CCTV[\-\s]?(\d+)[^\d]*"
    match = re.search(pattern, name)
    return f"CCTV{match.group(1)}" if match else name

def test_url_speed(url):
    try:
        start_time = time.time()
        response = requests.head(url, timeout=5, verify=False)
        if response.status_code == 200:
            return time.time() - start_time
        else:
            return float('inf')
    except:
        return float('inf')

def filter_live_sources():
    template_channels = [
        "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5", "CCTV6", "CCTV7", "CCTV8",
        "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15",
        "湖南卫视", "浙江卫视", "东方卫视", "北京卫视", "江苏卫视", "安徽卫视",
        "重庆卫视", "四川卫视", "天津卫视", "兵团卫视"
    ]
    
    suzhou_sources = [
        "苏州新闻综合,http://live-auth.51kandianshi.com/szgd/csztv1.m3u8$江苏苏州地方",
        "苏州社会经济,http://live-auth.51kandianshi.com/szgd/csztv2.m3u8$江苏苏州地方",
        "苏州文化生活,http://live-auth.51kandianshi.com/szgd/csztv3.m3u8$江苏苏州地方",
        "苏州生活资讯,http://live-auth.51kandianshi.com/szgd/csztv5.m3u8$江苏苏州地方",
        "苏州4K,http://live-auth.51kandianshi.com/szgd/csztv4k_hd.m3u8$江苏苏州地方"
    ]
    
    urls = [
        "https://raw.githubusercontent.com/gzj7003/iptvz/refs/heads/main/zubo.txt",
        "https://raw.githubusercontent.com/Supprise0901/TVBox_live/refs/heads/main/live.txt"
    ]
    
    # 合并所有源的字典
    channel_sources = {}
    
    for source_url in urls:
        try:
            response = requests.get(source_url, verify=False, timeout=10)
            response.raise_for_status()
            live_sources = response.text.splitlines()
        except requests.RequestException as e:
            print(f"获取直播源失败 {source_url}: {e}")
            continue  # 失败则尝试下一个URL
        
        for line in live_sources:
            try:
                name, channel_url = line.split(",", 1)
                clean_name = process_channel_name(name)
                if any(clean_name.startswith(ch) for ch in template_channels):
                    if clean_name not in channel_sources:
                        channel_sources[clean_name] = []
                    channel_sources[clean_name].append(channel_url)
            except ValueError:
                continue
    
    if not channel_sources:
        print("未获取到任何直播源，请检查URL或网络")
        return []
    
    filtered_sources = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for channel, urls_list in channel_sources.items():
            print(f"测试频道 {channel} 的 {len(urls_list)} 个源...")
            future_to_url = {executor.submit(test_url_speed, url): url for url in urls_list}
            speed_results = []
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    speed = future.result()
                    speed_results.append((url, speed))
                except Exception as e:
                    print(f"测试URL {url} 时出错: {e}")
                    speed_results.append((url, float('inf')))
            
            speed_results.sort(key=lambda x: x[1])
            fastest_urls = speed_results[:10]
            for url, speed in fastest_urls:
                if speed < float('inf'):
                    filtered_sources.append(f"{channel},{url}")
                    print(f"  保留: {url} (响应时间: {speed:.2f}s)")
    
    filtered_sources.extend(suzhou_sources)
    return filtered_sources

def main():
    filtered_sources = filter_live_sources()
    output_path = Path(__file__).parent / "zubo.txt"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(filtered_sources))
        print(f"成功保存到: {output_path}")
        print(f"总频道数: {len(filtered_sources)}")
        return True
    except IOError as e:
        print(f"文件写入失败: {e}")
        return False

if __name__ == "__main__":
    if main():
        print("执行成功")
    else:
        print("执行过程中遇到错误")
