# 🎰 SpriteBINGO
> **The Professional GBS Tool for Pixel-Perfect Recoloring & Grid Mapping**

SpriteBINGO is a specialized utility designed to bridge the gap between high-fidelity pixel art and the technical constraints of Game Boy Studio hardware. It automates color clustering, palette optimization, and tile-grid generation.

---

## 🚀 Key Features

* **Intelligent Recoloring:** Automatically maps source images to a defined "Go-To" palette using quadratic distance math.
* **GBS Hardware Preview:** Generates 8x16 tile-grid atlases to visualize how your sprites will be handled by hardware.
* **Palette Optimization:** Clusters colors into valid GBS palettes (Light, Mid, Shadow + Green Transparency).
* **Automated Remixing:** Brute-forces color permutations to find the mathematically "best match" for your sprites.

---

## 🛠 How to Use

### Step 1: Recolor
1. Select your **Input Folder** (containing your PNGs).
2. Define your **Go-To Palette** (Default is 4 colors).
3. Set your **Palette Limit** (Max number of hardware palettes).
4. Run **Step 1** to generate optimized variations.

### Step 2: GBS Preview
1. Choose the best variation from the selected output folder.
2. Run **Step 2** to generate your `tile_grid_atlas` and `palettes.json`.

---

## 🔒 Privacy & Data
* **100% Serverless:** All processing happens locally on your machine.
* **No Data Collection:** This application does not acquire, store, or transmit any personal data or usage statistics.

---

## 📜 License & Usage
* **Usage:** Free for personal and commercial use.
* **Distribution:** While the software is free, we prefer that users download the official version from the original source to ensure they have the latest security and feature updates.
* **Warranty:** Provided "as-is" under the MIT License.

## 📺 Video Tutorial

<p align="center">
  <video src="https://github.com/contactpyxelmorph-afk/spriteBINGO/raw/main/tutorial_small.mp4">
    Your browser does not support the video tag.
  </video>
</p>

---
**Developed by Pyxel Corp**
*Built for the GBS Community.*

