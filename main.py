import cv2
import math
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import *
from tkinter import messagebox
import os.path
import pdf2image
import img2pdf


message = None
root = None
MESSAGE = "画像/pdfファイルをドロップしてください。"


def imread(filename, flags=cv2.IMREAD_COLOR, dtype=np.uint8):
    try:
        n = np.fromfile(filename, dtype)
        img = cv2.imdecode(n, flags)
        return img
    except Exception as e:
        messagebox.showerror("Error", e)
        return None


def imwrite(filename, img, params=None):
    try:
        ext = os.path.splitext(filename)[1]
        result, n = cv2.imencode(ext, img, params)

        if result:
            with open(filename, mode='w+b') as f:
                n.tofile(f)
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


def disp_result(img1, img2, direction):
    rate = min(800 / (img1.shape[1] * 2), 1.0)
    dst = cv2.resize(cv2.hconcat([img1, img2]), dsize=None, fx=rate, fy=rate)
    if direction == "h":
        for i in range(10):
            cv2.line(dst, (0, dst.shape[0] * i // 10),
                     (dst.shape[1], dst.shape[0] * i // 10), (0, 255, 0), 1)
    else:
        for i in range(10):
            cv2.line(dst, (dst.shape[1] * i // 10, 0),
                     (dst.shape[1] * i // 10, dst.shape[0]), (0, 255, 0), 1)
    cv2.line(dst, (dst.shape[1] // 2, 0),
             (dst.shape[1] // 2, dst.shape[0]), (0, 0, 0), 2)
    cv2.putText(dst, 'origin', (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                1, (255, 0, 0), 2, cv2.LINE_4)
    cv2.putText(dst, 'result', (dst.shape[1] // 2 + 10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_4)
    cv2.imshow("image", dst)
    cv2.waitKey(0)


def disp(img, rate=None):
    if type(img) is list:
        im_list = []
        for im in img:
            if(len(im.shape) == 3):
                im_list.append(im)
            else:
                im_list.append(cv2.cvtColor(im, cv2.COLOR_GRAY2BGR))
        if rate is None:
            rate = min(800 / (im_list[0].shape[1] * len(im_list)), 1.0)
        dst = cv2.resize(
            cv2.hconcat(im_list), dsize=None, fx=rate, fy=rate)
        cv2.imshow("image", dst)
    else:
        if rate is None:
            rate = min(800 / img.shape[1], 1.0)
        dst = cv2.resize(img, dsize=None, fx=rate, fy=rate)
        cv2.imshow("image", dst)
    cv2.waitKey(0)


def get_degree(img, diff=5):
    l_img = img.copy()
    gray = cv2.cvtColor(l_img, cv2.COLOR_BGR2GRAY)
    median = cv2.medianBlur(gray, 5)
    ret3, th3 = cv2.threshold(median, 0, 255, cv2.THRESH_OTSU)
    edges = cv2.Canny(th3, 230, 300, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=10,
                            minLineLength=300, maxLineGap=50)
    sum_arg = 0
    cnt = 0
    sum_arg2 = 0
    cnt2 = 0

    if lines is None:
        return (0, "h")
    for line in lines:
        for x1, y1, x2, y2 in line:
            arg = math.degrees(math.atan2((y2-y1), (x2-x1)))
            if arg > - diff and arg < diff:
                # if arg != 0:
                #    cv2.line(l_img, (x1, y1), (x2, y2), (0, 0, 255), 10)
                # else:
                #    cv2.line(l_img, (x1, y1), (x2, y2), (255, 0, 0), 10)
                sum_arg += arg
                if arg == 0:
                    cnt += 0.5
                else:
                    cnt += 1
            if arg > 90 - diff and arg < 90 + diff:
                sum_arg2 += arg - 90
                if arg == 0:
                    cnt2 += 0.5
                else:
                    cnt2 += 1
    #disp([l_img, edges])
    if cnt == 0 and cnt2 == 0:
        return (0, "h")
    else:
        if cnt > cnt2 // 2:
            return (sum_arg / cnt, "h")
        return (sum_arg2 / cnt2, "v")


def get_new_filename(fname, kaku):
    if os.path.exists(fname + kaku) is not True:
        return fname + kaku
    i = 1
    while True:
        path = fname + "(" + str(i) + ")" + kaku
        if os.path.exists(path) is not True:
            return path
        i += 1


def rotate_img(img):
    degree, direction = get_degree(img)
    height = img.shape[0]
    width = img.shape[1]
    center = (int(width/2), int(height/2))
    trans = cv2.getRotationMatrix2D(center, degree, 1.0)
    img2 = cv2.warpAffine(img, trans, (width, height),
                          borderValue=(255, 255, 255))

    disp_result(img, img2, direction)
    return img2


def deal_pdf(path):
    try:
        splitext = os.path.splitext(os.path.basename(path))
        poppler_path = os.path.join(os.getcwd(), "poppler-0.68.0", "bin")
        os.environ["PATH"] += os.pathsep + poppler_path

        filepath = os.path.abspath(os.path.dirname(__file__))
        filepath = os.path.join(filepath, "pdf", path)

        pdfimages = pdf2image.convert_from_path(filepath)

    except Exception as e:
        messagebox.showerror("Error", e)
        messagebox.showinfo("popplerをインストールしてください。",
                            "popplerをインストールしていないために起きたエラーの可能性があります。popplerをインストールしてください。https://blog.alivate.com.au/poppler-windows/")
        return

    img_list = []
    for i, im in enumerate(pdfimages):
        img = np.asarray(im)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        temp_path = "___temp" + str(i) + ".jpg"
        imwrite(temp_path, rotate_img(img))
        img_list.append(temp_path)

    fname = os.path.dirname(path) + "/" + splitext[0]
    path = get_new_filename(fname, splitext[-1])
    print(img_list)
    with open(path, "wb") as f:
        f.write(img2pdf.convert(img_list))
    message.set(MESSAGE)
    messagebox.showinfo("処理が完了しました", os.path.basename(path) + "として保存しました。")


def deal_img(path):
    splitext = os.path.splitext(os.path.basename(path))
    img = imread(path)
    if img is None:
        messagebox.showerror(
            "Error", os.path.basename(path)+"を画像ファイルとして認識できません。")
        return
    message.set(os.path.basename(path) + "を処理しています。")
    root.update()
    img2 = rotate_img(img)
    fname = os.path.dirname(path) + "/" + splitext[0]
    path = get_new_filename(fname, splitext[-1])
    imwrite(path, img2)
    message.set(MESSAGE)
    messagebox.showinfo("処理が完了しました", os.path.basename(path) + "として保存しました。")


def make_file(path):
    splitext = os.path.splitext(os.path.basename(path))
    if splitext[-1] == ".pdf":
        deal_pdf(path)
    else:
        deal_img(path)


def drop(event):
    path = event.data[1:-1]
    make_file(path)


def main():
    global message, root
    # メインウィンドウの生成
    root = TkinterDnD.Tk()
    root.geometry("600x400")
    root.title("画像とpdfの傾き修正プログラム")
    root.drop_target_register(DND_FILES)
    root.dnd_bind("<<Drop>>", drop)
    # StringVarのインスタンスを格納するウィジェット変数text
    message = tk.StringVar(root)
    message.set(MESSAGE)
    # Lavelウィジェットの生成
    label = ttk.Label(root, textvariable=message,
                      font=("MSゴシック", "15", "bold"))
    # ウィジェットの配置
    label.grid(row=0, column=0, padx=10)
    root.mainloop()


print(cv2.__file__)
main()
