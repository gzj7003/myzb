import re
import os

# 定义要添加的苏州直播源
suzhou_sources = [
    "苏州新闻综合,https://live-auth.51kandianshi.com/szgd/csztv1.m3u8\n",
    "苏州社会经济,https://live-auth.51kandianshi.com/szgd/csztv2.m3u8\n",
    "苏州文化生活,https://live-auth.51kandianshi.com/szgd/csztv3.m3u8\n",
    "苏州生活资讯,https://live-auth.51kandianshi.com/szgd/csztv5.m3u8\n",
    "苏州4K,https://live-auth.51kandianshi.com/szgd/csztv4k_hd.m3u8\n"
]

# 打开文档并读取所有行
with open('zubo2.txt', 'r', encoding="utf-8") as file:
    lines = file.readlines()

# 使用列表来存储唯一的行的顺序 
unique_lines = [] 
seen_lines = set() 

# 遍历每一行，如果是新的就加入 unique_lines 
for line in lines:
    if line not in seen_lines:
        unique_lines.append(line)
        seen_lines.add(line)

# 添加苏州直播源（确保不重复）
for source in suzhou_sources:
    if source not in seen_lines:
        unique_lines.append(source)
        seen_lines.add(source)

# 将唯一的行写入新的文档 
with open('zubo.txt', 'w', encoding="utf-8") as file:
    file.writelines(unique_lines)

# 删除旧文件
os.remove("zubo2.txt")
