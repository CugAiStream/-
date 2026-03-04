#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频下载和编解码工具 - 完整修复版
解决日志输出、进度条显示、B站视频下载等问题
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import threading
import queue
import datetime
import json
import re

class VideoDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("视频下载和编解码工具")
        self.root.geometry("900x700")
        
        # 设置编码
        self.setup_encoding()
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标签页
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 下载标签页
        self.download_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.download_tab, text="视频下载")
        
        # 转换标签页
        self.convert_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.convert_tab, text="视频转换")
        
        # 批量下载标签页
        self.batch_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.batch_tab, text="批量下载")
        
        # 初始化下载标签页
        self.init_download_tab()
        
        # 初始化转换标签页
        self.init_convert_tab()
        
        # 初始化批量下载标签页
        self.init_batch_tab()
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=10)
        
        # 日志文本框
        self.log_text = tk.Text(self.main_frame, height=12, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 队列用于线程间通信
        self.queue = queue.Queue()
        
        # 存储当前正在执行的进程
        self.current_process = None
        
        # 日志文件
        self.log_file = None
        self.init_log_file()
        
        # 定期检查队列
        self.root.after(100, self.check_queue)
        
        # 初始日志
        self.log("=== 视频下载和编解码工具启动 ===")
        self.log(f"日志文件: {self.log_filename}")
    
    def setup_encoding(self):
        """设置编码"""
        import sys
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    
    def init_download_tab(self):
        """初始化下载标签页"""
        # URL输入
        url_frame = ttk.LabelFrame(self.download_tab, text="视频URL", padding="10")
        url_frame.pack(fill=tk.X, pady=5)
        
        self.url_entry = ttk.Entry(url_frame, width=80)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        download_btn = ttk.Button(url_frame, text="下载", command=self.start_download)
        download_btn.pack(side=tk.RIGHT, padx=5)
        
        # 质量选择
        quality_frame = ttk.LabelFrame(self.download_tab, text="视频质量", padding="10")
        quality_frame.pack(fill=tk.X, pady=5)
        
        self.quality_var = tk.StringVar(value="best")
        qualities = ["best", "worst", "1080p", "720p", "480p", "360p"]
        for quality in qualities:
            ttk.Radiobutton(quality_frame, text=quality, value=quality, variable=self.quality_var).pack(side=tk.LEFT, padx=10)
        
        # 输出目录
        output_frame = ttk.LabelFrame(self.download_tab, text="输出目录", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        self.output_dir_entry = ttk.Entry(output_frame, width=60)
        self.output_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.output_dir_entry.insert(0, "downloads")
        
        browse_btn = ttk.Button(output_frame, text="浏览", command=self.browse_output_dir)
        browse_btn.pack(side=tk.RIGHT, padx=5)
        
        # Cookie选项
        cookie_frame = ttk.LabelFrame(self.download_tab, text="Cookie选项", padding="10")
        cookie_frame.pack(fill=tk.X, pady=5)
        
        self.browser_cookie_var = tk.StringVar(value="none")
        browsers = ["none", "chrome", "firefox", "edge"]
        for browser in browsers:
            ttk.Radiobutton(cookie_frame, text=browser, value=browser, variable=self.browser_cookie_var).pack(side=tk.LEFT, padx=10)
        
        # 代理选项
        proxy_frame = ttk.LabelFrame(self.download_tab, text="代理选项", padding="10")
        proxy_frame.pack(fill=tk.X, pady=5)
        
        self.use_proxy_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(proxy_frame, text="使用免费代理", variable=self.use_proxy_var).pack(side=tk.LEFT, padx=10)
    
    def init_convert_tab(self):
        """初始化转换标签页"""
        # 输入文件
        input_frame = ttk.LabelFrame(self.convert_tab, text="输入文件", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        
        self.input_file_entry = ttk.Entry(input_frame, width=60)
        self.input_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_btn = ttk.Button(input_frame, text="浏览", command=self.browse_input_file)
        browse_btn.pack(side=tk.RIGHT, padx=5)
        
        # 输出格式
        format_frame = ttk.LabelFrame(self.convert_tab, text="输出格式", padding="10")
        format_frame.pack(fill=tk.X, pady=5)
        
        self.output_format_var = tk.StringVar(value="mp4")
        formats = ["mp4", "avi", "mkv", "flv", "mov"]
        for fmt in formats:
            ttk.Radiobutton(format_frame, text=fmt, value=fmt, variable=self.output_format_var).pack(side=tk.LEFT, padx=10)
        
        # 输出目录
        output_frame = ttk.LabelFrame(self.convert_tab, text="输出目录", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        self.convert_output_dir_entry = ttk.Entry(output_frame, width=60)
        self.convert_output_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.convert_output_dir_entry.insert(0, "converted")
        
        browse_btn = ttk.Button(output_frame, text="浏览", command=self.browse_convert_output_dir)
        browse_btn.pack(side=tk.RIGHT, padx=5)
        
        # 转换和取消按钮
        button_frame = ttk.Frame(self.convert_tab)
        button_frame.pack(pady=10)
        
        convert_btn = ttk.Button(button_frame, text="转换", command=self.start_convert)
        convert_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ttk.Button(button_frame, text="取消", command=self.cancel_convert)
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def init_batch_tab(self):
        """初始化批量下载标签页"""
        # URL文件
        url_file_frame = ttk.LabelFrame(self.batch_tab, text="URL文件", padding="10")
        url_file_frame.pack(fill=tk.X, pady=5)
        
        self.url_file_entry = ttk.Entry(url_file_frame, width=60)
        self.url_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_btn = ttk.Button(url_file_frame, text="浏览", command=self.browse_url_file)
        browse_btn.pack(side=tk.RIGHT, padx=5)
        
        # 质量选择
        quality_frame = ttk.LabelFrame(self.batch_tab, text="视频质量", padding="10")
        quality_frame.pack(fill=tk.X, pady=5)
        
        self.batch_quality_var = tk.StringVar(value="best")
        qualities = ["best", "worst", "1080p", "720p", "480p", "360p"]
        for quality in qualities:
            ttk.Radiobutton(quality_frame, text=quality, value=quality, variable=self.batch_quality_var).pack(side=tk.LEFT, padx=10)
        
        # 输出目录
        output_frame = ttk.LabelFrame(self.batch_tab, text="输出目录", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        self.batch_output_dir_entry = ttk.Entry(output_frame, width=60)
        self.batch_output_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.batch_output_dir_entry.insert(0, "downloads")
        
        browse_btn = ttk.Button(output_frame, text="浏览", command=self.browse_batch_output_dir)
        browse_btn.pack(side=tk.RIGHT, padx=5)
        
        # Cookie选项
        cookie_frame = ttk.LabelFrame(self.batch_tab, text="Cookie选项", padding="10")
        cookie_frame.pack(fill=tk.X, pady=5)
        
        self.batch_browser_cookie_var = tk.StringVar(value="none")
        browsers = ["none", "chrome", "firefox", "edge"]
        for browser in browsers:
            ttk.Radiobutton(cookie_frame, text=browser, value=browser, variable=self.batch_browser_cookie_var).pack(side=tk.LEFT, padx=10)
        
        # 代理选项
        proxy_frame = ttk.LabelFrame(self.batch_tab, text="代理选项", padding="10")
        proxy_frame.pack(fill=tk.X, pady=5)
        
        self.batch_use_proxy_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(proxy_frame, text="使用免费代理", variable=self.batch_use_proxy_var).pack(side=tk.LEFT, padx=10)
        
        # 批量下载按钮
        batch_download_btn = ttk.Button(self.batch_tab, text="批量下载", command=self.start_batch_download)
        batch_download_btn.pack(pady=10)
    
    def init_log_file(self):
        """初始化日志文件"""
        try:
            # 创建logs目录
            os.makedirs('logs', exist_ok=True)
            # 创建日志文件，使用当前日期时间命名
            self.log_filename = f"logs/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            self.log_file = open(self.log_filename, 'w', encoding='utf-8')
        except Exception as e:
            print(f"创建日志文件失败: {e}")
            self.log_filename = None
            self.log_file = None
    
    def log(self, message):
        """写入日志到文件和GUI"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        
        # 写入日志文件
        if self.log_file:
            try:
                self.log_file.write(log_message + '\n')
                self.log_file.flush()
            except Exception as e:
                print(f"写入日志文件失败: {e}")
        
        # 添加到队列
        self.queue.put(log_message)
    
    def update_log(self, message):
        """更新日志文本框"""
        try:
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.update_idletasks()
        except Exception as e:
            print(f"更新日志显示失败: {e}")
    
    def update_progress(self, value):
        """更新进度条"""
        try:
            self.progress_var.set(value)
            self.root.update_idletasks()
        except Exception as e:
            print(f"更新进度条失败: {e}")
    
    def check_queue(self):
        """检查队列并更新UI"""
        try:
            while not self.queue.empty():
                message = self.queue.get_nowait()
                # 确保消息是字符串类型
                if isinstance(message, str):
                    msg_str = message
                else:
                    # 处理非字符串消息
                    msg_str = str(message)
                
                # 直接更新UI
                self.update_log(msg_str)
        except queue.Empty:
            pass
        except Exception as e:
            # 捕获并显示日志更新时的错误
            error_msg = f"日志更新错误: {e}"
            print(error_msg)
            self.update_log(error_msg)
        
        self.root.after(100, self.check_queue)
    
    def start_download(self):
        """开始下载视频"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入视频URL")
            return
        
        quality = self.quality_var.get()
        output_dir = self.output_dir_entry.get().strip()
        
        # 验证输出目录
        try:
            os.makedirs(output_dir, exist_ok=True)
            # 测试目录是否可写
            test_file = os.path.join(output_dir, 'test_write.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            messagebox.showerror("错误", f"无法创建或写入输出目录: {e}")
            return
        
        # 处理Cookie
        cookie_file = None
        browser_cookie = self.browser_cookie_var.get()
        if browser_cookie != "none":
            cookie_file = self.get_browser_cookies(browser_cookie)
        
        # 处理代理
        proxy = None
        if self.use_proxy_var.get():
            proxy = self.get_free_proxy()
        
        # 启动下载线程
        try:
            self.log("启动下载线程...")
            threading.Thread(target=self.download_video, args=(url, output_dir, quality, cookie_file, proxy), daemon=True).start()
        except Exception as e:
            messagebox.showerror("错误", f"启动下载线程失败: {e}")
    
    def download_video(self, url, output_dir, quality, cookie_file=None, proxy=None):
        """下载视频"""
        self.log("=== 开始下载视频 ===")
        self.log(f"视频URL: {url}")
        self.log(f"输出目录: {output_dir}")
        self.log(f"视频质量: {quality}")
        
        # 检查yt-dlp是否存在
        yt_dlp_path = 'yt-dlp.exe'
        if not os.path.exists(yt_dlp_path):
            yt_dlp_path = './yt-dlp.exe'
            if not os.path.exists(yt_dlp_path):
                self.log("错误: yt-dlp.exe 不存在，请确保它在当前目录中")
                return
        
        # 构建yt-dlp命令
        cmd = [
            yt_dlp_path,
            '--continue',
            '--output', f'{output_dir}/%(title)s.%(ext)s',
            '-i',
            '--no-check-certificate',
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            '--no-playlist',
            '--verbose',
            '--merge-output-format', 'mp4',
            '--ffmpeg-location', '.',
            '--hls-prefer-native',
            '--extractor-args', 'youtube:player-client=web',
            '--progress',
            '--newline',
        ]
        
        # 质量选择
        if quality == 'best':
            if 'bilibili.com' in url:
                cmd.extend(['-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'])
            elif 'iqiyi.com' in url:
                cmd.extend(['-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'])
            else:
                cmd.extend(['-f', 'bestvideo+bestaudio/best'])
        else:
            cmd.extend(['-f', quality])
        
        # 添加Cookie
        if cookie_file and os.path.exists(cookie_file):
            self.log(f"使用Cookie文件: {cookie_file}")
            cmd.extend(['--cookies', cookie_file])
        
        # 添加代理
        if proxy:
            self.log(f"使用代理: {proxy}")
            cmd.extend(['--proxy', proxy])
        
        # 针对爱奇艺的特殊处理
        if 'iqiyi.com' in url:
            self.log("检测到爱奇艺视频，添加特殊处理参数")
            cmd.extend([
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
                '--no-check-certificate',
                '--no-geo-bypass',
                '--force-ipv4',
                '--hls-use-mpegts',
            ])
        
        # 针对哔哩哔哩的特殊处理
        if 'bilibili.com' in url:
            self.log("检测到哔哩哔哩视频，添加特殊处理参数")
            cmd.extend([
                '--referer', 'https://www.bilibili.com/',
                '--add-header', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                '--add-header', 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8',
                '--add-header', 'Origin: https://www.bilibili.com',
                '--add-header', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                '--add-header', 'Cache-Control: max-age=0',
                '--add-header', 'Accept-Encoding: gzip, deflate, br',
                '--extractor-args', 'bilibili:browser=chrome',
                '--no-check-certificate',
                '--no-geo-bypass',
                '--force-ipv4',
            ])
        
        cmd.append(url)
        
        command_str = ' '.join(cmd)
        self.log(f"执行命令: {command_str}")
        
        try:
            # 使用utf-8编码捕获输出
            self.log("开始执行下载命令...")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            
            # 重置进度条
            self.update_progress(0)
            
            for line in process.stdout:
                output_line = line.strip()
                self.log(output_line)
                
                # 解析进度信息
                if '[download]' in output_line and '%' in output_line:
                    try:
                        import re
                        match = re.search(r'\[(download|Extract)\]\s*(\d+\.\d+)%', output_line)
                        if match:
                            progress = float(match.group(2))
                            # 更新进度条
                            self.update_progress(progress)
                    except Exception as e:
                        self.log(f"解析进度失败: {e}")
            
            process.wait()
            
            # 下载完成后重置进度条
            if process.returncode == 0:
                self.update_progress(100)
                self.log("视频下载成功！")
            else:
                self.update_progress(0)
                self.log(f"下载失败，返回码: {process.returncode}")
                
                # 尝试其他方法
                self.log("尝试使用其他方法下载...")
                self.try_alternative_download(url, output_dir, quality, cookie_file, proxy)
                
        except Exception as e:
            self.log(f"下载过程中发生错误: {e}")
            import traceback
            self.log(f"错误详情: {traceback.format_exc()}")
    
    def try_alternative_download(self, url, output_dir, quality, cookie_file=None, proxy=None):
        """尝试其他下载方法"""
        self.log("尝试使用其他格式选择...")
        
        # 检查yt-dlp是否存在
        yt_dlp_path = 'yt-dlp.exe'
        if not os.path.exists(yt_dlp_path):
            yt_dlp_path = './yt-dlp.exe'
        
        # 尝试不同的格式选择
        alternative_formats = [
            'best',
            'bestvideo+bestaudio/best',
            'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'mp4',
        ]
        
        for fmt in alternative_formats:
            self.log(f"尝试格式: {fmt}")
            cmd = [
                yt_dlp_path,
                '--continue',
                '--output', f'{output_dir}/%(title)s.%(ext)s',
                '-i',
                '--no-check-certificate',
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                '--no-playlist',
                '--merge-output-format', 'mp4',
                '--ffmpeg-location', '.',
                '--progress',
                '--newline',
                '-f', fmt,
                url
            ]
            
            if cookie_file and os.path.exists(cookie_file):
                cmd.extend(['--cookies', cookie_file])
            
            if proxy:
                cmd.extend(['--proxy', proxy])
            
            try:
                self.log(f"执行命令: {' '.join(cmd)}")
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
                
                for line in process.stdout:
                    output_line = line.strip()
                    self.log(output_line)
                    
                    # 解析进度信息
                    if '[download]' in output_line and '%' in output_line:
                        try:
                            import re
                            match = re.search(r'\[(download|Extract)\]\s*(\d+\.\d+)%', output_line)
                            if match:
                                progress = float(match.group(2))
                                self.update_progress(progress)
                        except Exception:
                            pass
                
                process.wait()
                
                if process.returncode == 0:
                    self.update_progress(100)
                    self.log("使用替代格式下载成功！")
                    return
                else:
                    self.log(f"格式 {fmt} 失败，返回码: {process.returncode}")
                    
            except Exception as e:
                self.log(f"格式 {fmt} 下载失败: {e}")
        
        self.log("所有替代格式都失败了")
        self.update_progress(0)
    
    def start_convert(self):
        """开始转换视频"""
        input_file = self.input_file_entry.get().strip()
        if not input_file:
            messagebox.showerror("错误", "请选择输入文件")
            return
        
        output_format = self.output_format_var.get()
        output_dir = self.convert_output_dir_entry.get().strip()
        
        # 验证输出目录
        try:
            os.makedirs(output_dir, exist_ok=True)
            # 测试目录是否可写
            test_file = os.path.join(output_dir, 'test_write.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            messagebox.showerror("错误", f"无法创建或写入输出目录: {e}")
            return
        
        # 启动转换线程
        try:
            self.log("启动转换线程...")
            threading.Thread(target=self.convert_video, args=(input_file, output_format, output_dir), daemon=True).start()
        except Exception as e:
            messagebox.showerror("错误", f"启动转换线程失败: {e}")
    
    def convert_video(self, input_file, output_format, output_dir):
        """转换视频"""
        self.log(f"开始转换视频: {input_file}")
        
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_file):
                self.log(f"错误: 输入文件不存在: {input_file}")
                return
            
            # 检查ffmpeg是否存在
            ffmpeg_path = 'ffmpeg.exe'
            if not os.path.exists(ffmpeg_path):
                ffmpeg_path = './ffmpeg.exe'
                if not os.path.exists(ffmpeg_path):
                    self.log("错误: ffmpeg.exe 不存在，请确保它在当前目录中")
                    return
            
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = os.path.join(output_dir, f'{base_name}.{output_format}')
            
            cmd = [
                ffmpeg_path,
                '-i', input_file,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-strict', 'experimental',
                '-y',
                '-progress', 'pipe:1',
                '-hide_banner',
            ]
            
            cmd.append(output_file)
            
            self.log(f"执行命令: {' '.join(cmd)}")
            # 使用utf-8编码捕获输出，避免gbk编码错误
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            # 存储当前进程
            self.current_process = process
            
            # 重置进度条
            self.update_progress(0)
            
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.log(line)
            
            process.wait()
            
            # 转换完成后重置进度条
            if process.returncode == 0:
                self.update_progress(100)
                self.log("视频转换成功！")
                self.log(f"输出文件: {output_file}")
            else:
                self.update_progress(0)
                self.log(f"转换失败，返回码: {process.returncode}")
        except Exception as e:
            self.log(f"转换失败: {e}")
            import traceback
            self.log(f"错误详情: {traceback.format_exc()}")
        finally:
            # 清除当前进程
            self.current_process = None
    
    def cancel_convert(self):
        """取消正在进行的转换操作"""
        if self.current_process:
            try:
                self.log("正在取消转换操作...")
                # 终止进程
                self.current_process.terminate()
                # 等待进程结束
                self.current_process.wait(timeout=5)
                self.log("转换操作已取消")
                # 重置进度条
                self.update_progress(0)
            except Exception as e:
                self.log(f"取消转换失败: {e}")
            finally:
                # 清除当前进程
                self.current_process = None
        else:
            self.log("没有正在进行的转换操作")
    
    def start_batch_download(self):
        """开始批量下载"""
        url_file = self.url_file_entry.get().strip()
        if not url_file:
            messagebox.showerror("错误", "请选择URL文件")
            return
        
        quality = self.batch_quality_var.get()
        output_dir = self.batch_output_dir_entry.get().strip()
        
        # 验证输出目录
        try:
            os.makedirs(output_dir, exist_ok=True)
            # 测试目录是否可写
            test_file = os.path.join(output_dir, 'test_write.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            messagebox.showerror("错误", f"无法创建或写入输出目录: {e}")
            return
        
        # 处理Cookie
        cookie_file = None
        browser_cookie = self.batch_browser_cookie_var.get()
        if browser_cookie != "none":
            cookie_file = self.get_browser_cookies(browser_cookie)
        
        # 处理代理
        proxy = None
        if self.batch_use_proxy_var.get():
            proxy = self.get_free_proxy()
        
        # 读取URL列表
        try:
            with open(url_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            if not urls:
                messagebox.showerror("错误", "URL文件为空")
                return
            
            # 验证URL格式
            valid_urls = []
            for url in urls:
                if url.startswith(('http://', 'https://')):
                    valid_urls.append(url)
                else:
                    self.log(f"警告: 无效的URL格式: {url}")
            
            if not valid_urls:
                messagebox.showerror("错误", "没有有效的URL")
                return
            
            # 启动批量下载线程
            try:
                self.log(f"开始批量下载，共 {len(valid_urls)} 个视频")
                threading.Thread(target=self.batch_download, args=(valid_urls, output_dir, quality, cookie_file, proxy), daemon=True).start()
            except Exception as e:
                messagebox.showerror("错误", f"启动批量下载线程失败: {e}")
        except Exception as e:
            messagebox.showerror("错误", f"读取URL文件失败: {e}")
    
    def batch_download(self, urls, output_dir, quality, cookie_file=None, proxy=None):
        """批量下载视频"""
        self.log(f"开始批量下载，共 {len(urls)} 个视频")
        
        for i, url in enumerate(urls):
            self.log(f"正在下载 ({i+1}/{len(urls)}): {url}")
            self.download_video(url, output_dir, quality, cookie_file, proxy)
        
        self.log("批量下载完成！")
    
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, directory)
    
    def browse_input_file(self):
        """浏览输入文件"""
        file = filedialog.askopenfilename(title="选择输入文件", filetypes=[("视频文件", "*.mp4;*.avi;*.mkv;*.flv;*.mov")])
        if file:
            self.input_file_entry.delete(0, tk.END)
            self.input_file_entry.insert(0, file)
    
    def browse_convert_output_dir(self):
        """浏览转换输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.convert_output_dir_entry.delete(0, tk.END)
            self.convert_output_dir_entry.insert(0, directory)
    
    def browse_url_file(self):
        """浏览URL文件"""
        file = filedialog.askopenfilename(title="选择URL文件", filetypes=[("文本文件", "*.txt")])
        if file:
            self.url_file_entry.delete(0, tk.END)
            self.url_file_entry.insert(0, file)
    
    def browse_batch_output_dir(self):
        """浏览批量下载输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.batch_output_dir_entry.delete(0, tk.END)
            self.batch_output_dir_entry.insert(0, directory)
    
    def get_browser_cookies(self, browser='chrome'):
        """从浏览器导出Cookie"""
        try:
            import browser_cookie3
            
            if browser == 'chrome':
                cookies = browser_cookie3.chrome()
            elif browser == 'firefox':
                cookies = browser_cookie3.firefox()
            elif browser == 'edge':
                cookies = browser_cookie3.edge()
            else:
                self.log(f"不支持的浏览器: {browser}")
                return None
        except PermissionError:
            self.log(f"权限错误: 无法访问{browser}浏览器的Cookie文件")
            self.log("请尝试以下解决方案:")
            self.log("1. 以管理员身份运行程序")
            self.log("2. 关闭所有浏览器窗口后重试")
            self.log("3. 手动导出Cookie文件并使用 --cookie 参数")
            return None
        except Exception as e:
            self.log(f"获取Cookie失败: {e}")
            return None
        
        # 将cookie保存为Netscape格式
        import tempfile
        cookie_file = tempfile.mktemp(suffix='.txt')
        with open(cookie_file, 'w', encoding='utf-8') as f:
            f.write('# Netscape HTTP Cookie File\n')
            for cookie in cookies:
                f.write(f"{cookie.domain}\t{cookie.path == '/'}\t{cookie.path}\t{cookie.secure}\t{cookie.expires}\t{cookie.name}\t{cookie.value}\n")
        
        self.log(f"成功从{browser}浏览器导出Cookie到: {cookie_file}")
        return cookie_file
    
    def get_free_proxy(self):
        """获取免费代理"""
        self.log("获取免费代理...")
        # 这里可以添加实际的代理获取逻辑
        # 目前返回None，表示不使用代理
        self.log("暂不支持免费代理功能")
        return None
    
    def __del__(self):
        """析构函数，关闭日志文件"""
        if self.log_file:
            try:
                self.log_file.close()
            except:
                pass

def main():
    root = tk.Tk()
    app = VideoDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()