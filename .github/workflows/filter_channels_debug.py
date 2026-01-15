# filter_channels_debug.py - 包含详细日志的版本
import requests
import sys
import os
from datetime import datetime

# 目标电视台列表
target_channels = [
    "CCTV-1综合", "CCTV-2财经", "CCTV-3综艺", "CCTV-4中文国际", "CCTV-5体育",
    "CCTV-6电影", "CCTV-7国防军事", "CCTV-8电视剧", "CCTV-9纪录", "CCTV-10科教",
    "CCTV-11戏曲", "CCTV-12社会与法", "CCTV-13新闻", "CCTV-14少儿", "CCTV-15音乐",
    "江苏卫视", "浙江卫视", "北京卫视", "东方卫视", "湖南卫视"
]

# 苏州地方台
suzhou_channels = [
    ("苏州新闻综合", "https://live-auth.51kandianshi.com/szgd/csztv1.m3u8$!白名单-不参与测速-保留结果在前"),
    ("苏州社会经济", "https://live-auth.51kandianshi.com/szgd/csztv2.m3u8$!白名单-不参与测速-保留结果在前"),
    ("苏州文化生活", "https://live-auth.51kandianshi.com/szgd/csztv3.m3u8$!白名单-不参与测速-保留结果在前"),
    ("苏州生活资讯", "https://live-auth.51kandianshi.com/szgd/csztv5.m3u8$!白名单-不参与测速-保留结果在前"),
    ("苏州4K", "https://live-auth.51kandianshi.com/szgd/csztv4k_hd.m3u8$!白名单-不参与测速-保留结果在前")
]

def filter_channels():
    print(f"开始时间: {datetime.now()}")
    
    # 从源获取数据
    url = "https://raw.githubusercontent.com/gzj7003/iptv-api/refs/heads/master/output/user_result.txt"
    
    try:
        print(f"正在从 {url} 获取数据...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.text
        print(f"成功获取数据，状态码: {response.status_code}, 数据大小: {len(data)} 字节")
    except requests.exceptions.Timeout:
        print("错误：请求超时")
        # 创建备用文件
        create_backup_file()
        return
    except requests.exceptions.RequestException as e:
        print(f"获取源数据失败: {e}")
        # 创建备用文件
        create_backup_file()
        return
    
    # 按行分割
    lines = data.strip().split('\n')
    print(f"源数据共有 {len(lines)} 行")
    
    # 存储匹配到的频道
    matched_channels = []
    matched_count = {channel: 0 for channel in target_channels}
    
    # 遍历每一行，查找目标频道
    for i, line in enumerate(lines[:1000]):  # 只处理前1000行，加快速度
        if ',' in line:
            try:
                channel_name = line.split(',', 1)[0].strip()
                
                # 检查是否是目标频道
                for target in target_channels:
                    if target in channel_name:
                        matched_channels.append(line.strip())
                        matched_count[target] += 1
                        break
            except (ValueError, IndexError):
                continue
    
    print("\n匹配结果统计:")
    for channel in target_channels:
        if matched_count[channel] > 0:
            print(f"  {channel}: {matched_count[channel]} 个")
    
    # 输出到文件
    output_filename = "itvlist.txt"
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        # 写入文件头
        f.write(f"# 电视频道列表 - 生成时间: {datetime.now()}\n")
        f.write(f"# 源地址: {url}\n\n")
        
        # 写入匹配到的频道
        f.write("# ===== 卫视频道 =====\n")
        for channel in matched_channels:
            f.write(channel + '\n')
        
        # 写入苏州地方台
        f.write("\n# ===== 苏州地方台 =====\n")
        for name, url in suzhou_channels:
            f.write(f"{name},{url}\n")
    
    # 验证文件
    if os.path.exists(output_filename):
        with open(output_filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        total_lines = len(content.splitlines())
        print(f"\n文件已生成: {output_filename}")
        print(f"文件大小: {len(content)} 字节")
        print(f"总行数: {total_lines}")
        print(f"卫视频道数: {len(matched_channels)}")
        print(f"苏州台数: {len(suzhou_channels)}")
        
        # 显示部分内容
        print("\n文件内容预览:")
        lines = content.splitlines()
        for i in range(min(10, len(lines))):
            print(f"  {lines[i]}")
    else:
        print("错误：输出文件未创建！")
        create_backup_file()

def create_backup_file():
    """创建备用文件"""
    print("正在创建备用文件...")
    with open("itvlist.txt", "w", encoding="utf-8") as f:
        f.write("# 备用频道列表 - 生成时间: {}\n".format(datetime.now()))
        f.write("CCTV-1综合,http://example.com/cctv1\n")
        f.write("CCTV-2财经,http://example.com/cctv2\n")
        for name, url in suzhou_channels:
            f.write(f"{name},{url}\n")
    print("备用文件已创建")

if __name__ == "__main__":
    filter_channels()
