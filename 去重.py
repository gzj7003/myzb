import re
import os
from datetime import datetime
import subprocess

# 定义要添加的苏州直播源
suzhou_sources = [
    "苏州新闻综合,https://live-auth.51kandianshi.com/szgd/csztv1.m3u8\n",
    "苏州社会经济,https://live-auth.51kandianshi.com/szgd/csztv2.m3u8\n",
    "苏州文化生活,https://live-auth.51kandianshi.com/szgd/csztv3.m3u8\n",
    "苏州生活资讯,https://live-auth.51kandianshi.com/szgd/csztv5.m3u8\n",
    "苏州4K,https://live-auth.51kandianshi.com/szgd/csztv4k_hd.m3u8\n"
]

# 获取当前时间作为更新时间
update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def git_pull_with_retry():
    try:
        # 先stash本地修改
        subprocess.run(["git", "stash"], check=True)
        # 拉取远程更改
        subprocess.run(["git", "pull", "--rebase"], check=True)
        # 恢复stash的修改
        subprocess.run(["git", "stash", "pop"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Git操作出错: {e}")
        exit(1)

def git_push_with_retry():
    try:
        # 添加所有更改
        subprocess.run(["git", "add", "."], check=True)
        # 提交更改
        subprocess.run(["git", "commit", "-m", f"自动更新组播源 {update_time} [skip ci]"], check=True)
        # 强制推送（使用--force-with-lease更安全）
        subprocess.run(["git", "push", "--force-with-lease"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Git推送出错: {e}")
        exit(1)

# 处理文件去重和更新
def process_files():
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

    # 在文件开头添加更新时间注释
    unique_lines.insert(0, f"# 文件最后更新时间: {update_time}\n")

    # 将唯一的行写入新的文档 
    with open('zubo.txt', 'w', encoding="utf-8") as file:
        file.writelines(unique_lines)

    # 删除旧文件
    if os.path.exists("zubo2.txt"):
        os.remove("zubo2.txt")

    # 在屏幕上显示更新时间
    print("=" * 50)
    print("✅ 文件已更新完成！")
    print(f"🕒 更新时间: {update_time}")
    print("=" * 50)

if __name__ == "__main__":
    # 先同步远程仓库
    git_pull_with_retry()
    
    # 处理文件
    process_files()
    
    # 推送更改
    git_push_with_retry()
