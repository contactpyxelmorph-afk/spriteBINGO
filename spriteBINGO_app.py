import os
import sys
import json
import threading
import shutil
import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
from collections import Counter
from itertools import combinations, permutations
from PIL import Image, ImageDraw, ImageTk
import ctypes

# Fix for the taskbar icon: Tells Windows to use the custom icon for the running process
try:
    myappid = 'mycompany.myproduct.subproduct.version'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

# ------------------------- CONFIG -------------------------
GBS_HW_COLORS = [
    (224, 248, 207),  # 0: Light
    (134, 192, 108),  # 1: Dark/Mid
    (101, 255, 0),  # 2: Green (Trans)
    (7, 24, 33)  # 3: Shadow
]

TILE_WIDTH = 8
TILE_HEIGHT = 16


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def brightness(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ------------------------- APP -------------------------
class SpriteBingoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SpriteBINGO – Professional GBS Tool")
        self.root.geometry("850x750")

        # 1. SETUP TASKBAR ID FIRST
        try:
            myappid = 'mycompany.spritebingo.gbs.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"Ctypes error: {e}")

        # 2. SET ICONS
        try:
            icon_path = resource_path("logo ico.ico")

            # This sets the small icon in the top left of the window
            self.root.iconbitmap(icon_path)

            # This is the "Magic Bullet" for the taskbar:
            # We load the image via PIL and pass it to wm_iconphoto
            icon_img = Image.open(icon_path)
            self.taskbar_icon = ImageTk.PhotoImage(icon_img)

            # The 'True' argument applies this icon to all future child windows too
            self.root.wm_iconphoto(True, self.taskbar_icon)

        except Exception as e:
            print(f"Icon Error: {e}")
        # STARTUP FIX: Defaulting to 4 colors with variety
        self.goto_colors = [
            (255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255)
        ]

        self.input_folder = ""
        self.output_folder = ""
        self.step2_input_path = ""
        self.build_ui()

    def build_ui(self):
        bg_color = "#add8e6"  # Light Blue
        self.root.configure(bg=bg_color)

        # 1. LOGO (Centered at top)
        try:
            logo_path = resource_path("logo png.png")
            pil_logo = Image.open(logo_path).convert("RGBA")
            h_target = 130
            w_target = int(pil_logo.width * (h_target / pil_logo.height))
            pil_logo = pil_logo.resize((w_target, h_target), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(pil_logo)
            tk.Label(self.root, image=self.logo_img, bg=bg_color).pack(pady=15)
        except Exception as e:
            print(f"Logo failed to load: {e}")

        # 2. CONFIG FRAME
        cfg = tk.Frame(self.root, bg=bg_color)
        cfg.pack(pady=10)

        tk.Label(cfg, text="Go-To Colors", bg=bg_color).grid(row=0, column=0, padx=5)

        self.count_var = tk.StringVar(value="4")
        tk.Spinbox(cfg, from_=1, to=32, textvariable=self.count_var,
                   command=self.refresh_swatches, width=5).grid(row=0, column=1)

        tk.Label(cfg, text="Palette Limit", bg=bg_color).grid(row=0, column=2, padx=5)

        self.limit_var = tk.StringVar(value="8")
        tk.Spinbox(cfg, from_=1, to=32, textvariable=self.limit_var, width=5).grid(row=0, column=3)

        # 3. PALETTE FRAME
        self.swatch_frame = tk.LabelFrame(self.root, text="Go-To Palette", bg=bg_color)
        self.swatch_frame.pack(padx=20, pady=10, fill="x")
        self.swatch_container = tk.Frame(self.swatch_frame, bg=bg_color)
        self.swatch_container.pack()
        self.refresh_swatches()

        # 4. IO FOLDERS
        io = tk.Frame(self.root, bg=bg_color)
        io.pack(pady=10)
        tk.Button(io, text="Select Input Folder", command=self.select_input).pack(side="left", padx=5)
        tk.Button(io, text="Select Output Folder", command=self.select_output).pack(side="left", padx=5)

        # 5. ACTION BUTTONS
        self.btn_frame = tk.Frame(self.root, bg=bg_color)
        self.btn_frame.pack(pady=10)

        self.btn_step1 = tk.Button(self.btn_frame, text="Step 1: Recolor", bg="#65ff00",
                                   command=lambda: threading.Thread(target=self.step1_recolor, daemon=True).start())
        self.btn_step1.pack(side="left", padx=5)

        # CREATE BUT DON'T PACK (HIDDEN)
        self.btn_choose = tk.Button(self.btn_frame, text="👉 CHOOSE REMIX FOR STEP 2", bg="#ffff00",
                                    font=("Arial", 10, "bold"), command=self.select_step2_input)

        self.btn_step2 = tk.Button(self.btn_frame, text="Step 2: GBS Preview", bg="#00ff65",
                                   command=lambda: threading.Thread(target=self.step2_green, daemon=True).start())
        self.btn_step2.pack(side="left", padx=5)

        # 6. STATUS
        self.input_label = tk.Label(self.root, text="Step 2 Input: Auto (recolored.png)",
                                    bg=bg_color, fg="#555555", font=("Arial", 9, "italic"))
        self.input_label.pack(pady=5)

    def refresh_swatches(self):
        n = int(self.count_var.get())
        presets = [
            (255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255), (0, 0, 0),
            (128, 0, 0), (0, 128, 0), (0, 0, 128), (128, 128, 0)
        ]
        while len(self.goto_colors) < n:
            if len(self.goto_colors) < len(presets):
                self.goto_colors.append(presets[len(self.goto_colors)])
            else:
                self.goto_colors.append((127, 127, 127))
        while len(self.goto_colors) > n:
            self.goto_colors.pop()
        for w in self.swatch_container.winfo_children():
            w.destroy()
        for i, c in enumerate(self.goto_colors):
            tk.Button(self.swatch_container, bg="#%02x%02x%02x" % c, width=3, height=1,
                      command=lambda i=i: self.change_color(i)).grid(row=i // 8, column=i % 8, padx=2, pady=2)

    def change_color(self, idx):
        result = colorchooser.askcolor(initialcolor=self.goto_colors[idx])
        if result[0]:
            self.goto_colors[idx] = tuple(map(int, result[0]))
            self.refresh_swatches()

    def select_input(self):
        self.input_folder = filedialog.askdirectory()

    def select_output(self):
        self.output_folder = filedialog.askdirectory()

    def select_step2_input(self):
        remix_dir = os.path.join(self.output_folder, "new_alg_remixes")
        path = filedialog.askopenfilename(initialdir=remix_dir if os.path.exists(remix_dir) else self.output_folder,
                                          title="Select Image for Green Preview",
                                          filetypes=(("PNG files", "*.png"), ("all files", "*.*")))
        if path:
            self.step2_input_path = path
            self.input_label.config(text=f"Step 2 Input: {os.path.basename(path)}", fg="#00aa44",
                                    font=("Arial", 9, "bold"))

    def export_recolored_only(self, images, cmap):
        if not images: return
        w, h = max(img.width for img in images), sum(img.height for img in images)
        sheet = Image.new("RGBA", (w, h))
        y_off = 0
        for img in images:
            out_data = [(cmap.get(p[:3], (0, 0, 0)) + (255,)) if p[3] else (0, 0, 0, 0) for p in img.getdata()]
            tmp = Image.new("RGBA", img.size)
            tmp.putdata(out_data)
            sheet.paste(tmp, (0, y_off))
            y_off += img.height
        sheet.save(os.path.join(self.output_folder, "recolored.png"))

    def step1_recolor(self):
        if not self.input_folder or not self.output_folder:
            messagebox.showerror("Error", "Select folders")
            return

        images, names = [], []
        for f in sorted(os.listdir(self.input_folder)):
            if f.lower().endswith(".png"):
                images.append(Image.open(os.path.join(self.input_folder, f)).convert("RGBA"))
                names.append(f)
        if not images: return

        usage = Counter()
        for img in images:
            for r, g, b, a in img.getdata():
                if a: usage[(r, g, b)] += 1
        source_colors = list(usage.keys())

        potency_cmap = {c: min(self.goto_colors, key=lambda g: dist(c, g)) for c in source_colors}

        def get_illegal_tiles(current_cmap):
            ill = []
            for img in images:
                pix, w, h = list(img.getdata()), img.width, img.height
                for y in range(0, h, TILE_HEIGHT):
                    for x in range(0, w, TILE_WIDTH):
                        s = set()
                        for dy in range(TILE_HEIGHT):
                            for dx in range(TILE_WIDTH):
                                ix, iy = x + dx, y + dy
                                if ix < w and iy < h:
                                    p = pix[iy * w + ix]
                                    if p[3]: s.add(current_cmap[p[:3]])
                        if len(s) > 3: ill.append(s)
            return ill

        optimized_cmap = potency_cmap.copy()

        while True:
            illegal_sets = get_illegal_tiles(optimized_cmap)
            if not illegal_sets: break
            target_set = illegal_sets[0]
            best_pair = None
            min_total_cost = float('inf')
            current_unique_count = len(set(optimized_cmap.values()))

            for c1, c2 in combinations(target_set, 2):
                visual_damage = sum(dist(src, c2) * usage[src] for src, v in optimized_cmap.items() if v == c1)
                test_unique_count = len(set(v if v != c1 else c2 for v in optimized_cmap.values()))
                color_loss_penalty = 0
                if test_unique_count < current_unique_count:
                    color_loss_penalty = 1000000 + (visual_damage * 10)
                total_cost = visual_damage + color_loss_penalty
                if total_cost < min_total_cost:
                    min_total_cost = total_cost
                    best_pair = (c1, c2)

            if best_pair:
                c1, c2 = best_pair
                for k in optimized_cmap:
                    if optimized_cmap[k] == c1: optimized_cmap[k] = c2
            else:
                break

        self.export_recolored_only(images, optimized_cmap)

        remix_f = os.path.join(self.output_folder, "new_alg_remixes")
        if os.path.exists(remix_f): shutil.rmtree(remix_f)
        os.makedirs(remix_f, exist_ok=True)

        target_colors = list(set(optimized_cmap.values()))
        best_overall_cmap = optimized_cmap
        min_score = sum(dist(src, optimized_cmap[src]) * usage[src] for src in source_colors)

        if 2 <= len(target_colors) <= 6:
            for p_idx, p_set in enumerate(permutations(target_colors)):
                swap = dict(zip(target_colors, p_set))
                variant_cmap = {src: swap[optimized_cmap[src]] for src in source_colors}
                current_score = sum(dist(src, variant_cmap[src]) * usage[src] for src in source_colors)

                for img, n in zip(images, names):
                    out = img.copy()
                    out.putdata([(variant_cmap.get(p[:3], (0, 0, 0)) + (255,)) if p[3] else (0, 0, 0, 0) for p in
                                 img.getdata()])
                    out.save(os.path.join(remix_f, f"v{p_idx}_{n}"))

                if current_score < min_score:
                    min_score = current_score
                    best_overall_cmap = variant_cmap.copy()

        for img, n in zip(images, names):
            out = img.copy()
            out.putdata(
                [(best_overall_cmap.get(p[:3], (0, 0, 0)) + (255,)) if p[3] else (0, 0, 0, 0) for p in img.getdata()])
            out.save(os.path.join(self.output_folder, f"RECOMMENDED_BEST_{n}"))

        self.step2_input_path = os.path.join(self.output_folder, f"RECOMMENDED_BEST_{names[0]}")

        # --- SHOW BUTTON AFTER FINISH ---
        self.btn_choose.pack(side="left", padx=5)
        messagebox.showinfo("Complete", f"Variety-First Optimization Done.\nKept {len(target_colors)} colors.")

    def step2_green(self):
        path = self.step2_input_path if self.step2_input_path else os.path.join(self.output_folder, "recolored.png")
        if not os.path.exists(path):
            messagebox.showerror("Error", "No image found.")
            return

        recolored = Image.open(path).convert("RGBA")
        w, h = recolored.size
        sorted_active = sorted(self.goto_colors, key=brightness, reverse=True)

        green_map = {}
        if len(sorted_active) >= 1: green_map[sorted_active[0]] = (224, 248, 207)
        if len(sorted_active) >= 2: green_map[sorted_active[1]] = (134, 192, 108)
        if len(sorted_active) >= 3: green_map[sorted_active[-1]] = (7, 24, 33)

        green_pixels = []
        for p in recolored.getdata():
            if p[3] == 0:
                green_pixels.append((101, 255, 0, 255))
            else:
                rgb = p[:3]
                target_rgb = green_map.get(rgb, (134, 192, 108))
                green_pixels.append(target_rgb + (255,))

        green_out = Image.new("RGBA", (w, h))
        green_out.putdata(green_pixels)
        green_out.save(os.path.join(self.output_folder, "GBS_GREEN_PREVIEW.png"))

        raw_tiles, pix = {}, list(recolored.getdata())
        for y in range(0, h, TILE_HEIGHT):
            for x in range(0, w, TILE_WIDTH):
                colors = set()
                for dy in range(TILE_HEIGHT):
                    for dx in range(TILE_WIDTH):
                        ix, iy = x + dx, y + dy
                        if ix < w and iy < h:
                            p = pix[iy * w + ix]
                            if p[3]: colors.add(p[:3])
                raw_tiles[(x, y)] = frozenset(colors)

        u_sets = sorted(list(set(raw_tiles.values()) - {frozenset()}), key=len, reverse=True)
        opt_pals = []
        for s in u_sets:
            if not any(s <= existing for existing in opt_pals): opt_pals.append(s)
        opt_pals.reverse()
        tile_assignments = {pos: next((i for i, p in enumerate(opt_pals) if s <= p), 0) for pos, s in raw_tiles.items()
                            if s}

        atlas_f = os.path.join(self.output_folder, "tile_grid_atlas")
        if os.path.exists(atlas_f): shutil.rmtree(atlas_f)
        os.makedirs(atlas_f, exist_ok=True)

        DISPLAY_TILE_SIZE, CHUNK_TILES, MARGIN, LEGEND_HEIGHT = 32, 16, 60, 100
        BG_COLOR, LABEL_COLOR = (30, 33, 39), (180, 185, 190)
        IDX_COLORS = [(255, 95, 95), (95, 255, 95), (95, 95, 255), (255, 255, 95), (255, 95, 255), (95, 255, 255),
                      (255, 160, 60), (160, 255, 60)]

        for cy in range(0, h // 8, CHUNK_TILES):
            for cx in range(0, w // 8, CHUNK_TILES):
                actual_tiles_x = min(CHUNK_TILES, (w // 8) - cx)
                actual_tiles_y = min(CHUNK_TILES, (h // 8) - cy)
                canvas_w = (actual_tiles_x * DISPLAY_TILE_SIZE) + MARGIN
                canvas_h = (actual_tiles_y * DISPLAY_TILE_SIZE) + MARGIN + LEGEND_HEIGHT
                canvas = Image.new("RGBA", (canvas_w, canvas_h), BG_COLOR)
                draw = ImageDraw.Draw(canvas)

                for ty in range(actual_tiles_y):
                    abs_y = cy + ty
                    draw.text((15, ty * DISPLAY_TILE_SIZE + MARGIN + 8), str(abs_y), fill=LABEL_COLOR)
                    for tx in range(actual_tiles_x):
                        abs_x = cx + tx
                        if ty == 0:
                            draw.text((tx * DISPLAY_TILE_SIZE + MARGIN + 8, 15), str(abs_x), fill=LABEL_COLOR)
                        origin_x, origin_y = (abs_x * 8), (abs_y * 8)
                        lookup_y = origin_y if origin_y % 16 == 0 else origin_y - 8
                        p_idx = tile_assignments.get((origin_x, lookup_y), -1)
                        rx, ry = tx * DISPLAY_TILE_SIZE + MARGIN, ty * DISPLAY_TILE_SIZE + MARGIN
                        rect = [rx, ry, rx + DISPLAY_TILE_SIZE - 2, ry + DISPLAY_TILE_SIZE - 2]
                        if p_idx != -1:
                            fill_col = IDX_COLORS[p_idx % len(IDX_COLORS)]
                            draw.rectangle(rect, fill=fill_col, outline=(255, 255, 255, 80))
                            draw.text((rx + 10, ry + 8), str(p_idx), fill=(255, 255, 255), stroke_width=1,
                                      stroke_fill=(0, 0, 0))
                        else:
                            draw.rectangle(rect, outline=(60, 63, 69))
                canvas.save(os.path.join(atlas_f, f"atlas_X{cx // CHUNK_TILES}_Y{cy // CHUNK_TILES}.png"))

        pal_data = {}
        for i, pal in enumerate(opt_pals):
            ps = sorted(list(pal), key=brightness, reverse=True)
            hex_c = ["#%02x%02x%02x" % c for c in ps]
            pal_data[f"palette {i}"] = [
                hex_c[0] if len(ps) > 0 else "#E0F8CF",
                hex_c[1] if len(ps) > 1 else "#86C06C",
                "#65FF00",
                hex_c[2] if len(ps) > 2 else (hex_c[1] if len(ps) > 1 else "#071821")
            ]
        with open(os.path.join(self.output_folder, "palettes.json"), "w") as f:
            json.dump(pal_data, f, indent=2)

        messagebox.showinfo("BINGO", f"Step 2 Complete!\nPalettes used: {len(opt_pals)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SpriteBingoApp(root)
    root.mainloop()