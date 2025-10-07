import requests
from pathlib import Path
import urllib3
import re
import time
import concurrent.futures
from urllib3.exceptions import InsecureRequestWarning

# 禁用SSL警告
urllib3.disable_warnings(InsecureRequestWarning)

def test_source_speed(url, timeout=5):
    """测试直播源的速度，返回响应时间(秒)"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout, verify=False, stream=True)
        # 只读取一小部分数据来测试连接速度
        for _ in response.iter_content(1024):  # 读取1KB数据
            break
        response.close()
        end_time = time.time()
        return end_time - start_time
    except:
        return float('inf')  # 如果失败返回无穷大

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
            name, source_url = line.split(",", 1)
            clean_name = process_channel_name(name)
            if any(clean_name.startswith(ch) for ch in template_channels):
                processed_sources.append((clean_name, source_url))
        except ValueError:
            continue
    
    # 添加苏州台
    for suzhou_source in suzhou_sources:
        name, source_url = suzhou_source.split(",", 1)
        processed_sources.append((name, source_url))
    
    # 去重
    unique_sources = list(dict.fromkeys([f"{name},{url}" for name, url in processed_sources]))
    
    # 测试所有源的速度
    print("开始测试直播源速度...")
    sources_with_speed = []
    
    # 使用线程池并发测试速度
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # 准备测试任务
        future_to_source = {}
        for source in unique_sources:
            name, source_url = source.split(",", 1)
            # 提取真实的m3u8 URL（去掉可能的分组信息）
            m3u8_url = source_url.split('$')[0] if '$' in source_url else source_url
            future = executor.submit(test_source_speed, m3u8_url)
            future_to_source[future] = (name, source_url)
        
        # 收集结果
        completed = 0
        total = len(future_to_source)
        for future in concurrent.futures.as_completed(future_to_source):
            name, source_url = future_to_source[future]
            speed = future.result()
            completed += 1
            print(f"进度: {completed}/{total} - {name}: {speed:.2f}s" if speed != float('inf') else f"进度: {completed}/{total} - {name}: 超时")
            
            if speed != float('inf'):  # 只保留有效的源
                sources_with_speed.append((name, source_url, speed))
    
    # 按速度排序并保留前10个最快的
    sources_with_speed.sort(key=lambda x: x[2])  # 按速度升序排序
    fastest_sources = [f"{name},{url}" for name, url, speed in sources_with_speed[:10]]
    
    print(f"\n速度测试完成，共找到 {len(fastest_sources)} 个有效直播源")
    print("最快的10个源：")
    for i, (name, url, speed) in enumerate(sources_with_speed[:10], 1):
        print(f"{i}. {name}: {speed:.2f}秒")
    
    return fastest_sources

def main():
    # 获取并处理直播源
    filtered_sources = filter_live_sources()
    
    # 写入文件
    output_path = Path(__file__).parent / "zubo.txt"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(filtered_sources))
        print(f"\n成功保存到: {output_path}")
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
