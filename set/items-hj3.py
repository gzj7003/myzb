import requests
from pathlib import Path
import urllib3
import re
import time
import concurrent.futures
from urllib3.exceptions import InsecureRequestWarning
import socket
import threading
import os

# 禁用SSL警告
urllib3.disable_warnings(InsecureRequestWarning)

# 设置默认超时时间
socket.setdefaulttimeout(10)

# 线程安全的打印
print_lock = threading.Lock()
def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)

def process_channel_name(name):
    """处理CCTV频道名称标准化"""
    pattern = r"CCTV[\-\s]?(\d+)[^\d]*"
    match = re.search(pattern, name)
    return f"CCTV{match.group(1)}" if match else name

def test_url_speed(url):
    """测试URL的响应速度"""
    try:
        start_time = time.time()
        # 使用GET而不是HEAD，因为有些服务器不支持HEAD方法
        response = requests.get(url, timeout=5, verify=False, stream=True)
        end_time = time.time()
        if response.status_code in [200, 206]:  # 206表示部分内容
            # 立即关闭连接，避免占用资源
            response.close()
            return end_time - start_time
        else:
            return float('inf')  # 返回无穷大表示不可用
    except Exception as e:
        # safe_print(f"测试URL {url} 失败: {e}")
        return float('inf')  # 返回无穷大表示不可用

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
        "苏州新闻综合,http://live-auth.51kandianshi.com/szgd/csztv1.m3u8$江苏苏州地方",
        "苏州社会经济,http://live-auth.51kandianshi.com/szgd/csztv2.m3u8$江苏苏州地方",
        "苏州文化生活,http://live-auth.51kandianshi.com/szgd/csztv3.m3u8$江苏苏州地方",
        "苏州生活资讯,http://live-auth.51kandianshi.com/szgd/csztv5.m3u8$江苏苏州地方",
        "苏州4K,http://live-auth.51kandianshi.com/szgd/csztv4k_hd.m3u8$江苏苏州地方"
    ]
    
    # 修正的直播源地址列表
    source_urls = [
        "https://raw.githubusercontent.com/q1017673817/iptvz/main/zubo.txt",
        "https://raw.githubusercontent.com/q1017673817/iptvz/main/txt/安徽电信.txt",
        "https://raw.githubusercontent.com/q1017673817/iptvz/main/txt/北京电信.txt"
    ]
    
    # 从多个源获取直播源
    all_live_sources = []
    
    for url in source_urls:
        try:
            safe_print(f"正在获取直播源: {url}")
            response = requests.get(url, verify=False, timeout=15)
            response.raise_for_status()
            live_sources = response.text.splitlines()
            all_live_sources.extend(live_sources)
            safe_print(f"  从 {url} 获取到 {len(live_sources)} 行")
        except requests.RequestException as e:
            safe_print(f"获取直播源失败 ({url}): {e}")
    
    if not all_live_sources:
        safe_print("未能从任何源获取到直播源")
        return []
    
    safe_print(f"总共获取到 {len(all_live_sources)} 行直播源数据")
    
    # 按频道分组直播源
    channel_sources = {}
    processed_count = 0
    for line in all_live_sources:
        # 跳过空行
        if not line.strip():
            continue
            
        try:
            # 分割频道名和URL
            parts = line.split(",", 1)
            if len(parts) < 2:
                continue
                
            name, url = parts
            clean_name = process_channel_name(name)
            if any(clean_name.startswith(ch) for ch in template_channels):
                if clean_name not in channel_sources:
                    channel_sources[clean_name] = []
                channel_sources[clean_name].append(url)
                processed_count += 1
        except ValueError:
            continue
    
    safe_print(f"处理了 {processed_count} 个直播源，按 {len(channel_sources)} 个频道分组")
    
    # 为每个频道测试并选择最快的源
    filtered_sources = []
    
    # 限制并发数，避免连接过多
    max_workers = 20
    
    # 使用线程池并行测试速度
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for channel, urls in channel_sources.items():
            if not urls:
                continue
                
            safe_print(f"测试频道 {channel} 的 {len(urls)} 个源...")
            
            # 测试所有URL的速度
            future_to_url = {executor.submit(test_url_speed, url): url for url in urls}
            speed_results = []
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    speed = future.result()
                    speed_results.append((url, speed))
                except Exception as e:
                    # safe_print(f"测试URL {url} 时出错: {e}")
                    speed_results.append((url, float('inf')))
            
            # 按速度排序并选择最快的10个
            speed_results.sort(key=lambda x: x[1])
            # 只选择速度不是无穷大的源
            valid_sources = [item for item in speed_results if item[1] < float('inf')]
            
            # 如果有效源少于10个，则全部使用
            fastest_urls = valid_sources[:10] if len(valid_sources) > 10 else valid_sources
            
            # 添加到结果列表
            for url, speed in fastest_urls:
                filtered_sources.append(f"{channel},{url}")
                safe_print(f"  保留: {url} (响应时间: {speed:.2f}s)")
    
    # 添加苏州台
    filtered_sources.extend(suzhou_sources)
    
    safe_print(f"最终筛选出 {len(filtered_sources)} 个直播源")
    return filtered_sources

def main():
    try:
        # 获取当前脚本所在目录
        current_dir = Path(__file__).parent.absolute()
        safe_print(f"当前脚本目录: {current_dir}")
        
        # 获取并处理直播源
        filtered_sources = filter_live_sources()
        
        if not filtered_sources:
            safe_print("错误: 没有获取到任何直播源")
            return False
            
        # 写入文件 - 确保输出为 zb3.txt，保存在脚本同一目录下
        output_path = current_dir / "zb3.txt"
        safe_print(f"输出文件路径: {output_path}")
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(filtered_sources))
            safe_print(f"成功保存到: {output_path}")
            safe_print(f"总频道数: {len(filtered_sources)}")
            
            # 验证文件是否已创建
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                safe_print(f"文件大小: {file_size} 字节")
                
                # 显示文件前几行内容
                try:
                    with open(output_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        if lines:
                            safe_print("文件前5行内容:")
                            for i in range(min(5, len(lines))):
                                safe_print(f"  {lines[i].strip()}")
                        else:
                            safe_print("警告: 文件为空!")
                            return False
                except Exception as e:
                    safe_print(f"读取文件内容出错: {e}")
                    return False
            else:
                safe_print("错误: 文件未创建成功")
                return False
                
            return True
        except IOError as e:
            safe_print(f"文件写入失败: {e}")
            # 尝试检查目录权限
            safe_print(f"当前目录权限: {os.access(current_dir, os.W_OK)}")
            return False
    except Exception as e:
        safe_print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if main():
        safe_print("执行成功")
        exit(0)
    else:
        safe_print("执行过程中遇到错误")
        exit(1)
