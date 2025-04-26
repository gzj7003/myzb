import requests
from pathlib import Path
import urllib3
import re
from urllib3.exceptions import InsecureRequestWarning

# 禁用SSL警告
urllib3.disable_warnings(InsecureRequestWarning)

def process_channel_name(name):
    """处理CCTV频道名称标准化"""
    pattern = r"CCTV[\-\s]?(\d+)[^\d]*"
    match = re.search(pattern, name)
    return f"CCTV{match.group(1)}" if match else name

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
        return []

    # 处理频道名称并筛选
    processed_sources = []
    for line in live_sources:
        try:
            name, url = line.split(",", 1)
            clean_name = process_channel_name(name)
            if any(clean_name.startswith(ch) for ch in template_channels):
                processed_sources.append(f"{clean_name},{url}")
        except ValueError:
            continue
    
    # 添加苏州台并去重
    processed_sources.extend(suzhou_sources)
    return list(dict.fromkeys(processed_sources))

def main():
    # 获取并处理直播源
    filtered_sources = filter_live_sources()
    
    # 写入文件
    output_path = Path(__file__).parent / "zubo.txt"  # 删除多余的set/前缀
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
