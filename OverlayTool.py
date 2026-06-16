import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image

# ================================
# 明度異常対応処置/背景色に合わせて透明PNGのRGBを補正（右下対応）
# ================================
def match_background_color(overlay, bg, pos_x, pos_y):
    ow, oh = overlay.size
    bw, bh = bg.size

    r_o, g_o, b_o, a_o = overlay.split()
    r_o_data = r_o.load()
    g_o_data = g_o.load()
    b_o_data = b_o.load()
    a_o_data = a_o.load()

    bg_data = bg.load()

    for y in range(oh):
        for x in range(ow):
            if a_o_data[x, y] == 0:
                bx = x + pos_x
                by = y + pos_y
                if 0 <= bx < bw and 0 <= by < bh:
                    pixel = bg_data[bx, by]
                    if len(pixel) == 4:
                        br, bgc, bb, _ = pixel
                    else:
                        br, bgc, bb = pixel

                    r_o_data[x, y] = br
                    g_o_data[x, y] = bgc
                    b_o_data[x, y] = bb

    return Image.merge("RGBA", (r_o, g_o, b_o, a_o))

# ================================
# 特殊フォーマット対応/premultiplied alpha の解除
# ================================
def fix_premultiplied_alpha(img):
    r, g, b, a = img.split()
    a_data = a.load()
    r_data = r.load()
    g_data = g.load()
    b_data = b.load()

    for y in range(img.height):
        for x in range(img.width):
            alpha = a_data[x, y] / 255
            if alpha > 0:
                r_data[x, y] = int(r_data[x, y] / alpha)
                g_data[x, y] = int(g_data[x, y] / alpha)
                b_data[x, y] = int(b_data[x, y] / alpha)

    return Image.merge("RGBA", (r, g, b, a))

# ================================
# バッチ処理本体
# ================================
def run_batch():
    input_dir = input_dir_var.get()
    overlay_path = overlay_path_var.get()

    if not input_dir or not overlay_path:
        messagebox.showerror("エラー", "入力フォルダとレイヤー画像を指定してください")
        return

    output_dir = os.path.join(input_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    overlay_original = Image.open(overlay_path).convert("RGBA")
    overlay_original = fix_premultiplied_alpha(overlay_original)

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue

        bg_path = os.path.join(input_dir, filename)
        out_path = os.path.join(output_dir, filename)

        bg = Image.open(bg_path).convert("RGBA")

        # === 右下座標を計算 ===
        bw, bh = bg.size
        ow, oh = overlay_original.size
        pos_x = bw - ow
        pos_y = bh - oh

        # === 背景色に合わせて補正（右下位置）===
        overlay = match_background_color(overlay_original.copy(), bg, pos_x, pos_y)

        # === 合成（右下）===
        result = bg.copy()
        result.alpha_composite(overlay, dest=(pos_x, pos_y))

        # ファイル名変更（C を付与）
        name, ext = os.path.splitext(filename)
        new_filename = f"{name}C{ext}"
        out_path = os.path.join(output_dir, new_filename)

        result.save(out_path)

    messagebox.showinfo("完了", "バッチ処理が完了しました！")

# ================================
# GUI
# ================================
def select_input_dir():
    path = filedialog.askdirectory()
    if path:
        input_dir_var.set(path)

def select_overlay():
    path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.webp")])
    if path:
        overlay_path_var.set(path)

root = tk.Tk()
root.title("オ―バ―レイ バッチツール")

input_dir_var = tk.StringVar()
overlay_path_var = tk.StringVar()

tk.Label(root, text="入力フォルダ").grid(row=0, column=0, sticky="w")
tk.Entry(root, textvariable=input_dir_var, width=40).grid(row=0, column=1)
tk.Button(root, text="選択", command=select_input_dir).grid(row=0, column=2)

tk.Label(root, text="レイヤー画像（PNG）").grid(row=1, column=0, sticky="w")
tk.Entry(root, textvariable=overlay_path_var, width=40).grid(row=1, column=1)
tk.Button(root, text="選択", command=select_overlay).grid(row=1, column=2)

tk.Button(root, text="バッチ処理開始", command=run_batch,
          bg="#4CAF50", fg="white").grid(row=2, column=1, pady=10)

root.mainloop()
