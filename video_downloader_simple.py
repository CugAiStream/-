import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import threading
import queue
import datetime

class VideoDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("视频下载工具")
        self.root.geometry("800x600")
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # URL输入
        url_frame = ttk.LabelFrame(self.main_frame, text="视频URL", padding="10")
        url_frame.pack(fill=tk.X, pady=5)
        
        self.url_entry = ttk.Entry(url_frame, width=80)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        download_btn = ttk.Button(url_frame, text="下载", command=self.start_download)
        download_btn.pack(side=tk.RIGHT, padx=5)
        
        # 质量选择
        quality_frame = ttk.LabelFrame(self.main_frame, text="视频质量", padding="10")
        quality_frame.pack(fill=tk.X, pady=5)
        
        self.quality_var = tk.StringVar(value="best")
        qualities = ["best", "worst", "1080p", "720p", "480p", "360p"]
        for quality in qualities:
            ttk.Radiobutton(quality_frame, text=quality, value=quality, variable=self.quality_var).pack(side=tk.LEFT, padx=10)
        
        # 输出目录
        output_frame = ttk.LabelFrame(self.main_frame, text="输出目录", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        self.output_dir_entry = ttk.Entry(output_frame, width=60)
        self.output_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.output_dir_entry.insert(0, "downloads")
        
        browse_btn = ttk.Button(output_frame, text="浏览", command=self.browse_output_dir)
        browse_btn.pack(side=tk.RIGHT, padx=5)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=10)
        
        # 日志文本框
        self.log_text = tk.Text(self.main_frame, height=10, wrap=tk.WORD)
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
    
    def init_log_file(self):
        """初始化日志文件"""
        try:
            # 创建logs目录
            os.makedirs('logs', exist_ok=True)
            # 创建日志文件，使用当前日期时间命名
            log_filename = f"logs/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            self.log_file = open(log_filename, 'w', encoding='utf-8')
            self.log(f"日志文件已创建: {log_filename}")
        except Exception as e:
            print(f"创建日志文件失败: {e}")
    
    def log(self, message):
        """写入日志到文件和GUI"""
        # 写入日志文件
        if self.log_file:
            try:
                self.log_file.write(message + '\n')
                self.log_file.flush()
            except Exception as e:
                print(f"写入日志文件失败: {e}")
        
        # 添加到队列
        self.queue.put(message)
    
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
        
        # 启动下载线程
        try:
            threading.Thread(target=self.download_video, args=(url, output_dir, quality), daemon=True).start()
        except Exception as e:
            messagebox.showerror("错误", f"启动下载线程失败: {e}")
    
    def download_video(self, url, output_dir, quality):
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
        except Exception as e:
            self.log(f"下载过程中发生错误: {e}")
            import traceback
            self.log(f"错误详情: {traceback.format_exc()}")
    
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, directory)
    
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