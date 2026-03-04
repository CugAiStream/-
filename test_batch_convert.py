#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试批量转换功能
"""

import os
import sys
import subprocess

# 设置编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def test_batch_convert():
    """测试批量转换功能"""
    print("开始测试批量转换功能...")
    
    # 测试1: 转换单个文件
    print("\n测试1: 转换单个文件")
    input_file = "downloads/海来阿木《梦底》春节联欢晚会.4K.HDR.全网超高清原画舞台.mp4"
    if os.path.exists(input_file):
        cmd = [
            'python', 'video_downloader.py',
            '--convert',
            '--input-file', input_file,
            '--output-format', 'avi',
            '--output-dir', 'test_output',
            '--bitrate', '1000k',
            '--fps', '30',
            '--resolution', '1280x720'
        ]
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        print(f"返回码: {result.returncode}")
        print(f"输出: {result.stdout}")
        if result.stderr:
            print(f"错误: {result.stderr}")
    else:
        print(f"测试文件不存在: {input_file}")
    
    # 测试2: 批量转换多个文件
    print("\n测试2: 批量转换多个文件")
    test_files = []
    for file in os.listdir('downloads'):
        if file.endswith('.mp4'):
            test_files.append(os.path.join('downloads', file))
            if len(test_files) >= 2:
                break
    
    if test_files:
        cmd = [
            'python', 'video_downloader.py',
            '--batch-convert',
            '--input-files'
        ] + test_files + [
            '--output-format', 'mkv',
            '--output-dir', 'test_output',
            '--bitrate', '500k',
            '--fps', '25'
        ]
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        print(f"返回码: {result.returncode}")
        print(f"输出: {result.stdout}")
        if result.stderr:
            print(f"错误: {result.stderr}")
    else:
        print("没有找到测试文件")
    
    # 测试3: 转换目录下的所有文件
    print("\n测试3: 转换目录下的所有文件")
    input_dir = "downloads"
    if os.path.exists(input_dir):
        cmd = [
            'python', 'video_downloader.py',
            '--dir-convert',
            '--input-dir', input_dir,
            '--output-format', 'wmv',
            '--output-dir', 'test_output',
            '--resolution', '854x480'
        ]
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        print(f"返回码: {result.returncode}")
        print(f"输出: {result.stdout}")
        if result.stderr:
            print(f"错误: {result.stderr}")
    else:
        print(f"测试目录不存在: {input_dir}")
    
    print("\n批量转换功能测试完成！")

if __name__ == '__main__':
    test_batch_convert()
