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
import json

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
    """测试URL的响应速度 - 简化版本"""
    try:
        start_time = time.time()
        # 先尝试HEAD请求
        try:
            response = requests.head(url, timeout=2, verify=False, allow_redirects=True)
            if response.status_code in [200, 206, 301, 302, 307, 308]:
                return time.time() - start_time
        except:
            pass
        
        # 如果HEAD失败，尝试GET少量数据
        start_time = time.time()
        response = requests.get(url, timeout=2, verify=False, stream=True)
        # 只读取前512字节来确认可用性
        chunk = next(response.iter_content(chunk_size=512, decode_unicode=False), None)
        response.close()
        
        if response.status_code == 200 and chunk is not None:
            return time.time() - start_time
        else:
            return float('inf')
    except Exception:
        return float('inf')

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
        "苏州新闻综合,http://live-auth.51kandianshi.com/szgd/csztv1.m3u8",
        "苏州社会经济,http://live-auth.51kandianshi.com/szgd/csztv2.m3u8",
        "苏州文化生活,http://live-auth.51kandianshi.com/szgd/csztv3.m3u8",
        "苏州生活资讯,http://live-auth.51kandianshi.com/szgd/csztv5.m3u8",
        "苏州4K,http://live-auth.51kandianshi.com/szgd/csztv4k_hd.m3u8"
    ]
    
    # 直播源地址列表 - 使用编码后的URL
    source_urls = [
        "https://raw.githubusercontent.com/q1017673817/iptvz/main/zubo.txt",
        "https://raw.githubusercontent.com/q1017673817/iptvz/main/txt/%E5%AE%89%E5%BE%BD%E7%94%B5%E4%BF%A1.txt",
        "https://raw.githubusercontent.com/q1017673817/iptvz/main/txt/%E5%8C%97%E4%BA%AC%E7%94%B5%E4%BF%A1.txt"
    ]
    
    # 从多个源获取直播源
    all_live_sources = []
    
    for url in source_urls:
        try:
            safe_print(f"正在获取直播源: {url}")
            response = requests.get(url, verify=False, timeout=15)
            response.raise_for_status()
            live_sources = response.text.strip().splitlines()
            # 过滤掉注释行和空行
            live_sources = [line for line in live_sources if line.strip() and not line.startswith('#')]
            all_live_sources.extend(live_sources)
            safe_print(f"  从 {url} 获取到 {len(live_sources)} 行")
        except requests.RequestException as e:
            safe_print(f"获取直播源失败 ({url}): {e}")
            continue
    
    # 如果没有获取到任何直播源，只返回苏州台
    if not all_live_sources:
        safe_print("未能从任何源获取到直播源，仅返回苏州台")
        return suzhou_sources
    
    # 去重
    unique_sources = list(dict.fromkeys(all_live_sources))
    safe_print(f"总共获取到 {len(all_live_sources)} 行直播源数据，去重后 {len(unique_sources)} 行")
    
    # 按频道分组直播源
    channel_sources = {}
    for line in unique_sources:
        line = line.strip()
        if not line:
            continue
            
        # 尝试多种分隔符
        if ',' in line:
            parts = line.split(',', 1)
        elif '$' in line:
            parts = line.split('$', 1)
        else:
            continue
            
        if len(parts) < 2:
            continue
            
        name, url = parts
        # 清理URL（移除末尾的$和之后的内容）
        url = url.split('$')[0].strip()
        if not url.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
            continue
            
        clean_name = process_channel_name(name)
        if any(clean_name.startswith(ch) for ch in template_channels):
            if clean_name not in channel_sources:
                channel_sources[clean_name] = []
            if url not in channel_sources[clean_name]:
                channel_sources[clean_name].append(url)
    
    safe_print(f"按 {len(channel_sources)} 个频道分组")
    
    # 为每个频道测试并选择最快的源
    filtered_sources = []
    
    # 限制并发数
    max_workers = 5
    
    # 简化测试：只测试前几个URL，避免耗时过长
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for channel, urls in channel_sources.items():
            if not urls:
                continue
                
            # 每个频道最多测试5个URL
            urls_to_test = urls[:5]
            safe_print(f"测试频道 {channel} 的 {len(urls_to_test)} 个源...")
            
            # 测试URL速度
            future_to_url = {executor.submit(test_url_speed, url): url for url in urls_to_test}
            speed_results = []
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    speed = future.result()
                    if speed < float('inf'):
                        speed_results.append((url, speed))
                except Exception:
                    pass
            
            # 按速度排序并选择最快的源
            if speed_results:
                speed_results.sort(key=lambda x: x[1])
                # 只取最快的一个
                fastest_url = speed_results[0]
                filtered_sources.append(f"{channel},{fastest_url[0]}")
                safe_print(f"  保留: {fastest_url[0]} (响应时间: {fastest_url[1]:.2f}s)")
            else:
                # 如果没有可用的，使用第一个URL
                filtered_sources.append(f"{channel},{urls[0]}")
                safe_print(f"  使用默认: {urls[0]}")
    
    # 添加苏州台
    filtered_sources.extend(suzhou_sources)
    
    safe_print(f"最终筛选出 {len(filtered_sources)} 个直播源")
    return filtered_sources

def main():
    try:
        # 获取当前脚本所在目录
        current_dir = Path(__file__).parent.absolute()
        safe_print(f"当前脚本目录: {current_dir}")
        safe_print(f"当前工作目录: {os.getcwd()}")
        
        # 创建备份文件
        backup_file = current_dir / "backup_sources.json"
        try:
            # 读取现有文件作为备份
            if os.path.exists(current_dir / "zby.txt"):
                with open(current_dir / "zby.txt", "r", encoding="utf-8") as f:
                    backup_content = f.read()
                with open(backup_file, "w", encoding="utf-8") as f:
                    json.dump({"timestamp": time.time(), "content": backup_content}, f)
                safe_print("已创建备份文件")
        except:
            pass
        
        # 获取并处理直播源
        filtered_sources = filter_live_sources()
        
        if not filtered_sources:
            safe_print("警告: 没有获取到任何直播源，使用备份或苏州台")
            # 尝试从备份恢复
            try:
                if os.path.exists(backup_file):
                    with open(backup_file, "r", encoding="utf-8") as f:
                        backup_data = json.load(f)
                    filtered_sources = backup_data["content"].splitlines()
                    safe_print("从备份文件恢复直播源")
                else:
                    # 使用苏州台
                    filtered_sources = [
                        "苏州新闻综合,http://live-auth.51kandianshi.com/szgd/csztv1.m3u8",
                        "苏州社会经济,http://live-auth.51kandianshi.com/szgd/csztv2.m3u8",
                        "苏州文化生活,http://live-auth.51kandianshi.com/szgd/csztv3.m3u8",
                        "苏州生活资讯,http://live-auth.51kandianshi.com/szgd/csztv5.m3u8",
                        "苏州4K,http://live-auth.51kandianshi.com/szgd/csztv4k_hd.m3u8"
                    ]
            except:
                safe_print("错误: 无法恢复直播源")
                return False
        
        # 写入文件
        output_path = current_dir / "zby.txt"
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
                
                # 显示文件统计信息
                with open(output_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        safe_print(f"文件行数: {len(lines)}")
                        safe_print("文件前3行内容:")
                        for i in range(min(3, len(lines))):
                            safe_print(f"  {lines[i].strip()}")
                    else:
                        safe_print("警告: 文件为空!")
                        return False
                
                # 确保文件有内容
                if file_size == 0:
                    safe_print("错误: 文件大小为0")
                    return False
                    
                return True
            else:
                safe_print("错误: 文件未创建成功")
                return False
                
        except IOError as e:
            safe_print(f"文件写入失败: {e}")
            return False
    except Exception as e:
        safe_print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    start_time = time.time()
    success = main()
    end_time = time.time()
    safe_print(f"程序运行时间: {end_time - start_time:.2f}秒")
    
    if success:
        safe_print("执行成功")
        exit(0)
    else:
        safe_print("执行过程中遇到错误")
        exit(1)
