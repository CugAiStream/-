import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import threading
import queue
import tempfile
import requests
from lxml import etree
import sys
import datetime
import re

# 设置编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

class VideoDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("视频下载和编解码工具")
        self.root.geometry("900x700")
        
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
        self.root.after(50, self.check_queue)
    
    def init_download_tab(self):
        # URL输入
        url_frame = ttk.LabelFrame(self.download_tab, text="视频URL", padding="10")
        url_frame.pack(fill=tk.X, pady=5)
        
        self.url_entry = ttk.Entry(url_frame, width=80)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 下载按钮
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
        # 转换模式选择
        mode_frame = ttk.LabelFrame(self.convert_tab, text="转换模式", padding="10")
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.convert_mode_var = tk.StringVar(value="single")
        modes = [("单个文件", "single"), ("多个文件", "multiple"), ("目录转换", "directory")]
        for mode_text, mode_value in modes:
            ttk.Radiobutton(mode_frame, text=mode_text, value=mode_value, variable=self.convert_mode_var, command=self.on_convert_mode_change).pack(side=tk.LEFT, padx=10)
        
        # 输入文件/目录框架
        self.input_frame = ttk.LabelFrame(self.convert_tab, text="输入", padding="10")
        self.input_frame.pack(fill=tk.X, pady=5)
        
        # 单个文件输入
        self.single_input_frame = ttk.Frame(self.input_frame)
        self.single_input_frame.pack(fill=tk.X, pady=5)
        
        self.input_file_entry = ttk.Entry(self.single_input_frame, width=60)
        self.input_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        single_browse_btn = ttk.Button(self.single_input_frame, text="浏览", command=self.browse_input_file)
        single_browse_btn.pack(side=tk.RIGHT, padx=5)
        
        # 多个文件输入
        self.multiple_input_frame = ttk.Frame(self.input_frame)
        
        # 目录输入
        self.directory_input_frame = ttk.Frame(self.input_frame)
        
        # 初始显示单个文件输入
        self.on_convert_mode_change()
        
        # 输出格式
        format_frame = ttk.LabelFrame(self.convert_tab, text="输出格式", padding="10")
        format_frame.pack(fill=tk.X, pady=5)
        
        self.output_format_var = tk.StringVar(value="mp4")
        formats = ["mp4", "avi", "mkv", "flv", "mov", "wmv"]
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
        
        # 转换参数
        params_frame = ttk.LabelFrame(self.convert_tab, text="转换参数", padding="10")
        params_frame.pack(fill=tk.X, pady=5)
        
        # 码率
        bitrate_frame = ttk.Frame(params_frame)
        bitrate_frame.pack(fill=tk.X, pady=5)
        ttk.Label(bitrate_frame, text="码率:").pack(side=tk.LEFT, padx=5)
        self.bitrate_var = tk.StringVar(value="")
        bitrate_entry = ttk.Entry(bitrate_frame, textvariable=self.bitrate_var, width=15)
        bitrate_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(bitrate_frame, text="(如: 2M, 5M, 留空为默认)").pack(side=tk.LEFT, padx=5)
        
        # 帧率
        fps_frame = ttk.Frame(params_frame)
        fps_frame.pack(fill=tk.X, pady=5)
        ttk.Label(fps_frame, text="帧率:").pack(side=tk.LEFT, padx=5)
        self.fps_var = tk.StringVar(value="")
        fps_entry = ttk.Entry(fps_frame, textvariable=self.fps_var, width=10)
        fps_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(fps_frame, text="(如: 30, 60, 留空为默认)").pack(side=tk.LEFT, padx=5)
        
        # 分辨率
        resolution_frame = ttk.Frame(params_frame)
        resolution_frame.pack(fill=tk.X, pady=5)
        ttk.Label(resolution_frame, text="分辨率:").pack(side=tk.LEFT, padx=5)
        self.resolution_var = tk.StringVar(value="")
        resolution_options = ["", "4K (3840x2160)", "2K (2560x1440)", "1K (1920x1080)", "全高清 (1920x1080)", "半高清 (1280x720)"]
        resolution_combo = ttk.Combobox(resolution_frame, textvariable=self.resolution_var, values=resolution_options, width=20)
        resolution_combo.pack(side=tk.LEFT, padx=5)
        
        # 转换和取消按钮
        button_frame = ttk.Frame(self.convert_tab)
        button_frame.pack(pady=10)
        
        convert_btn = ttk.Button(button_frame, text="转换", command=self.start_convert)
        convert_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ttk.Button(button_frame, text="取消", command=self.cancel_convert)
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def on_convert_mode_change(self):
        """转换模式改变时的回调"""
        mode = self.convert_mode_var.get()
        
        # 隐藏所有输入框架
        self.single_input_frame.pack_forget()
        self.multiple_input_frame.pack_forget()
        self.directory_input_frame.pack_forget()
        
        # 根据模式显示相应的输入框架
        if mode == "single":
            self.single_input_frame.pack(fill=tk.X, pady=5)
        elif mode == "multiple":
            if self.multiple_input_frame.winfo_ismapped():
                self.multiple_input_frame.pack(fill=tk.X, pady=5)
            else:
                self.multiple_input_frame = ttk.Frame(self.input_frame)
                ttk.Label(self.multiple_input_frame, text="选择多个视频文件:").pack(side=tk.LEFT, padx=5)
                multiple_browse_btn = ttk.Button(self.multiple_input_frame, text="浏览", command=self.browse_multiple_files)
                multiple_browse_btn.pack(side=tk.LEFT, padx=5)
                self.multiple_files_entry = ttk.Entry(self.multiple_input_frame, width=60)
                self.multiple_files_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                self.multiple_input_frame.pack(fill=tk.X, pady=5)
        elif mode == "directory":
            if self.directory_input_frame.winfo_ismapped():
                self.directory_input_frame.pack(fill=tk.X, pady=5)
            else:
                self.directory_input_frame = ttk.Frame(self.input_frame)
                ttk.Label(self.directory_input_frame, text="选择视频目录:").pack(side=tk.LEFT, padx=5)
                directory_browse_btn = ttk.Button(self.directory_input_frame, text="浏览", command=self.browse_directory)
                directory_browse_btn.pack(side=tk.LEFT, padx=5)
                self.directory_entry = ttk.Entry(self.directory_input_frame, width=60)
                self.directory_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                self.directory_input_frame.pack(fill=tk.X, pady=5)
    
    def init_batch_tab(self):
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
            log_filename = f"logs/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            self.log_file = open(log_filename, 'w', encoding='utf-8')
            self.queue.put(f"日志文件已创建: {log_filename}")
        except Exception as e:
            print(f"创建日志文件失败: {e}")
    
    def write_log(self, message):
        """写入日志到文件"""
        if self.log_file:
            try:
                self.log_file.write(message + '\n')
                self.log_file.flush()
            except Exception as e:
                print(f"写入日志文件失败: {e}")
    
    def update_log(self, message):
        """更新日志文本框"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_var.set(value)
        self.root.update_idletasks()
    
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
                
                # 写入日志文件
                self.write_log(msg_str)
                
                # 使用after方法确保在主线程中更新UI
                self.root.after(0, lambda msg=msg_str: self.update_log(msg))
        except queue.Empty:
            pass
        except Exception as e:
            # 捕获并显示日志更新时的错误
            error_msg = f"日志更新错误: {e}"
            print(error_msg)
            self.write_log(error_msg)
        
        self.root.after(50, self.check_queue)
    
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
            threading.Thread(target=self.download_video, args=(url, output_dir, quality, cookie_file, proxy), daemon=True).start()
        except Exception as e:
            messagebox.showerror("错误", f"启动下载线程失败: {e}")
    
    def download_video(self, url, output_dir, quality, cookie_file=None, proxy=None):
        """下载视频"""
        self.queue.put("=" * 50)
        self.queue.put("=== 开始下载视频 ===")
        self.queue.put("=" * 50)
        self.queue.put(f"视频URL: {url}")
        self.queue.put(f"输出目录: {output_dir}")
        self.queue.put(f"视频质量: {quality}")
        
        # 检查yt-dlp是否存在
        yt_dlp_path = 'yt-dlp.exe'
        if not os.path.exists(yt_dlp_path):
            yt_dlp_path = './yt-dlp.exe'
            if not os.path.exists(yt_dlp_path):
                self.queue.put("错误: yt-dlp.exe 不存在，请确保它在当前目录中")
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
            self.queue.put(f"使用Cookie文件: {cookie_file}")
            cmd.extend(['--cookies', cookie_file])
        
        # 添加代理
        if proxy:
            self.queue.put(f"使用代理: {proxy}")
            cmd.extend(['--proxy', proxy])
        
        # 针对爱奇艺的特殊处理
        if 'iqiyi.com' in url:
            self.queue.put("检测到爱奇艺视频，添加特殊处理参数")
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
            self.queue.put("检测到哔哩哔哩视频，添加特殊处理参数")
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
        self.queue.put(f"执行命令: {command_str}")
        
        try:
            # 使用utf-8编码捕获输出
            self.queue.put("开始执行下载命令...")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            
            # 重置进度条
            self.root.after(0, lambda: self.update_progress(0))
            
            for line in process.stdout:
                output_line = line.strip()
                self.queue.put(output_line)
                
                # 解析进度信息
                if '[download]' in output_line and '%' in output_line:
                    try:
                        match = re.search(r'\[(download|Extract)\]\s*(\d+\.\d+)%', output_line)
                        if match:
                            progress = float(match.group(2))
                            # 使用after方法确保在主线程中更新UI
                            self.root.after(0, lambda p=progress: self.update_progress(p))
                    except Exception as e:
                        self.queue.put(f"解析进度失败: {e}")
            
            process.wait()
            
            # 下载完成后重置进度条
            if process.returncode == 0:
                # 使用after方法确保在主线程中更新UI
                self.root.after(0, lambda: self.update_progress(100))
                self.queue.put("=" * 50)
                self.queue.put("视频下载成功！")
                self.queue.put("=" * 50)
            else:
                # 使用after方法确保在主线程中更新UI
                self.root.after(0, lambda: self.update_progress(0))
                self.queue.put(f"下载失败，返回码: {process.returncode}")
        except Exception as e:
            self.queue.put(f"下载过程中发生错误: {e}")
            import traceback
            self.queue.put(f"错误详情: {traceback.format_exc()}")
    
    def start_convert(self):
        """开始转换视频"""
        mode = self.convert_mode_var.get()
        
        if mode == "single":
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
            
            # 获取转换参数
            bitrate = self.bitrate_var.get().strip() or None
            fps_str = self.fps_var.get().strip()
            fps = int(fps_str) if fps_str else None
            resolution = self.resolution_var.get().strip() or None
            
            # 启动转换线程
            try:
                threading.Thread(target=self.convert_video, args=(input_file, output_format, output_dir, bitrate, fps, resolution), daemon=True).start()
            except Exception as e:
                messagebox.showerror("错误", f"启动转换线程失败: {e}")
        
        elif mode == "multiple":
            input_files_str = self.multiple_files_entry.get().strip()
            if not input_files_str or input_files_str == "请选择多个视频文件":
                messagebox.showerror("错误", "请选择多个输入视频文件")
                return
            
            input_files = input_files_str.split()
            
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
            
            # 获取转换参数
            bitrate = self.bitrate_var.get().strip() or None
            fps_str = self.fps_var.get().strip()
            fps = int(fps_str) if fps_str else None
            resolution = self.resolution_var.get().strip() or None
            
            # 启动批量转换线程
            try:
                threading.Thread(target=self.batch_convert_videos, args=(input_files, output_format, output_dir, bitrate, fps, resolution), daemon=True).start()
            except Exception as e:
                messagebox.showerror("错误", f"启动批量转换线程失败: {e}")
        
        elif mode == "directory":
            input_dir = self.directory_entry.get().strip()
            if not input_dir or input_dir == "请选择视频目录":
                messagebox.showerror("错误", "请选择输入视频目录")
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
            
            # 获取转换参数
            bitrate = self.bitrate_var.get().strip() or None
            fps_str = self.fps_var.get().strip()
            fps = int(fps_str) if fps_str else None
            resolution = self.resolution_var.get().strip() or None
            
            # 启动目录转换线程
            try:
                threading.Thread(target=self.convert_directory_videos, args=(input_dir, output_format, output_dir, bitrate, fps, resolution), daemon=True).start()
            except Exception as e:
                messagebox.showerror("错误", f"启动目录转换线程失败: {e}")
    
    def convert_video(self, input_file, output_format, output_dir, bitrate=None, fps=None, resolution=None):
        """转换视频"""
        self.queue.put("=" * 50)
        self.queue.put(f"开始转换视频: {input_file}")
        self.queue.put("=" * 50)
        
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_file):
                self.queue.put(f"错误: 输入文件不存在: {input_file}")
                return
            
            # 检查ffmpeg是否存在
            ffmpeg_path = 'ffmpeg.exe'
            if not os.path.exists(ffmpeg_path):
                ffmpeg_path = './ffmpeg.exe'
                if not os.path.exists(ffmpeg_path):
                    self.queue.put("错误: ffmpeg.exe 不存在，请确保它在当前目录中")
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
            
            # 添加码率参数
            if bitrate:
                cmd.extend(['-b:v', bitrate])
            
            # 添加帧率参数
            if fps:
                cmd.extend(['-r', str(fps)])
            
            # 添加分辨率参数
            if resolution:
                # 解析分辨率选项，提取实际的分辨率值
                match = re.search(r'\((\d+x\d+)\)', resolution)
                if match:
                    actual_resolution = match.group(1)
                    cmd.extend(['-s', actual_resolution])
                else:
                    # 如果是直接输入的分辨率格式，直接使用
                    cmd.extend(['-s', resolution])
            
            cmd.append(output_file)
            
            self.queue.put(f"执行命令: {' '.join(cmd)}")
            # 使用utf-8编码捕获输出，避免gbk编码错误
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            # 存储当前进程
            self.current_process = process
            
            # 重置进度条
            self.root.after(0, lambda: self.update_progress(0))
            
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.queue.put(line)
            
            process.wait()
            
            # 转换完成后重置进度条
            if process.returncode == 0:
                # 使用after方法确保在主线程中更新UI
                self.root.after(0, lambda: self.update_progress(100))
                self.queue.put("=" * 50)
                self.queue.put("视频转换成功！")
                self.queue.put(f"输出文件: {output_file}")
                self.queue.put("=" * 50)
            else:
                # 使用after方法确保在主线程中更新UI
                self.root.after(0, lambda: self.update_progress(0))
                self.queue.put(f"转换失败，返回码: {process.returncode}")
        except Exception as e:
            self.queue.put(f"转换失败: {e}")
            import traceback
            self.queue.put(f"错误详情: {traceback.format_exc()}")
        finally:
            # 清除当前进程
            self.current_process = None
    
    def cancel_convert(self):
        """取消正在进行的转换操作"""
        if self.current_process:
            try:
                self.queue.put("=" * 50)
                self.queue.put("正在取消转换操作...")
                self.queue.put("=" * 50)
                # 终止进程
                self.current_process.terminate()
                # 等待进程结束
                self.current_process.wait(timeout=5)
                self.queue.put("转换操作已取消")
                # 重置进度条
                self.root.after(0, lambda: self.update_progress(0))
            except Exception as e:
                self.queue.put(f"取消转换失败: {e}")
            finally:
                # 清除当前进程
                self.current_process = None
        else:
            self.queue.put("没有正在进行的转换操作")
    
    def batch_convert_videos(self, input_files, output_format, output_dir, bitrate=None, fps=None, resolution=None):
        """批量转换多个视频文件"""
        self.queue.put("=" * 50)
        self.queue.put(f"开始批量转换，共 {len(input_files)} 个视频文件")
        self.queue.put("=" * 50)
        
        for i, input_file in enumerate(input_files):
            self.queue.put(f"正在转换 ({i+1}/{len(input_files)}): {input_file}")
            self.convert_video(input_file, output_format, output_dir, bitrate, fps, resolution)
        
        self.queue.put("=" * 50)
        self.queue.put("批量转换完成！")
        self.queue.put("=" * 50)
    
    def convert_directory_videos(self, input_dir, output_format, output_dir, bitrate=None, fps=None, resolution=None):
        """转换指定目录下的所有视频文件"""
        self.queue.put("=" * 50)
        self.queue.put(f"开始转换目录: {input_dir}")
        self.queue.put("=" * 50)
        
        # 支持的视频格式
        video_extensions = ['.mp4', '.avi', '.mkv', '.wmv', '.flv', '.mov', '.mpg', '.mpeg']
        
        # 收集目录中的所有视频文件
        video_files = []
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in video_extensions):
                    video_files.append(os.path.join(root, file))
        
        if not video_files:
            self.queue.put("目录中没有找到视频文件")
            return
        
        self.queue.put(f"找到 {len(video_files)} 个视频文件")
        
        for i, input_file in enumerate(video_files):
            self.queue.put(f"正在转换 ({i+1}/{len(video_files)}): {input_file}")
            self.convert_video(input_file, output_format, output_dir, bitrate, fps, resolution)
        
        self.queue.put("=" * 50)
        self.queue.put("目录转换完成！")
        self.queue.put("=" * 50)
    
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
                    self.queue.put(f"警告: 无效的URL格式: {url}")
            
            if not valid_urls:
                messagebox.showerror("错误", "没有有效的URL")
                return
            
            # 启动批量下载线程
            try:
                threading.Thread(target=self.batch_download, args=(valid_urls, output_dir, quality, cookie_file, proxy), daemon=True).start()
            except Exception as e:
                messagebox.showerror("错误", f"启动批量下载线程失败: {e}")
        except Exception as e:
            messagebox.showerror("错误", f"读取URL文件失败: {e}")
    
    def batch_download(self, urls, output_dir, quality, cookie_file=None, proxy=None):
        """批量下载视频"""
        self.queue.put("=" * 50)
        self.queue.put(f"开始批量下载，共 {len(urls)} 个视频")
        self.queue.put("=" * 50)
        
        for i, url in enumerate(urls):
            self.queue.put(f"正在下载 ({i+1}/{len(urls)}): {url}")
            self.download_video(url, output_dir, quality, cookie_file, proxy)
        
        self.queue.put("=" * 50)
        self.queue.put("批量下载完成！")
        self.queue.put("=" * 50)
    
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
    
    def browse_multiple_files(self):
        """浏览多个输入文件"""
        files = filedialog.askopenfilenames(title="选择多个视频文件", filetypes=[("视频文件", "*.mp4;*.avi;*.mkv;*.flv;*.mov")])
        if files:
            files_str = ' '.join(files)
            self.multiple_files_entry.delete(0, tk.END)
            self.multiple_files_entry.insert(0, files_str)
    
    def browse_directory(self):
        """浏览输入目录"""
        directory = filedialog.askdirectory(title="选择视频目录")
        if directory:
            self.directory_entry.delete(0, tk.END)
            self.directory_entry.insert(0, directory)
    
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
                self.queue.put(f"不支持的浏览器: {browser}")
                return None
        except PermissionError:
            self.queue.put(f"权限错误: 无法访问{browser}浏览器的Cookie文件")
            self.queue.put("请尝试以下解决方案:")
            self.queue.put("1. 以管理员身份运行程序")
            self.queue.put("2. 关闭所有浏览器窗口后重试")
            self.queue.put("3. 手动导出Cookie文件并使用 --cookie 参数")
            return None
        except Exception as e:
            self.queue.put(f"获取Cookie失败: {e}")
            return None
        
        # 将cookie保存为Netscape格式
        cookie_file = tempfile.mktemp(suffix='.txt')
        with open(cookie_file, 'w', encoding='utf-8') as f:
            f.write('# Netscape HTTP Cookie File\n')
            for cookie in cookies:
                f.write(f"{cookie.domain}\t{cookie.path == '/'}\t{cookie.path}\t{cookie.secure}\t{cookie.expires}\t{cookie.name}\t{cookie.value}\n")
        
        self.queue.put(f"成功从{browser}浏览器导出Cookie到: {cookie_file}")
        return cookie_file
    
    def get_free_proxy(self):
        """获取免费代理"""
        try:
            # 测试代理连接
            response = requests.get('https://www.baidu.com', timeout=5)
            if response.status_code == 200:
                self.queue.put("网络连接正常，不使用代理")
                return None
            else:
                self.queue.put("网络连接异常，无法获取代理")
                return None
        except:
            self.queue.put("网络连接异常，无法获取代理")
            return None

def main():
    root = tk.Tk()
    app = VideoDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()