import http.server  # 导入用于创建HTTP服务器的模块
from socketserver import ThreadingMixIn  # 导入支持线程的MixIn类
import os  # 导入用于文件和目录操作的模块
import urllib.parse  # 导入用于解析URL的模块
import shutil  # 导入用于文件操作（如复制、删除）的模块
import datetime  # 导入用于处理日期和时间的模块
import string  # 导入包含字符串常量的模块
import cgi_nowarnings  # 导入处理多部分表单数据的模块。由于cgi模块将在Python 3.13版中移除，故备份此库并移除弃用警告，相关信息：https://docs.python.org/zh-cn/3/library/cgi.html
import time  # 导入用于时间操作的模块
import argparse  # 导入用于解析命令行参数的模块
import base64  # 导入用于Base64编码和解码的模块
import ssl  # 导入 SSL 模块，用于启用 HTTPS
import socket  # 导入socket模块以获取主机名和IP地址
import socket  # 导入socket模块用于网络连接
import psutil  # 导入psutil模块用于获取系统和网络接口信息
import concurrent.futures  # 导入concurrent.futures模块，用于使用线程池
import sys  # 导入sys模块

# 设置命令行参数
parser = argparse.ArgumentParser(description='HTTP/HTTPS服务器')
parser.add_argument('-hp', '--http-port', type=int, default=80, help='HTTP监听的端口号')
parser.add_argument('-hsp', '--https-port', type=int, default=443, help='HTTPS监听的端口号')
parser.add_argument('-u', '--username', type=str, help='基本认证的用户名')
parser.add_argument('-pw', '--password', type=str, help='基本认证的密码')
parser.add_argument('-m', '--mode', type=str, default='both', choices=['http', 'https', 'both'], help='选择服务器模式: http, https, 或 both')
args = parser.parse_args()  # 解析命令行参数

# SVG 图标资源（用于网页上的图标显示）
disk_icon_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg id="b" data-name="图层 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 13.18 5.82" width="16" height="16">
  <g id="c" data-name="图层 1">
    <rect y="0" width="13.18" height="5.82" rx="1.88" ry="1.88" style="fill: #2e2e2e; stroke-width: 0px;"/>
    <rect x=".84" y=".78" width="11.51" height="4.27" rx="1.13" ry="1.13" style="fill: #fff; stroke-width: 0px;"/>
    <path d="M10.59,2.91c0,.41-.34.75-.75.75s-.75-.34-.75-.75.34-.75.75-.75.75.34.75.75Z" style="fill: #2e2e2e; stroke-width: 0px;"/>
  </g>
</svg>'''

file_icon_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg id="b" data-name="图层 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10.46 13.31" width="16" height="16">
  <g id="c" data-name=" 图层 2">
    <g id="d" data-name=" 图层 1-2">
      <g>
        <path d="M7.29.14l3.03,3.03c.09.09.14.2.14.34v8.85c0,.26-.09.49-.28.67s-.41.28-.67.28H.96c-.26,0-.49-.09-.68-.28s-.28-.41-.28-.67V.95c0-.26.09-.49.28-.67s.41-.28.68-.28h6c.13,0,.24.05.34.14h-.01Z" style="fill: #b4acbc; stroke-width: 0px;"/>
        <path d="M6.98.47l3,3.07v8.81c0,.13-.05.24-.14.34s-.2.14-.34.14H.96c-.13,0-.24-.05-.34-.14s-.14-.2-.14-.34V.95c0-.13.05-.24.14-.34s.21-.14.34-.14c0,0,6.02,0,6.02,0Z" style="fill: #f3eef8; stroke-width: 0px;"/>
        <path d="M2.14,9.02h3.8c.07,0,.12.02.17.07s.07.1.07.17-.02.12-.07.17-.1.07-.17.07h-3.8c-.07,0-.12-.02-.17-.07s-.07-.1-.07-.17.02-.12.07-.17.1-.07.17-.07ZM1.91,7.84c0,.07.02.12.07.17.05.05.1.07.17.07h6.18c.07,0,.12-.02.17-.07s.07-.1.07-.17-.02-.12-.07-.17-.1-.07-.17-.07H2.14c-.07,0-.12.02-.17.07s-.07.1-.07.17h0ZM2.14,6.18h6.18c.07,0,.12.02.17.07s.07.1.07.17-.02.12-.07.17-.1.07-.17.07H2.14c-.07,0-.12-.02-.17-.07s-.07-.1-.07-.17.02-.12.07-.17.1-.07.17-.07ZM2.14,4.75c-.07,0-.12.02-.17.07s-.07.1-.07.17.02.12.07.17.1.07.17.07h6.18c.07,0,.12-.02.17-.07s.07-.1.07-.17-.02-.12-.07-.17-.1-.07-.17-.07H2.14Z" style="fill: #998ea4; stroke-width: 0px;"/>
        <path d="M9.98,3.54L6.98.47v2.25c0,.22.08.42.24.57s.35.24.57.24h2.19Z" style="fill: #cdc4d6; stroke-width: 0px;"/>
      </g>
    </g>
  </g>
</svg>'''

folder_icon_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg id="b" data-name="图层 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 13.3 12.35" width="16" height="16">
  <g id="c" data-name=" 图层 2">
    <g id="d" data-name=" 图层 1-2">
      <g>
        <path d="M6.36,1.61c.2.19.44.29.71.29h5.22c.28,0,.52.1.72.3.2.2.29.44.29.71v1.6H0V1.01C0,.73.1.49.3.3c.2-.19.44-.3.71-.3h3.12c.41,0,.76.15,1.05.44l1.18,1.18h0Z" style="fill: #ffb02e; stroke-width: 0px;"/>
        <path d="M12.29,12.35c.28,0,.52-.1.72-.29.2-.2.29-.43.29-.71v-7.02c0-.28-.1-.51-.29-.71-.2-.2-.43-.29-.72-.29H1.01c-.28,0-.51.1-.71.29s-.3.43-.3.71v7.02c0,.28.1.51.3.71.2.2.44.29.71.29h11.29-.01Z" style="fill: #fcd53f; stroke-width: 0px;"/>
      </g>
    </g>
  </g>
</svg>'''

# 定义一个支持多线程的HTTP服务器类
class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    """
    通过继承 ThreadingMixIn 和 http.server.HTTPServer，创建一个支持多线程处理请求的 HTTP 服务器类。
    ThreadingMixIn 提供了将每个请求分发到新线程的能力，而 http.server.HTTPServer 提供了基本的 HTTP 服务器功能。组合这两个类允许服务器并行处理多个请求，提高了处理并发请求的能力。
    该类本身不包含任何自定义方法或属性，它依赖于从 ThreadingMixIn 和 http.server.HTTPServer 继承的功能。这是一种使用 Mixin 来增强类功能的典型示例，无需在子类中添加额外代码。
    """
    pass  # 继承ThreadingMixIn和HTTPServer的功能

# 自定义的HTTP请求处理器
class HttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def format_size(self, size_in_bytes):
        # 将字节大小格式化为可读的文件大小
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.2f} TB"

    def list_directory(self, path):
        # 重写方法以自定义目录列表页面
        if path in ('/', '\\'):
            # 根目录下显示磁盘驱动器
            response_content = '''\
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>磁盘选择</title>
    <style>
        /* 设置整个页面的基本字体和行高，确保文本的可读性 */
        body {
            font-family: Arial, sans-serif; /* 使用无衬线字体提高文本的通用性和可读性 */
            line-height: 1.6; /* 设置行高以增加文本的可读空间 */
        }
        
        /* 移除列表的默认样式，使其更加简洁 */
        ul {
            list-style-type: none; /* 移除列表项前的默认项目符号 */
            padding: 0; /* 移除列表的默认内边距 */
        }
        
        /* 设定列表项的样式，包括内边距、边距和背景色 */
        li {
            padding: 8px; /* 设置列表项的内边距，使内容不会挨着边框 */
            margin-bottom: 10px; /* 设置列表项之间的外边距，保持一定的间距 */
            background-color: #f0f0f0; /* 设置列表项的背景色，提高可读性和美观性 */
            border-radius: 5px; /* 设置边框圆角，使元素看起来更柔和 */
        }
        
        /* 设置链接的样式，包括显示方式、对齐方式、文本装饰和颜色 */
        a {
            display: flex; /* 使用Flex布局，方便里面的内容（如SVG和文本）垂直居中 */
            align-items: center; /* 使Flex项目（SVG和文本）在垂直方向上居中 */
            text-decoration: none; /* 去除链接的下划线，使其看起来更整洁 */
            color: #333; /* 设置链接文字颜色 */
            font-weight: bold; /* 增加字体的粗细，使链接更突出 */
        }
        
        /* 为链接内的SVG图标和文本之间设置右外边距，保持一定的空间 */
        li a svg {
            margin-right: 5px; /* 设置SVG图标右侧的外边距 */
        }
        
        /* 设置链接在鼠标悬停时的颜色变化，提高用户的交互体验 */
        a:hover {
            color: #007bff; /* 鼠标悬停时的链接颜色 */
        }
    </style>
</head>
<body>
    <h2>请选择磁盘驱动器</h2>
    <ul>
'''

            for drive in string.ascii_uppercase:
                if os.path.exists(f'{drive}:\\'):
                    response_content += f'<li><a href="/{drive}:/">{disk_icon_svg} {drive}:/</a></li>'
            response_content += '</ul></body></html>'
        else:
            # 显示指定目录下的文件和文件夹
            try:
                file_list = os.listdir(path)
            except OSError:
                self.send_error(404, "没有找到该目录")
                return None

            file_list.sort(key=lambda a: a.lower())
            response_content = '''\
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>目录列表</title>
    <style>
        /* 定义表格样式，包括边框的合并、宽度、单元格的内边距、文本对齐方式和单元格下边框样式 */
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        /* 设置链接的默认样式，去除下划线 */
        a {
            display: flex; /* 使用Flex布局，方便里面的内容（如SVG和文本）垂直居中 */
            align-items: center; /* 使Flex项目（SVG和文本）在垂直方向上居中 */
            text-decoration: none;
        }
        /* 为链接内的SVG图标和文本之间设置右外边距，保持一定的空间 */
        a svg {
            margin-right: 5px; /* 在SVG图标和文本之间添加一些间距 */
        }
        /* 上传状态信息的样式，包括上边距的设置 */
        #uploadStatus {
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <h2>当前路径: ''' + path + '''</h2>
    <button onclick="document.getElementById('fileInput').click()">上传文件</button>
    <input id="fileInput" type="file" multiple style="display:none" onchange="uploadFile()"/>
    <button onclick="document.getElementById('folderInput').click()">上传文件夹</button>
    <input id="folderInput" type="file" webkitdirectory style="display:none" onchange="uploadFolder()"/>
    <button onclick="promptNewFolder()">新建文件夹</button>
    <div id="uploadStatus"></div>
    <hr>
'''

            if path in [f'{drive}:\\' for drive in string.ascii_uppercase if os.path.exists(f'{drive}:\\')]:  # 如果当前目录是磁盘根目录
                response_content += '<a href="/">🔙磁盘选择界面</a><br><br>'  # 添加返回磁盘选择界面的链接
            elif os.path.abspath(path) != os.path.abspath('/'):  # 如果当前目录不是服务器根目录
                parent_dir = os.path.abspath(os.path.join(path, '..'))  # 获取上级目录的绝对路径
                parent_dir_link = urllib.parse.quote(parent_dir.replace(os.getcwd(), '').replace('\\', '/').strip('/'))  # 转换为相对路径并进行URL编码
                response_content += f'<a href="/{parent_dir_link}">🔙上级目录</a><br><br>'  # 添加返回上级目录的链接


            # 内联JavaScript用于处理文件/文件夹的上传、删除和重命名操作
            response_content += """
            <script>
            function handleResponse(response, successMessage, failureMessage) {
                response.text().then(text => {
                    if (response.ok) {
                        document.getElementById('uploadStatus').innerHTML = '<p>' + successMessage + '</p><pre>' + text + '</pre>';
                    } else {
                        document.getElementById('uploadStatus').innerHTML = '<p>' + failureMessage + '</p><pre>' + text + '</pre>';
                    }
                    // 设置延时3秒刷新页面
                    setTimeout(function() {
                        window.location.reload();
                    }, 3000);
                });
            }

            function confirmDelete(path, filename) {
                if (confirm('确定要删除 "' + decodeURIComponent(filename) + '" 这个文件(夹)吗？（⚠此操作不可逆！）')) {
                    var data = new FormData();
                    data.append('delete', path);
                    fetch('.', {
                        method: 'POST',
                        body: data,
                    }).then(response => handleResponse(response, '删除操作成功！（页面将在3秒后刷新）', '删除操作失败！（页面将在3秒后刷新）'));
                }
            }

            function promptRename(path, filename) {
                var newName = prompt('请输入 "' + decodeURIComponent(filename) + '" 的新名称（包括扩展名）                                            💡提示：您可以输入路径分隔符以实现移动操作（以"copy:"开头则为复制）（⚠如果目标路径存在与自身相同的项目会进行覆盖操作）:', decodeURIComponent(filename));
                if (newName && newName.trim() !== '') {
                    var data = new FormData();
                    data.append('rename', path);
                    data.append('newName', newName);
                    fetch('.', {
                        method: 'POST',
                        body: data,
                    }).then(response => handleResponse(response, '操作成功！（页面将在3秒后刷新）', '操作失败！（页面将在3秒后刷新）'));
                }
            }

            function uploadFile() {
                var input = document.getElementById('fileInput');
                var data = new FormData();
                for (var i = 0; i < input.files.length; i++) {
                    data.append('file', input.files[i]); // 使用相同的键名 "file"，但每个文件都是独立的部分
                }

                fetch('.', {
                    method: 'POST',
                    body: data,
                }).then(response => handleResponse(response, '文件上传成功！（页面将在3秒后刷新）', '文件上传失败！（页面将在3秒后刷新）'));
            }

            function uploadFolder() {
                var input = document.getElementById('folderInput');
                var data = new FormData();
                for (var i = 0; i < input.files.length; i++) {
                    data.append('folder', input.files[i]);
                }
                fetch('.', {
                    method: 'POST',
                    body: data,
                }).then(response => handleResponse(response, '文件夹上传成功！（页面将在3秒后刷新）', '文件夹上传失败！（页面将在3秒后刷新）'));
            }

            function promptNewFolder() {
                var folderName = prompt('请输入新文件夹的名称:');
                if (folderName && folderName.trim() !== '') {
                    var data = new FormData();
                    data.append('newFolder', folderName);
                    fetch('.', {
                        method: 'POST',
                        body: data,
                    }).then(response => handleResponse(response, '新文件夹创建成功！（页面将在3秒后刷新）', '新文件夹创建失败！（页面将在3秒后刷新）'));
                }
            }
            </script>
            """

            # 为文件和目录生成表格
            response_content += '<table><tr><th>名称</th><th>修改日期</th><th>创建日期</th><th>大小</th><th>操作</th></tr>'

            for filename in file_list:  # 遍历目录下的每个文件和文件夹
                full_path = os.path.join(path, filename)  # 获取完整路径
                display_name = filename  # 显示名称
                link_target = urllib.parse.quote(filename)  # URL编码的文件名，用于链接
                file_size = 'N/A'  # 默认文件大小
                modification_time = 'N/A'  # 默认修改时间

                if os.path.isdir(full_path):  # 检查是否为目录
                    folder_icon = f"{folder_icon_svg} "  # 定义文件夹图标
                    link_target += "/"
                    display_link = f'<a href="{link_target}">{folder_icon}{display_name}</a>' # 使用 folder_icon 变量在显示名称前添加文件夹图标
                else:  # 如果是文件，尝试获取大小和修改时间
                    file_icon = f"{file_icon_svg} "  # 定义文件图标
                    display_link = f'<a href="{link_target}">{file_icon}{display_name}</a>' # 使用 file_icon 变量在显示名称前添加文件图标
                    try:
                        file_size = self.format_size(os.path.getsize(full_path))
                    except OSError:
                        file_size = '不可访问'

                try:
                    # 获取并格式化修改日期
                    modification_time = datetime.datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    modification_time = '未知'

                try:
                    # 获取并格式化创建日期
                    creation_time = datetime.datetime.fromtimestamp(os.path.getctime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    creation_time = '未知'

                # 为每个文件/文件夹创建删除和重命名按钮
                delete_button = f'<button onclick="confirmDelete(\'{urllib.parse.quote(full_path)}\', \'{urllib.parse.quote(filename)}\')">删除</button>'
                rename_button = f'<button onclick="promptRename(\'{urllib.parse.quote(full_path)}\', \'{urllib.parse.quote(filename)}\')">重命名</button>'
                response_content += f'<tr><td>{display_link}</td><td>{modification_time}</td><td>{creation_time}</td><td>{file_size}</td><td>{delete_button} | {rename_button}</td></tr>'

            response_content += '</table><hr></body></html>'
        self.send_response(200)  # 发送HTTP响应
        self.send_header("Content-type", "text/html; charset=utf-8")  # 设置内容类型为HTML
        self.end_headers()  # 结束HTTP头
        self.wfile.write(response_content.encode('utf-8'))  # 写入响应内容

    def do_GET(self):
        # 调用基类方法进行基本的 GET 处理
        if not self.authenticate():
            return

        # 检查是否有 Range 头部
        range_header = self.headers.get('Range')
        if range_header:
            try:
                # 尝试处理范围请求
                self.handle_partial_content(range_header)
            except Exception as e:
                # 如果处理过程中发生错误，返回 500
                self.send_error(500, "Server Error: %s" % str(e))
        else:
            # 如果没有 Range 头部，正常处理 GET 请求
            super().do_GET()

    def handle_partial_content(self, range_header):
        # 处理部分内容请求，支持文件的续传功能
        try:
            # 解析Range头，支持起始和结束字节
            range_value = range_header.strip().split('=')[1]  # 将Range头部分割，获取范围值
            # 分割Range头部的值，并将起始和结束字节转换为整数，如果未指定结束字节，则为None
            start_byte, end_byte = map(
                lambda x: int(x) if x else None,  # 如果x非空，转换为整数；否则为None
                range_value.split('-')  # 按照"-"分割Range头部的值，得到起始和结束字节的字符串
            )


            # 确定请求文件的路径
            path = self.translate_path(self.path)  # 将URL路径转换为文件系统路径
            # 获取文件总大小
            file_size = os.path.getsize(path)  # 获取文件的总字节数

            # 如果没有指定结束字节，它会被设置为文件的最后一个字节的索引（file_size - 1）。这确保了即使在请求中只指定了起始字节，服务器也能正确地返回从起始字节到文件末尾的内容。
            if end_byte is None or end_byte >= file_size:
                end_byte = file_size - 1

            # 检查范围的有效性
            if start_byte is None or start_byte > end_byte or start_byte >= file_size:
                # 范围无效，发送 416 Range Not Satisfiable
                self.send_error(416, 'Requested Range Not Satisfiable')
                return

            # 以二进制模式打开请求的文件
            with open(path, 'rb') as f:
                # 将文件指针移动到请求的起始位置
                f.seek(start_byte)
                # 发送206 Partial Content响应状态码
                self.send_response(206)
                # 设置响应头部
                self.send_header("Content-type", self.guess_type(path))  # 猜测并设置文件的MIME类型
                self.send_header("Accept-Ranges", "bytes")  # 表明服务器接受范围请求
                # 设置Content-Range头部，格式为"字节 起始字节-结束字节/文件总大小"
                self.send_header("Content-Range", f"bytes {start_byte}-{end_byte}/{file_size}")
                # 设置Content-Length头部为请求范围的长度
                self.send_header("Content-Length", str(end_byte - start_byte + 1))
                self.end_headers()  # 结束响应头部的发送

                # 初始化剩余字节数
                remaining_bytes = end_byte - start_byte + 1
                # 循环读取和发送文件的指定范围内容
                while remaining_bytes > 0:
                    # 读取文件的下一块
                    block_size = min(65536, remaining_bytes)  # 选择较小的值避免过大的内存使用，65536字节（64KB）
                    data = f.read(block_size)  # 从文件中读取数据
                    if not data:  # 如果没有读取到数据，表示文件已经读取完毕
                        break  # 文件读取完毕
                    try:
                        self.wfile.write(data)  # 发送数据块
                        remaining_bytes -= len(data)  # 更新剩余字节数
                    except (BrokenPipeError, ConnectionResetError, ssl.SSLError) as e:
                        # 捕获可能发生的异常：
                        # BrokenPipeError: 客户端关闭了连接
                        # ConnectionResetError: 连接被客户端重置
                        # ssl.SSLError: SSL层面发生的错误，例如数据长度错误或协议违规

                        # 打印错误信息，实际生产环境中可能需要将这些信息记录到日志
                        print("客户端过早关闭连接或发生其他SSL错误：", e)
                        break  # 退出循环，停止发送数据

        except Exception as e:
            # 处理过程中出现异常，发送500服务器错误
            self.send_error(500, f"Server Error: {e}")
            # raise e

    def do_POST(self):
        # 处理POST请求，首先进行认证
        if not self.authenticate():
            return

        start_time = time.time()  # 记录操作开始时间
        form = cgi_nowarnings.FieldStorage(  # 使用cgi模块解析POST数据
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type'],}
        )

        upload_details = []  # 存储操作详情

        # 处理文件上传
        if 'file' in form:  # 检查表单中是否有文件数据
            file_items = form['file']  # 获取文件数据
            if not isinstance(file_items, list):  # 检查"file_items"是否是一个列表，如果不是，那么只上传了一个文件
                file_items = [file_items]  # 如果只上传了一个文件，则将其转换为列表
            for item in file_items:
                if item.filename:  # 如果文件名存在
                    filepath = os.path.join(self.translate_path(self.path), item.filename)  # 构造文件路径
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)  # 创建文件所在目录

                    with open(filepath, "wb") as f:  # 以二进制写模式打开文件
                        f.write(item.file.read())  # 写入文件数据
                    upload_details.append(f'文件 "{item.filename}" 上传成功。')  # 添加操作详情
            self.send_response(200)  # 发送HTTP响应

        # 处理文件夹上传
        if 'folder' in form:  # 检查表单中是否有文件夹数据
            items = form['folder']  # 获取文件夹数据
            if not isinstance(items, list):  # 如果数据不是列表类型（单个文件情况）
                items = [items]  # 将其转换为列表

            for item in items:  # 遍历所有文件
                if item.filename:  # 如果文件名存在
                    filepath = os.path.join(self.translate_path(self.path), item.filename)  # 构造文件路径
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)  # 创建文件所在目录

                    with open(filepath, "wb") as f:  # 以二进制写模式打开文件
                        f.write(item.file.read())  # 写入文件数据
                    upload_details.append(f'文件 "{item.filename}" 上传成功。')  # 添加操作详情
            self.send_response(200)  # 发送HTTP响应

        # 处理删除操作
        if 'delete' in form:  # 检查表单中是否有删除请求
            file_path = urllib.parse.unquote(form.getvalue('delete'))  # 获取要删除的文件路径，并进行URL解码
            try:
                if os.path.isdir(file_path):  # 如果是目录
                    shutil.rmtree(file_path)  # 删除目录及其所有内容
                else:
                    os.remove(file_path)  # 删除文件
                upload_details.append(f'文件（夹） "{os.path.basename(file_path)}" 已被删除。')  # 添加操作详情
                self.send_response(200)  # 发送HTTP响应
            except OSError as e:
                upload_details.append(f'删除文件 "{os.path.basename(file_path)}" 失败: {e}。')  # 添加操作失败详情
                self.send_response(500)  # 发送HTTP响应

        # 处理重命名、复制、移动操作
        if 'rename' in form and 'newName' in form:
            old_path = urllib.parse.unquote(form.getvalue('rename'))  # 获取原文件路径
            new_name_input = form.getvalue('newName').strip()  # 获取用户输入的新文件名，并去除首尾空格

            if new_name_input.lower().startswith("copy:"):
                # 从用户输入中提取目标路径，并去除 "copy:" 前缀和首尾空格
                target_path = new_name_input[5:].strip()
                target_full_path = os.path.join(os.path.dirname(old_path), target_path.replace('/', os.sep).replace('\\', os.sep))

                # 检查源路径和目标路径是否相同
                if os.path.normpath(old_path) == os.path.normpath(target_full_path):
                    upload_details.append(f'复制失败：不能将文件（夹）复制到自己的路径。')
                    self.send_response(400)  # 发送400 Bad Request响应
                else:
                    # 确保目标路径的父文件夹存在
                    target_dir = os.path.dirname(target_full_path)
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)  # 如果目标路径的父文件夹不存在，则创建

                    try:
                        if os.path.isdir(old_path):
                            # 复制文件夹，包括所有子文件夹和文件
                            if os.path.exists(target_full_path):
                                shutil.rmtree(target_full_path)  # 如果目标文件夹存在，先删除
                            shutil.copytree(old_path, target_full_path, copy_function=shutil.copy2)  # 使用copy2来保留元数据
                        else:
                            # 复制文件
                            if os.path.exists(target_full_path):
                                os.remove(target_full_path)  # 如果目标文件存在，先删除
                            shutil.copy2(old_path, target_full_path)  # 使用copy2来保留元数据
                        upload_details.append(f'复制成功："{old_path}" 到 "{target_full_path}"。')
                        self.send_response(200)
                    except OSError as e:
                        upload_details.append(f'复制失败：{e}。')
                        self.send_response(500)
            else:
                new_path = os.path.join(os.path.dirname(old_path), new_name_input.replace('/', os.sep).replace('\\', os.sep))
                # 检查源路径和目标路径是否相同
                if os.path.normpath(old_path) == os.path.normpath(new_path):
                    upload_details.append(f'移动失败：不能将文件（夹）移动到自己的路径。')
                    self.send_response(400)  # 发送400 Bad Request响应
                else:
                    try:
                        if os.sep in new_name_input or ('/' in new_name_input and os.sep != '/'):
                            # 移动文件或文件夹
                            if os.path.exists(new_path):
                                if os.path.isdir(old_path):
                                    shutil.rmtree(new_path)  # 如果目标是文件夹，则删除
                                else:
                                    os.remove(new_path)  # 如果目标是文件，则删除
                            shutil.move(old_path, new_path)
                            upload_details.append(f'移动成功："{old_path}" 到 "{new_path}"。')
                        else:
                            # 重命名文件或文件夹
                            os.rename(old_path, new_path)
                            upload_details.append(f'重命名成功："{old_path}" 到 "{new_path}"。')
                        self.send_response(200)
                    except OSError as e:
                        upload_details.append(f'操作失败：{e}。')
                        self.send_response(500)

        # 处理新建文件夹请求
        if 'newFolder' in form:
            folder_name = form.getvalue('newFolder')  # 获取新文件夹的名称
            folder_path = os.path.join(self.translate_path(self.path), folder_name)  # 构造新文件夹的完整路径
            try:
                os.makedirs(folder_path, exist_ok=True)  # 创建新文件夹，包括所有必需的父目录
                upload_details.append(f'新文件夹 "{folder_name}" 创建成功。')  # 添加操作详情
                self.send_response(200)  # 发送HTTP响应
            except Exception as e:
                upload_details.append(f'新文件夹 "{folder_name}" 创建失败：{e}')  # 添加操作失败的详情
                self.send_response(500)  # 发送500内部服务器错误响应

        end_time = time.time()  # 记录操作结束时间
        upload_time = end_time - start_time  # 计算操作用时
        upload_details.append(f"操作总用时: {upload_time:.5f} 秒。")  # 添加操作总用时详情


        self.send_header("Content-type", "text/plain; charset=utf-8")  # 设置内容类型为纯文本
        self.end_headers()  # 结束HTTP头
        response_text = "\n".join(upload_details)  # 将操作详情拼接成文本
        self.wfile.write(response_text.encode('utf-8'))  # 写入响应内容

    def translate_path(self, path):
        # 重写路径转换方法，以正确处理根目录和磁盘路径，并确保对路径进行解码
        decoded_path = urllib.parse.unquote(path)  # 对路径进行URL解码
        decoded_path = decoded_path.strip('/')  # 移除路径两端的斜杠
        if decoded_path and ':' in decoded_path:  # 如果路径包含磁盘符
            decoded_path = decoded_path.replace(':', ':\\')  # 替换为Windows风格的磁盘符表示
            return os.path.abspath(decoded_path)  # 返回绝对路径
        elif decoded_path == '':  # 如果路径为空
            return '/'  # 返回根目录
        else:
            return super().translate_path('/' + decoded_path)  # 调用父类方法处理其他情况

    def authenticate(self):
        # 基本认证实现
        if args.username and args.password:  # 如果设置了用户名和密码
            if self.headers.get('Authorization') is None:  # 如果请求中没有认证信息
                self.send_response(401)  # 发送401响应
                self.send_header('WWW-Authenticate', 'Basic realm=\"Test\"')  # 要求基本认证
                self.send_header('Content-type', 'text/html')  # 设置内容类型为HTML
                self.end_headers()  # 结束HTTP头
                self.wfile.write(b'Unauthorized')  # 返回未认证信息
                return False

            auth_header = self.headers.get('Authorization')  # 获取认证头
            auth_decoded = base64.b64decode(auth_header.split(' ')[1]).decode('utf-8')  # 解码认证信息
            username, password = auth_decoded.split(':')  # 分割用户名和密码
            if username == args.username and password == args.password:  # 如果用户名和密码匹配
                return True  # 认证成功
            else:
                self.send_response(403)  # 发送403响应
                self.end_headers()  # 结束HTTP头
                self.wfile.write(b'Forbidden')  # 返回禁止访问信息
                return False
        return True  # 如果没有设置用户名和密码，则不进行认证


# 定义一个函数get_active_ip_addresses，用于获取活跃的网络接口的IP地址
def get_active_ip_addresses():
    # 初始化一个字典，用于存储活跃的网络接口及其对应的IP地址
    active_ip_addresses = {}
    # 遍历通过psutil.net_if_addrs()获取的所有网络接口及其地址信息
    for interface, addrs in psutil.net_if_addrs().items():
        # 判断网络接口是否在psutil.net_if_stats()返回的统计信息中，并且该网络接口的状态是活跃的
        if interface in psutil.net_if_stats() and psutil.net_if_stats()[interface].isup:
            # 遍历当前网络接口的所有地址信息
            for addr in addrs:
                # 判断地址类型是否为IPv4
                if addr.family == socket.AF_INET:
                    # 将活跃的网络接口及其IPv4地址存储到字典中
                    active_ip_addresses[interface] = addr.address
    # 返回存储活跃网络接口及其IP地址的字典
    return active_ip_addresses


def run_http_server():
    """启动HTTP服务器的函数。"""
    server_address = ('', args.http_port)  # 设置服务器地址和端口
    try:
        httpd = ThreadedHTTPServer(server_address, HttpRequestHandler)  # 创建服务器实例

        print(f'HTTP 服务器现已启动在：http://localhost:{args.http_port}')  # 打印启动信息
        print()

        # 启动服务器，无限期地等待和处理请求。serve_forever 方法是一个阻塞调用，它将持续运行，直到程序被明确停止。
        # 在此期间，服务器将监听指定的端口，接收客户端的连接请求，并根据请求使用 HttpRequestHandler 来处理这些请求。
        httpd.serve_forever()  # 启动服务器，永久运行
    except PermissionError as e:  # 捕获 PermissionError
        print(f"在启动HTTP服务器时发生错误，可能的原因有:\n  1、没有足够的权限监听端口 {args.http_port}。请尝试使用更高的权限运行程序，或使用 1024 以上的端口。\n  2、端口 {args.http_port} 已被占用。请尝试使用不同的端口。\n")


def run_https_server():
    """启动HTTPS服务器的函数。"""
    server_address = ('', args.https_port)  # 设置服务器地址和端口
    try:
        # 尝试创建服务器实例。这里会尝试绑定指定的端口，
        # 如果端口已被占用，将抛出 OSError 异常
        httpd = ThreadedHTTPServer(server_address, HttpRequestHandler)  # 创建服务器实例

        # 创建 SSLContext 对象，用于封装 SSL/TLS 安全设置。
        # ssl.PROTOCOL_TLS_SERVER 是一个选择最新版本和最安全的 TLS 协议的枚举值。
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        # 如果程序被打包成了单文件的可执行文件，`sys.executable`将指向该可执行文件
        # 否则，它将指向 脚本 文件
        if getattr(sys, 'frozen', False):
            # 如果程序是被打包的，则返回可执行文件所在目录
            base_dir = os.path.dirname(sys.executable)
        else:
            # 如果程序是以脚本形式运行的，则返回脚本所在目录
            base_dir = os.path.dirname(__file__)

        # 构建 cert.pem 和 key.pem 文件的绝对路径
        cert_path = os.path.join(base_dir, 'cert.pem')
        key_path = os.path.join(base_dir, 'key.pem')

        # 使用 load_cert_chain 方法加载证书链（如果有的话）和相应的私钥。
        # certfile 参数指定了证书文件的路径，keyfile 参数指定了私钥文件的路径。
        # 生成无密码的密钥（推荐在生成密钥时直接操作）：openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
        context.load_cert_chain(certfile = cert_path, keyfile = key_path)

        # 使用 SSLContext 对象的 wrap_socket 方法包装原始的 socket，启用 SSL/TLS 功能。
        # server_side=True 表示这个 socket 是服务器端的 socket，这是必须的参数，因为我们在创建服务器。
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

        print(f'HTTPS 服务器现已启动在：https://localhost:{args.https_port}')  # 打印启动信息
        print()

        # 启动服务器，无限期地等待和处理请求。serve_forever 方法是一个阻塞调用，它将持续运行，直到程序被明确停止。
        # 在此期间，服务器将监听指定的端口，接收客户端的连接请求，并根据请求使用 HttpRequestHandler 来处理这些请求。
        httpd.serve_forever()  # 启动服务器，永久运行
    except PermissionError as e:  # 捕获 PermissionError
        print(f"在启动HTTPS服务器时发生错误，可能的原因有:\n  1、没有足够的权限监听端口 {args.https_port}。请尝试使用更高的权限运行程序，或使用 1024 以上的端口。\n  2、端口 {args.https_port} 已被占用。请尝试使用不同的端口。\n")


if __name__ == '__main__':
    # 调用get_active_ip_addresses函数，获取活跃的网络接口及其IP地址
    active_ip_addresses = get_active_ip_addresses()
    # 打印标题
    print("当前活跃的网络接口 IP 配置 如下：\n")
    # 遍历活跃的网络接口及其IP地址，逐一打印出来
    for interface, ip in active_ip_addresses.items():
        # 格式化输出网络接口及其对应的IP地址
        print(f"{interface}：{ip}")
    print()

    # 根据命令行参数选择运行模式
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        if args.mode in ['http', 'both']:
            # 启动 HTTP 服务器
            futures.append(executor.submit(run_http_server))
        if args.mode in ['https', 'both']:
            # 启动 HTTPS 服务器
            futures.append(executor.submit(run_https_server))

        # 等待所有启动的服务器线程结束（实际上这些服务器会永久运行，直到被外部终止）
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f'服务器运行引发了异常: {exc}')