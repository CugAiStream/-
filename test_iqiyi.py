#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
爱奇艺视频下载测试脚本
用于测试和验证爱奇艺视频下载功能
"""

import subprocess
import sys
import os
import re

def test_iqiyi_download():
    """测试爱奇艺视频下载"""
    print("=== 爱奇艺视频下载测试 ===")
    
    # 测试URL - 使用一个简短的爱奇艺视频
    test_url = "https://www.iqiyi.com/v_19rrif7kxs.html"  # 这是一个示例URL，可能需要更新
    
    print(f"测试URL: {test_url}")
    
    # 构建yt-dlp命令
    cmd = [
        'yt-dlp.exe',
        '--simulate',  # 模拟下载，不实际下载文件
        '--print-json',  # 输出JSON格式的信息
        '--no-check-certificate',
        '--verbose',
        '--referer', 'https://www.iqiyi.com/',
        '--add-header', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        '--add-header', 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8',
        '--add-header', 'Connection: keep-alive',
        '--add-header', 'Upgrade-Insecure-Requests: 1',
        '--add-header', 'X-Requested-With: XMLHttpRequest',
        '--add-header', 'Origin: https://www.iqiyi.com',
        '--add-header', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        '--add-header', 'Cache-Control: max-age=0',
        '--add-header', 'Accept-Encoding: gzip, deflate, br',
        '--add-header', 'DNT: 1',
        '--add-header', 'Sec-Fetch-Dest: document',
        '--add-header', 'Sec-Fetch-Mode: navigate',
        '--add-header', 'Sec-Fetch-Site: same-origin',
        '--add-header', 'Sec-Fetch-User: ?1',
        '--extractor-args', 'iqiyi:browser=chrome',
        '--no-geo-bypass',
        '--force-ipv4',
        '--hls-use-mpegts',
        test_url
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    print("=" * 50)
    
    try:
        # 执行命令
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
        
        stdout, stderr = process.communicate()
        
        print("=== 标准输出 ===")
        print(stdout)
        
        print("=== 标准错误 ===")
        print(stderr)
        
        print(f"=== 返回码: {process.returncode} ===")
        
        # 分析输出
        if process.returncode == 0:
            print("✓ 命令执行成功")
            
            # 检查是否有可用的格式
            if 'formats' in stdout.lower():
                print("✓ 检测到可用的视频格式")
            else:
                print("⚠ 未检测到可用的视频格式")
                
            # 检查是否有音频格式
            if 'audio' in stdout.lower():
                print("✓ 检测到音频格式")
            else:
                print("⚠ 未检测到音频格式")
                
        else:
            print("✗ 命令执行失败")
            
            # 检查错误信息
            if 'unavailable' in stderr.lower():
                print("✗ 视频不可用")
            elif 'geo-restricted' in stderr.lower():
                print("✗ 地理限制")
            elif 'sign in' in stderr.lower():
                print("✗ 需要登录")
            elif 'copyright' in stderr.lower():
                print("✗ 版权问题")
            else:
                print("✗ 未知错误")
                
    except Exception as e:
        print(f"执行过程中发生错误: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

def test_iqiyi_formats():
    """测试爱奇艺可用的格式"""
    print("\n=== 测试爱奇艺格式列表 ===")
    
    # 使用一个已知的爱奇艺视频URL
    test_url = "https://www.iqiyi.com/v_19rrif7kxs.html"  # 需要替换为有效的URL
    
    cmd = [
        'yt-dlp.exe',
        '--list-formats',  # 列出所有可用格式
        '--no-check-certificate',
        '--referer', 'https://www.iqiyi.com/',
        '--add-header', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        '--extractor-args', 'iqiyi:browser=chrome',
        test_url
    ]
    
    print(f"获取格式信息: {test_url}")
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
        stdout, stderr = process.communicate()
        
        print("=== 可用格式 ===")
        print(stdout)
        
        if stderr:
            print("=== 错误信息 ===")
            print(stderr)
            
    except Exception as e:
        print(f"获取格式信息失败: {e}")

def test_iqiyi_direct_download():
    """测试直接下载爱奇艺视频"""
    print("\n=== 测试直接下载爱奇艺视频 ===")
    
    test_url = "https://www.iqiyi.com/v_19rrif7kxs.html"  # 需要替换为有效的URL
    output_dir = "test_downloads"
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    cmd = [
        'yt-dlp.exe',
        '--output', f'{output_dir}/%(title)s.%(ext)s',
        '--merge-output-format', 'mp4',
        '--no-check-certificate',
        '--verbose',
        '--referer', 'https://www.iqiyi.com/',
        '--add-header', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        '--add-header', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        '--add-header', 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8',
        '--add-header', 'Connection: keep-alive',
        '--add-header', 'Upgrade-Insecure-Requests: 1',
        '--add-header', 'X-Requested-With: XMLHttpRequest',
        '--add-header', 'Origin: https://www.iqiyi.com',
        '--add-header', 'Cache-Control: max-age=0',
        '--add-header', 'Accept-Encoding: gzip, deflate, br',
        '--add-header', 'DNT: 1',
        '--add-header', 'Sec-Fetch-Dest: document',
        '--add-header', 'Sec-Fetch-Mode: navigate',
        '--add-header', 'Sec-Fetch-Site: same-origin',
        '--add-header', 'Sec-Fetch-User: ?1',
        '--extractor-args', 'iqiyi:browser=chrome',
        '--no-geo-bypass',
        '--force-ipv4',
        '--hls-use-mpegts',
        '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        test_url
    ]
    
    print(f"尝试下载: {test_url}")
    print(f"输出目录: {output_dir}")
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
        
        # 实时输出
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        return_code = process.poll()
        print(f"下载完成，返回码: {return_code}")
        
        if return_code == 0:
            print("✓ 下载成功")
            # 检查下载的文件
            downloaded_files = os.listdir(output_dir)
            if downloaded_files:
                print(f"下载的文件: {downloaded_files}")
                for file in downloaded_files:
                    file_path = os.path.join(output_dir, file)
                    size = os.path.getsize(file_path)
                    print(f"  {file}: {size} bytes")
            else:
                print("⚠ 没有找到下载的文件")
        else:
            print("✗ 下载失败")
            
    except Exception as e:
        print(f"下载过程中发生错误: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == "__main__":
    print("爱奇艺视频下载测试工具")
    print("=" * 50)
    
    # 检查yt-dlp是否存在
    if not os.path.exists('yt-dlp.exe'):
        print("错误: yt-dlp.exe 不存在，请确保它在当前目录中")
        sys.exit(1)
    
    # 运行测试
    test_iqiyi_download()
    test_iqiyi_formats()
    test_iqiyi_direct_download()
    
    print("\n测试完成！")