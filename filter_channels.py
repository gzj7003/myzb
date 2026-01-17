import requests
import sys
import os
import concurrent.futures
import time
from collections import defaultdict
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 目标电视台列表（需要测速的频道）
target_channels = [
    "CCTV-1综合", "CCTV-2财经", "CCTV-3综艺", "CCTV-4中文国际", "CCTV-5体育",
    "CCTV-6电影", "CCTV-7国防军事", "CCTV-8电视剧", "CCTV-9纪录", "CCTV-10科教",
    "CCTV-11戏曲", "CCTV-12社会与法", "CCTV-13新闻", "CCTV-14少儿", "CCTV-15音乐",
    "江苏卫视", "浙江卫视", "北京卫视", "东方卫视"
]

# 苏州地方台（白名单，不测速，直接保留）
suzhou_channels = [
    ("苏州新闻综合", "https://live-auth.51kandianshi.com/szgd/csztv1.m3u8$!白名单-不参与测速-保留结果在前"),
    ("苏州社会经济", "https://live-auth.51kandianshi.com/szgd/csztv2.m3u8$!白名单-不参与测速-保留结果在前"),
    ("苏州文化生活", "https://live-auth.51kandianshi.com/szgd/csztv3.m3u8$!白名单-不参与测速-保留结果在前"),
    ("苏州生活资讯", "https://live-auth.51kandianshi.com/szgd/csztv5.m3u8$!白名单-不参与测速-保留结果在前"),
    ("苏州4K", "https://live-auth.51kandianshi.com/szgd/csztv4k_hd.m3u8$!白名单-不参与测速-保留结果在前")
]

def test_channel_speed(url, timeout=3):
    """
    测试频道URL的速度
    返回：(速度毫秒, 是否成功)
    """
    start_time = time.time()
    try:
        # 只发送HEAD请求以节省时间和带宽
        response = requests.head(url, timeout=timeout, verify=False, allow_redirects=True)
        if response.status_code == 200:
            speed_ms = (time.time() - start_time) * 1000  # 转换为毫秒
            return speed_ms, True
    except:
        pass
    return float('inf'), False

def filter_and_speed_test_channels():
    # 从源获取数据
    url = "https://raw.githubusercontent.com/gzj7003/iptvz/refs/heads/main/zubo.txt"
    
    try:
        print("正在获取源数据...")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.text
        print(f"成功获取数据，数据大小: {len(data)} 字节")
    except requests.exceptions.RequestException as e:
        print(f"获取源数据失败: {e}")
        sys.exit(1)
    
    # 按行分割
    lines = data.strip().split('\n')
    print(f"源数据共有 {len(lines)} 行")
    
    # 存储匹配到的频道，按频道名分组
    channel_sources = defaultdict(list)
    
    # 遍历每一行，查找目标频道
    for line in lines:
        if ',' in line:
            try:
                channel_name, channel_url = line.split(',', 1)
                channel_name = channel_name.strip()
                channel_url = channel_url.strip()
                
                # 检查是否是目标频道
                for target in target_channels:
                    # 使用 in 而不是 ==，因为源数据中的频道名可能有额外空格或格式
                    if target in channel_name:
                        # 清理URL，移除可能的多余部分
                        if '$!' in channel_url:
                            channel_url = channel_url.split('$!')[0]
                        channel_sources[target].append((channel_name, channel_url))
                        break  # 找到匹配就跳出内层循环
            except ValueError:
                continue  # 跳过格式不正确的行
    
    print(f"\n匹配到的频道分组统计:")
    for channel, sources in channel_sources.items():
        print(f"  {channel}: {len(sources)} 个源")
    
    # 对每个频道的源进行测速，并保留前10个最快的
    filtered_channels = []
    
    print("\n开始测速...")
    for channel_name in target_channels:
        if channel_name in channel_sources and channel_sources[channel_name]:
            sources = channel_sources[channel_name]
            print(f"\n测速频道: {channel_name} ({len(sources)}个源)")
            
            # 准备测速数据
            speed_results = []
            
            # 使用线程池并行测速（限制并发数为10）
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # 提交测速任务
                future_to_source = {}
                for name, url in sources:
                    future = executor.submit(test_channel_speed, url)
                    future_to_source[future] = (name, url)
                
                # 收集结果
                for future in concurrent.futures.as_completed(future_to_source):
                    name, url = future_to_source[future]
                    try:
                        speed, success = future.result()
                        if success:
                            speed_results.append((name, url, speed))
                    except Exception as e:
                        # 测速失败，忽略此源
                        pass
            
            # 按速度排序（从快到慢）
            if speed_results:
                speed_results.sort(key=lambda x: x[2])
                
                # 只保留前10个最快的
                top_sources = speed_results[:10]
                
                # 准备最终输出
                if len(top_sources) == 1:
                    # 只有一个源，直接使用
                    final_url = top_sources[0][1]
                else:
                    # 多个源，用竖线分隔
                    urls = [source[1] for source in top_sources]
                    final_url = '|'.join(urls)
                
                filtered_channels.append((channel_name, final_url))
                
                # 打印测速结果
                print(f"  保留 {len(top_sources)} 个最快源:")
                for i, (name, url, speed) in enumerate(top_sources[:3]):  # 只显示前3个
                    print(f"    {i+1}. {speed:.0f}ms")
                if len(top_sources) > 3:
                    print(f"    ... 还有 {len(top_sources)-3} 个源")
            else:
                print(f"  没有有效的源，跳过此频道")
    
    print("\n测速完成!")
    
    # 输出到文件
    output_filename = "itvlist.txt"
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        # 首先写入苏州地方台（白名单，不参与测速）
        for name, url in suzhou_channels:
            f.write(f"{name},{url}\n")
            print(f"添加白名单频道: {name}")
        
        # 然后写入测速后的频道
        for name, url in filtered_channels:
            f.write(f"{name},{url}\n")
    
    print(f"\n筛选完成！")
    print(f"添加了 {len(suzhou_channels)} 个苏州地方台（白名单）")
    print(f"添加了 {len(filtered_channels)} 个测速后的目标频道")
    print(f"每个频道最多保留前10个最快源")
    print(f"结果已保存到 {output_filename}")
    
    # 检查文件是否成功创建
    if os.path.exists(output_filename):
        with open(output_filename, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.splitlines()
        print(f"输出文件大小: {len(content)} 字节，行数: {len(lines)}")
        
        # 打印文件内容示例
        if lines:
            print("\n文件前10行示例:")
            for i in range(min(10, len(lines))):
                print(f"  {i+1}. {lines[i]}")
    else:
        print("错误：输出文件未创建！")
        sys.exit(1)

if __name__ == "__main__":
    filter_and_speed_test_channels()
