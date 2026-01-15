# test_simple.py - 简单的测试版本
import requests

def main():
    # 先测试能否访问URL
    url = "https://raw.githubusercontent.com/gzj7003/iptvz/refs/heads/main/zubo.txt"
    
    try:
        print("测试访问URL...")
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"内容大小: {len(response.text)} 字节")
        
        # 保存一个简单的测试文件
        with open("itvlist.txt", "w", encoding="utf-8") as f:
            f.write("# 测试频道列表\n")
            f.write("CCTV-1综合,http://test.com/cctv1\n")
            f.write("苏州新闻综合,https://live-auth.51kandianshi.com/szgd/csztv1.m3u8$!白名单-不参与测速-保留结果在前\n")
        
        print("测试文件已创建")
        
    except Exception as e:
        print(f"错误: {e}")
        # 创建一个默认文件
        with open("itvlist.txt", "w", encoding="utf-8") as f:
            f.write("# 默认频道列表\n")
            f.write("CCTV-1综合,http://example.com/cctv1\n")
        print("已创建默认文件")

if __name__ == "__main__":
    main()
