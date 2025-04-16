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
        # 配置Git用户信息（必须先于任何Git操作）
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
        
        # 重置所有本地修改（确保工作区干净）
        subprocess.run(["git", "reset", "--hard"], check=True)
        subprocess.run(["git", "clean", "-fd"], check=True)
        
        # 拉取远程更改（不使用rebase避免复杂冲突）
        subprocess.run(["git", "pull"], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Git操作出错: {e}")
        
        # 尝试备用方案：强制使用远程版本
        try:
            print("尝试强制使用远程版本...")
            subprocess.run(["git", "fetch", "--all"], check=True)
            subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"强制同步失败: {e}")
            exit(1)

def git_push_with_retry():
    try:
        # 确保Git用户信息已配置
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
        
        # 添加所有更改
        subprocess.run(["git", "add", "."], check=True)
        
        # 检查是否有更改需要提交
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True, check=True)
        if not result.stdout.strip():
            print("没有需要提交的更改")
            return
            
        # 提交更改
        subprocess.run(["git", "commit", "-m", f"自动更新组播源 {update_time} [skip ci]"], check=True)
        
        # 尝试普通推送
        try:
            subprocess.run(["git", "push"], check=True)
        except subprocess.CalledProcessError:
            # 如果普通推送失败，尝试强制推送（更安全的方式）
            print("普通推送失败，尝试使用--force-with-lease")
            subprocess.run(["git", "push", "--force-with-lease"], check=True)
            
    except subprocess.CalledProcessError as e:
        print(f"Git推送出错: {e}")
        exit(1)

# 处理文件去重和更新
def process_files():
    try:
        # 检查源文件是否存在
        if not os.path.exists("zubo2.txt"):
            print("警告: zubo2.txt 文件不存在，将创建新文件")
            open("zubo2.txt", "w", encoding="utf-8").close()
        
        # 打开文档并读取所有行
        with open('zubo2.txt', 'r', encoding="utf-8") as file:
            lines = file.readlines()

        # 使用列表来存储唯一的行的顺序 
        unique_lines = [] 
        seen_lines = set() 

        # 遍历每一行，如果是新的就加入 unique_lines 
        for line in lines:
            stripped_line = line.strip()
            if stripped_line and stripped_line not in seen_lines:
                unique_lines.append(line)
                seen_lines.add(stripped_line)

        # 添加苏州直播源（确保不重复）
        for source in suzhou_sources:
            stripped_source = source.strip()
            if stripped_source not in seen_lines:
                unique_lines.append(source)
                seen_lines.add(stripped_source)

        # 在文件开头添加更新时间注释
        unique_lines.insert(0, f"# 文件最后更新时间: {update_time}\n")

        # 将唯一的行写入新的文档 
        with open('zubo.txt', 'w', encoding="utf-8") as file:
            file.writelines(unique_lines)

        # 删除旧文件（如果存在）
        if os.path.exists("zubo2.txt"):
            try:
                os.remove("zubo2.txt")
            except Exception as e:
                print(f"删除旧文件时出错: {e}")

        # 在屏幕上显示更新时间
        print("=" * 50)
        print("✅ 文件已更新完成！")
        print(f"🕒 更新时间: {update_time}")
        print(f"📊 更新条目数: {len(unique_lines)-1}")  # 减去时间注释行
        print("=" * 50)
        
    except Exception as e:
        print(f"文件处理出错: {e}")
        exit(1)

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🔄 开始执行自动更新流程")
        print("=" * 50)
        
        # 先同步远程仓库
        print("\n🔄 正在同步远程仓库...")
        git_pull_with_retry()
        
        # 处理文件
        print("\n🔄 正在处理文件去重和更新...")
        process_files()
        
        # 推送更改
        print("\n🔄 正在推送更改到远程仓库...")
        git_push_with_retry()
        
        print("\n" + "=" * 50)
        print("🎉 所有操作已完成！")
        print("=" * 50)
        
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"❌ 脚本执行出错: {e}")
        print("=" * 50)
        exit(1)
