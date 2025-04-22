import requests
import os
from pathlib import Path

def filter_live_sources():
    # 模板文件中的央视和卫视频道
    template_channels = [
        "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5", "CCTV6", "CCTV7", "CCTV8",
        "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15",
        "湖南卫视", "浙江卫视", "东方卫视", "北京卫视", "江苏卫视", "安徽卫视",
        "重庆卫视", "四川卫视", "天津卫视", "兵团卫视"
    ]
    
    # 苏州地方台直播源
    suzhou_sources = [
        "苏州新闻综合,https://live-auth.51kandianshi.com/szgd/csztv1.m3u8$江苏苏州地方",
        "苏州社会经济,https://live-auth.51kandianshi.com/szgd/csztv2.m3u8$江苏苏州地方",
        "苏州文化生活,https://live-auth.51kandianshi.com/szgd/csztv3.m3u8$江苏苏州地方",
        "苏州生活资讯,https://live-auth.51kandianshi.com/szgd/csztv5.m3u8$江苏苏州地方",
        "苏州4K,https://live-auth.51kandianshi.com/szgd/csztv4k_hd.m3u8$江苏苏州地方"
    ]
    
    # 获取直播源内容（跳过SSL验证）
    url = "https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/zubo.txt"
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        live_sources = response.text.splitlines()
    except Exception as e:
        print(f"获取直播源失败: {e}")
        return
    
    # 筛选所有匹配的线路（不再用break中断）
    filtered_sources = []
    for channel in template_channels:
        for line in live_sources:
            if line.startswith(channel + ","):
                filtered_sources.append(line)  # 保留所有匹配线路
    
    # 添加苏州地方台
    filtered_sources.extend(suzhou_sources)
    
    # 获取项目主目录路径
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / "txt_files"
    output_dir.mkdir(exist_ok=True)
    
    # 写入文件
    filtered_sources = list(dict.fromkeys(filtered_sources))  # 去重且保留顺序
    output_path = output_dir / "Susaw-sa.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(filtered_sources))
    
    print(f"文件已保存到: {output_path}")
    print(f"共找到 {len(filtered_sources)} 条线路（含 {len(suzhou_sources)} 条苏州台）")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    filter_live_sources()
