import requests
import sys
import os

# 目标电视台列表
target_channels = [
    "CCTV-1综合", "CCTV-2财经", "CCTV-3综艺", "CCTV-4中文国际", "CCTV-5体育",
    "CCTV-6电影", "CCTV-7国防军事", "CCTV-8电视剧", "CCTV-9纪录", "CCTV-10科教",
    "CCTV-11戏曲", "CCTV-12社会与法", "CCTV-13新闻", "CCTV-14少儿", "CCTV-15音乐",
    "江苏卫视", "浙江卫视", "北京卫视", "兵团卫视", "东方卫视"
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
    
    # 存储匹配到的频道
    matched_channels = []
    
    # 遍历每一行，查找目标频道
    for line in lines:
        if ',' in line:
            try:
                channel_name, channel_url = line.split(',', 1)
                
                # 检查是否是目标频道
                for target in target_channels:
                    # 使用 in 而不是 ==，因为源数据中的频道名可能有额外空格或格式
                    if target in channel_name:
                        matched_channels.append(f"{channel_name.strip()},{channel_url.strip()}")
                        break  # 找到匹配就跳出内层循环
            except ValueError:
                continue  # 跳过格式不正确的行
    
    # 输出到文件
    output_filename = "itvlist.txt"
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        # 写入匹配到的频道
        for channel in matched_channels:
            f.write(channel + '\n')
        
        # 写入苏州地方台
        for name, url in suzhou_channels:
            f.write(f"{name},{url}\n")
    
    print(f"筛选完成！共找到 {len(matched_channels)} 个目标频道")
    print(f"添加了 {len(suzhou_channels)} 个苏州地方台")
    print(f"结果已保存到 {output_filename}")
    
    # 检查文件是否成功创建
    if os.path.exists(output_filename):
        with open(output_filename, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"输出文件大小: {len(content)} 字节，行数: {len(content.splitlines())}")
        # 打印前几行作为示例
        lines = content.splitlines()
        if lines:
            print("文件前5行示例:")
            for i in range(min(5, len(lines))):
                print(f"  {i+1}. {lines[i]}")
    else:
        print("错误：输出文件未创建！")
        sys.exit(1)

if __name__ == "__main__":
    filter_channels()
