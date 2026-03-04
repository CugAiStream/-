import os
import sys
import argparse
import subprocess
import json
import tempfile
from tqdm import tqdm

# 设置编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def get_browser_cookies(browser='chrome'):
    """从浏览器导出Cookie"""
    try:
        # 尝试使用browser_cookie3库获取cookie
        import browser_cookie3
        
        try:
            if browser == 'chrome':
                cookies = browser_cookie3.chrome()
            elif browser == 'firefox':
                cookies = browser_cookie3.firefox()
            elif browser == 'edge':
                cookies = browser_cookie3.edge()
            else:
                print(f"不支持的浏览器: {browser}")
                return None
        except PermissionError:
            print(f"权限错误: 无法访问{browser}浏览器的Cookie文件")
            print("请尝试以下解决方案:")
            print("1. 以管理员身份运行程序")
            print("2. 关闭所有浏览器窗口后重试")
            print("3. 手动导出Cookie文件并使用 --cookie 参数")
            return None
        except Exception as e:
            print(f"获取Cookie失败: {e}")
            return None
        
        # 将cookie保存为Netscape格式
        cookie_file = tempfile.mktemp(suffix='.txt')
        with open(cookie_file, 'w', encoding='utf-8') as f:
            f.write('# Netscape HTTP Cookie File\n')
            for cookie in cookies:
                f.write(f"{cookie.domain}\t{cookie.path == '/'}\t{cookie.path}\t{cookie.secure}\t{cookie.expires}\t{cookie.name}\t{cookie.value}\n")
        
        print(f"成功从{browser}浏览器导出Cookie到: {cookie_file}")
        return cookie_file
    except ImportError:
        print("错误: 缺少browser_cookie3库，请运行 'pip install browser-cookie3' 安装")
        return None
    except Exception as e:
        print(f"导出Cookie失败: {e}")
        return None

def download_video(url, output_dir='downloads', quality='best', cookie_file=None, proxy=None):
    """使用yt-dlp下载视频"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 针对不同网站的特殊参数
    cmd = [
        'yt-dlp.exe',
        '--continue',  # 支持断点续传
        '--output', f'{output_dir}/%(title)s.%(ext)s',
        '-i',  # 忽略错误，继续下载
        '--no-check-certificate',  # 忽略证书错误
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        '--no-playlist',  # 不下载整个播放列表
        '--verbose',  # 详细输出
        '--merge-output-format', 'mp4',  # 确保合并输出为mp4格式
    ]
    
    # 质量选择
    if quality == 'best':
        # 选择最佳质量的视频+音频
        cmd.extend(['-f', 'bestvideo+bestaudio/best'])
    else:
        cmd.extend(['-f', quality])
    
    # 添加Cookie
    if cookie_file and os.path.exists(cookie_file):
        cmd.extend(['--cookies', cookie_file])
    
    # 添加代理
    if proxy:
        cmd.extend(['--proxy', proxy])
    
    # 针对爱奇艺的特殊处理
    if 'iqiyi.com' in url:
        cmd.extend([
            '--referer', 'https://www.iqiyi.com/',
            '--add-header', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            '--add-header', 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8',
            '--add-header', 'Connection: keep-alive',
            '--add-header', 'Upgrade-Insecure-Requests: 1',
            '--add-header', 'X-Requested-With: XMLHttpRequest',
        ])
    
    # 针对哔哩哔哩的特殊处理
    if 'bilibili.com' in url:
        cmd.extend([
            '--referer', 'https://www.bilibili.com/',
            '--add-header', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            '--add-header', 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8',
        ])
    
    cmd.append(url)
    
    print(f"开始下载视频: {url}")
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        # 捕获输出时指定编码为utf-8
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        print(f"返回码: {result.returncode}")
        print(f"标准输出: {result.stdout}")
        print(f"标准错误: {result.stderr}")
        
        if result.returncode == 0:
            print(f"视频下载成功！")
        else:
            print(f"下载失败: {result.stderr}")
            # 尝试使用不同的格式选择
            if 'Can\'t find any video' in result.stderr:
                print("尝试使用不同的格式选择...")
                cmd2 = cmd.copy()
                # 移除原有的格式选择
                if '-f' in cmd2:
                    idx = cmd2.index('-f')
                    cmd2.pop(idx)
                    cmd2.pop(idx)
                # 使用更通用的格式选择
                cmd2.insert(1, '-f')
                cmd2.insert(2, 'bestvideo+bestaudio/best')
                print(f"执行命令: {' '.join(cmd2)}")
                result2 = subprocess.run(cmd2, capture_output=True, text=True, encoding='utf-8', errors='replace')
                print(f"返回码: {result2.returncode}")
                print(f"标准输出: {result2.stdout}")
                print(f"标准错误: {result2.stderr}")
                if result2.returncode == 0:
                    print(f"视频下载成功！")
                else:
                    print(f"再次失败: {result2.stderr}")
                    # 尝试使用--no-check-certificate和其他参数
                    print("尝试使用更高级的参数...")
                    cmd3 = [
                        'yt-dlp.exe',
                        '--no-check-certificate',
                        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        '--referer', 'https://www.iqiyi.com/' if 'iqiyi.com' in url else 'https://www.bilibili.com/',
                        '--output', f'{output_dir}/%(title)s.%(ext)s',
                        '--merge-output-format', 'mp4',
                        '-f', 'bestvideo+bestaudio/best',
                        url
                    ]
                    print(f"执行命令: {' '.join(cmd3)}")
                    result3 = subprocess.run(cmd3, capture_output=True, text=True, encoding='utf-8', errors='replace')
                    print(f"返回码: {result3.returncode}")
                    print(f"标准输出: {result3.stdout}")
                    print(f"标准错误: {result3.stderr}")
                    if result3.returncode == 0:
                        print(f"视频下载成功！")
                    else:
                        print(f"最终失败: {result3.stderr}")
    except Exception as e:
        print(f"下载过程中发生错误: {e}")

def convert_video(input_file, output_format='mp4', output_dir='converted', bitrate=None, fps=None, resolution=None):
    """使用ffmpeg转换视频格式"""
    try:
        if not os.path.exists(input_file):
            print(f"错误: 输入文件不存在: {input_file}")
            return False
        
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_dir, f'{base_name}.{output_format}')
        
        cmd = [
            'ffmpeg.exe',
            '-i', input_file,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-strict', 'experimental',
        ]
        
        # 添加码流参数
        if bitrate:
            cmd.extend(['-b:v', bitrate])
        
        # 添加帧率参数
        if fps:
            cmd.extend(['-r', str(fps)])
        
        # 添加分辨率参数
        if resolution:
            cmd.extend(['-s', resolution])
        
        cmd.append(output_file)
        
        print(f"开始转换视频: {input_file} -> {output_file}")
        print(f"执行命令: {' '.join(cmd)}")
        # 捕获输出时指定编码为utf-8，避免gbk编码错误
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        if result.returncode == 0:
            print(f"视频转换成功！")
            return True
        else:
            print(f"转换失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"转换过程中发生错误: {e}")
        return False

def batch_convert_videos(input_files, output_format='mp4', output_dir='converted', bitrate=None, fps=None, resolution=None):
    """批量转换多个视频文件"""
    for input_file in tqdm(input_files, desc="批量转换进度"):
        convert_video(input_file, output_format, output_dir, bitrate, fps, resolution)

def convert_directory_videos(input_dir, output_format='mp4', output_dir='converted', bitrate=None, fps=None, resolution=None):
    """转换指定目录下的所有视频文件"""
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录不存在: {input_dir}")
        return False
    
    # 支持的视频格式
    video_extensions = ['.mp4', '.avi', '.mkv', '.wmv', '.flv', '.mov', '.mpg', '.mpeg']
    
    # 收集目录中的所有视频文件
    video_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_files.append(os.path.join(root, file))
    
    if not video_files:
        print(f"错误: 目录中没有找到视频文件: {input_dir}")
        return False
    
    print(f"找到 {len(video_files)} 个视频文件")
    batch_convert_videos(video_files, output_format, output_dir, bitrate, fps, resolution)
    return True

def batch_download(urls, output_dir='downloads', quality='best', cookie_file=None, proxy=None):
    """批量下载视频"""
    for url in tqdm(urls, desc="批量下载进度"):
        download_video(url, output_dir, quality, cookie_file, proxy)

def test_proxy(proxy):
    """测试代理是否可用"""
    try:
        import requests
        # 测试代理连接
        response = requests.get('https://www.baidu.com', proxies={'http': proxy, 'https': proxy}, timeout=5)
        if response.status_code == 200:
            return True
        return False
    except:
        return False

def get_free_proxy():
    """获取免费代理"""
    proxy_sources = [
        {
            'url': 'https://www.free-proxy-list.net/',
            'parser': lambda html: [
                f"{'https' if row.xpath('./td[7]/text()')[0] == 'yes' else 'http'}://{row.xpath('./td[1]/text()')[0]}:{row.xpath('./td[2]/text()')[0]}"
                for row in html.xpath('//table[@id="proxylisttable"]/tbody/tr')
            ]
        },
        {
            'url': 'https://free-proxy-list.com/',
            'parser': lambda html: [
                f"{'https' if row.xpath('./td[7]/text()')[0] == 'yes' else 'http'}://{row.xpath('./td[1]/text()')[0]}:{row.xpath('./td[2]/text()')[0]}"
                for row in html.xpath('//table[@class="table table-striped table-bordered"]/tbody/tr')
            ]
        },
        {
            'url': 'https://www.sslproxies.org/',
            'parser': lambda html: [
                f"https://{row.xpath('./td[1]/text()')[0]}:{row.xpath('./td[2]/text()')[0]}"
                for row in html.xpath('//table[@id="proxylisttable"]/tbody/tr')
            ]
        },
        {
            'url': 'https://www.us-proxy.org/',
            'parser': lambda html: [
                f"{'https' if row.xpath('./td[7]/text()')[0] == 'yes' else 'http'}://{row.xpath('./td[1]/text()')[0]}:{row.xpath('./td[2]/text()')[0]}"
                for row in html.xpath('//table[@id="proxylisttable"]/tbody/tr')
            ]
        },
        {
            'url': 'https://www.socks-proxy.net/',
            'parser': lambda html: [
                f"socks5://{row.xpath('./td[1]/text()')[0]}:{row.xpath('./td[2]/text()')[0]}"
                for row in html.xpath('//table[@id="proxylisttable"]/tbody/tr')
            ]
        }
    ]
    
    try:
        import requests
        from lxml import etree
        
        all_proxies = []
        
        # 从所有源获取代理
        for source in proxy_sources:
            try:
                response = requests.get(source['url'], timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                html = etree.HTML(response.text)
                proxies = source['parser'](html)
                all_proxies.extend(proxies)
                print(f"从{source['url']}获取到{len(proxies)}个代理")
            except Exception as e:
                print(f"从{source['url']}获取代理失败: {e}")
        
        # 测试并返回第一个可用的代理
        for proxy in all_proxies[:10]:  # 只测试前10个
            if test_proxy(proxy):
                print(f"找到可用代理: {proxy}")
                return proxy
        
        print("未找到可用的免费代理")
        return None
    except Exception as e:
        print(f"获取免费代理失败: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='视频下载和编解码工具')
    parser.add_argument('--download', action='store_true', help='下载视频')
    parser.add_argument('--convert', action='store_true', help='转换单个视频格式')
    parser.add_argument('--batch-convert', action='store_true', help='批量转换多个视频文件')
    parser.add_argument('--dir-convert', action='store_true', help='转换指定目录下的所有视频文件')
    parser.add_argument('--url', type=str, help='视频URL')
    parser.add_argument('--urls-file', type=str, help='包含多个URL的文件')
    parser.add_argument('--input-file', type=str, help='输入视频文件')
    parser.add_argument('--input-files', type=str, nargs='+', help='多个输入视频文件')
    parser.add_argument('--input-dir', type=str, help='输入视频目录')
    parser.add_argument('--output-format', type=str, default='mp4', help='输出视频格式')
    parser.add_argument('--output-dir', type=str, default='downloads', help='输出目录')
    parser.add_argument('--quality', type=str, default='best', help='视频质量')
    parser.add_argument('--bitrate', type=str, help='输出视频码流（如：1000k）')
    parser.add_argument('--fps', type=int, help='输出视频帧率')
    parser.add_argument('--resolution', type=str, help='输出视频分辨率（如：1920x1080）')
    parser.add_argument('--cookie', type=str, help='Cookie文件路径（用于需要登录的网站）')
    parser.add_argument('--browser-cookie', type=str, choices=['chrome', 'firefox', 'edge'], help='从浏览器导出Cookie')
    parser.add_argument('--proxy', type=str, help='代理服务器地址')
    parser.add_argument('--use-free-proxy', action='store_true', help='使用免费代理（用于国外视频网站）')
    
    args = parser.parse_args()
    
    # 处理Cookie
    cookie_file = args.cookie
    if args.browser_cookie:
        cookie_file = get_browser_cookies(args.browser_cookie)
    
    # 处理代理
    proxy = args.proxy
    if args.use_free_proxy:
        proxy = get_free_proxy()
    
    if args.download:
        if args.urls_file:
            with open(args.urls_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
            batch_download(urls, args.output_dir, args.quality, cookie_file, proxy)
        elif args.url:
            download_video(args.url, args.output_dir, args.quality, cookie_file, proxy)
        else:
            print("错误: 请提供视频URL或URL文件")
    
    elif args.convert:
        if args.input_file:
            convert_video(args.input_file, args.output_format, args.output_dir, args.bitrate, args.fps, args.resolution)
        else:
            print("错误: 请提供输入视频文件")
    
    elif args.batch_convert:
        if args.input_files:
            batch_convert_videos(args.input_files, args.output_format, args.output_dir, args.bitrate, args.fps, args.resolution)
        else:
            print("错误: 请提供多个输入视频文件")
    
    elif args.dir_convert:
        if args.input_dir:
            convert_directory_videos(args.input_dir, args.output_format, args.output_dir, args.bitrate, args.fps, args.resolution)
        else:
            print("错误: 请提供输入视频目录")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()