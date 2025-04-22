import requests
from pathlib import Path
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# 禁用SSL警告
urllib3.disable_warnings(InsecureRequestWarning)

def filter_live_sources():
    # 模板频道列表
    template_channels = [
        "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5", "CCTV6", "CCTV7", "CCTV8",
        "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15",
        "湖南卫视", "浙江卫视", "东方卫视", "北京卫视", "江苏卫视", "安徽卫视",
        "重庆卫视", "四川卫视", "天津卫视", "兵团卫视"
    ]
    
    # 苏州地方台
    suzhou_sources = [
        "苏州新闻综合,https://live-auth.51kandianshi.com/szgd/csztv1.m3u8$江苏苏州地方",
        "苏州社会经济,https://live-auth.51kandianshi.com/szgd/csztv2.m3u8$江苏苏州地方",
        "苏州文化生活,https://live-auth.51kandianshi.com/szgd/csztv3.m3u8$江苏苏州地方",
        "苏州生活资讯,https://live-auth.51kandianshi.com/szgd/csztv5.m3u8$江苏苏州地方",
        "苏州4K,https://live-auth.51kandianshi.com/szgd/csztv4k_hd.m3u8$江苏苏州地方"
    ]
    
    # 获取直播源
    url = "https://raw.githubusercontent.com/q1017673817/iptvz/main/zubo.txt"
    try:
        response = requests.get(url, verify=False, timeout=10)
        response.raise_for_status()
        live_sources = response.text.splitlines()
    except requests.RequestException as e:
        print(f"获取直播源失败: {e}")
        return None
    
    # 筛选频道
    filtered_sources = []
    for channel in template_channels:
        matched = [line for line in live_sources if line.startswith(channel + ",")]
        filtered_sources.extend(matched)
    
    # 添加苏州台并去重
    filtered_sources.extend(suzhou_sources)
    unique_sources = list(dict.fromkeys(filtered_sources))

import re

def process_channel_name(name):
    """处理CCTV频道名称标准化"""
    # 匹配所有CCTV相关频道（包括数字和特殊频道）
    pattern = r"CCTV[\-\s]?(\d+)[^\d]*"
    
    # 先尝试提取数字编号
    match = re.search(pattern, name)
    if match:
        return f"CCTV{match.group(1)}"
    
    # 保留非CCTV频道的原始名称（如地方台）
    return name

# 假设原始数据存储格式（根据你的实际数据源调整）
original_sources = [
    "CCTV-1综合,http://113.104.186.81:7088/udp/239.77.1.144:5146",
    "CCTV-2财经,http://27.46.65.9:17088/udp/239.0.1.4:8084",
    "湖南卫视,http://example.com/stream"
]

processed_sources = []
for source in original_sources:
    try:
        name, url = source.split(",", 1)
        clean_name = process_channel_name(name)
        processed_sources.append(f"{clean_name},{url}")
    except ValueError:
        continue

# 写入处理后的文件（根据你的实际文件路径调整）
with open("set/zubo.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(processed_sources))
    
    # 写入文件
    output_path = Path(__file__).parent / "zubo.txt"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(unique_sources))
        print(f"成功保存到: {output_path}")
        print(f"总频道数: {len(unique_sources)} (含 {len(suzhou_sources)} 个苏州台)")
        return True
    except IOError as e:
        print(f"文件写入失败: {e}")
        return False

if __name__ == "__main__":
    filter_live_sources()
