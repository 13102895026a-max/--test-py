import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import sys
import time
import numpy as np
import psutil as ps
import pyautogui as op
import os

from fontTools.merge import timer


# ---------------------- 1. 解决打包后资源路径（关键：确保图片能被找到）----------------------
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        # 打包后：读取临时解压目录的图片
        return os.path.join(sys._MEIPASS, relative_path)
    # 开发时：读取本地图片（图片需和main.py同目录）
    return os.path.join(os.path.dirname(sys.argv[0]), relative_path)


# ---------------------- 2. 你的核心图像匹配逻辑（仅修改图片路径获取方式）----------------------
def image_pd(image_path, threshold=0.5):
    try:
        # 截图
        op.screenshot("screenshot.png")
        scrren_image = cv2.imread("screenshot.png")
        # 用资源路径函数获取目标图片（关键修改）
        image = cv2.imread(get_resource_path(image_path))

        # 检查图片是否读取成功
        if scrren_image is None:
            return False, "截图失败，无法获取屏幕图像"
        if image is None:
            return False, f"未找到图片：{image_path}，请确认图片存在"

        # 图像匹配
        scrren_gray = cv2.cvtColor(scrren_image, cv2.COLOR_BGR2GRAY)
        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        match = cv2.matchTemplate(scrren_gray, image_gray, cv2.TM_CCOEFF_NORMED)
        location = np.where(match > threshold)

        if len(location[0]) > 0:  # 修复：原代码len(location)判断不准确，需判断具体维度
            x1, y1 = next(zip(*location[::-1]))
            h, w = image_gray.shape[:2]
            x2, y2 = x1 + w, y1 + h
            mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
            return True, (x1, y1, x2, y2, mid_x, mid_y)
        else:
            return False, f"未匹配到图片：{image_path}"
    except Exception as e:
        return False, f"图像匹配出错：{str(e)}"


def image_found(image_path, threshold=0.5):
    success, result = image_pd(image_path, threshold)
    if success:
        _, _, _, _, mid_x, mid_y = result
        op.click(mid_x, mid_y)
        op.click(mid_x, mid_y)
        return True, f"成功找到并点击：{image_path}"
    else:
        return False, result  # 返回错误信息


# ---------------------- 3. 界面按钮触发的主逻辑（含错误显示）----------------------
def run_main_logic():
    # 清空之前的日志和错误
    log_text.delete(1.0, tk.END)
    # 禁用开始按钮，防止重复点击
    start_btn.config(state=tk.DISABLED)

    try:
        # 1. 查找alas.png
        log_text.insert(tk.END, "正在查找：alas.png...\n")
        log_text.update()  # 实时刷新日志
        success, msg = image_found("alas.png", 0.5)
        if not success:
            raise Exception(msg)
        log_text.insert(tk.END, f"{msg}\n")
        log_text.insert(tk.END, "等待8秒...\n")
        log_text.update()
        time.sleep(8)

        # 2. 查找mumu.png
        log_text.insert(tk.END, "正在查找：mumu.png...\n")
        log_text.update()
        success, msg = image_found("mumu.png", 0.5)
        if not success:
            raise Exception(msg)
        log_text.insert(tk.END, f"{msg}\n")
        log_text.insert(tk.END, "等待15秒...\n")
        log_text.update()
        time.sleep(15)

        # 3. 查找blhx.png（循环10次等待）
        log_text.insert(tk.END, "正在查找：blhx.png...\n")
        log_text.update()
        blhx_found = False
        for _ in range(10):
            n = 0
            success, msg = image_found("blhx.png", 0.4)
            if success:
                log_text.insert(tk.END, f"{msg}\n")
                blhx_found = True
                n+=1
                time.sleep(4)
                if n >= 7:
                    break
                else:
                    continue
            time.sleep(4)
            if not success:
                log_text.insert(tk.END, f"第{_ + 1}次未找到blhx.png，继续等待...\n")
                log_text.update()
        if not blhx_found:
            raise Exception("循环10次后仍未找到blhx.png")

        # 4. 查找start.png
        log_text.insert(tk.END, "正在查找：start.png...\n")
        log_text.update()
        success, msg = image_found("start.png", 0.8)
        if not success:
            raise Exception(msg)
        log_text.insert(tk.END, f"{msg}\n")
        log_text.insert(tk.END, "=" * 30 + "\n")
        log_text.insert(tk.END, "所有步骤执行完成！\n")

    except Exception as e:
        # 显示错误信息
        log_text.insert(tk.END, f"\n【错误】：{str(e)}\n", "error")
    finally:
        # 恢复开始按钮可点击
        start_btn.config(state=tk.NORMAL)
        # 删除临时截图
        if os.path.exists("screenshot.png"):
            os.remove("screenshot.png")


# ---------------------- 4. 创建用户界面 ----------------------
root = tk.Tk()
root.title("图像匹配自动点击工具")
root.geometry("500x400")  # 窗口大小

# ① 开始按钮
start_btn = ttk.Button(
    root,
    text="开始执行",
    command=run_main_logic,
    width=20
)
start_btn.pack(pady=15)

# ② 日志/错误显示框（带滚动条）
log_frame = ttk.Frame(root)
log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# 滚动条
log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL)
log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

# 文本框（显示日志和错误）
log_text = tk.Text(
    log_frame,
    yscrollcommand=log_scroll.set,
    font=("微软雅黑", 10),
    wrap=tk.WORD
)
log_text.pack(fill=tk.BOTH, expand=True)
log_scroll.config(command=log_text.yview)

# 错误文本的样式（红色）
log_text.tag_configure("error", foreground="red", font=("微软雅黑", 10, "bold"))

# 启动界面
root.mainloop()