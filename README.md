# VideoFrameCollector-Single

一个基于 **PyQt6** 开发的单视频逐帧提取工具，界面简洁，操作直观。
支持灵活的截取模式与多种输出格式，可方便地对单个视频文件进行逐帧保存。

---

## ✨ 功能特点

* 🎞️ **灵活截取模式**：

  * 每 **N 秒** 提取一帧
  * 每 **N 帧** 提取一帧

* 🖼️ **多种输出格式**：

  * PNG 无损保存
  * JPG 可自定义压缩质量 (1–100)

* 📑 **输出管理**：

  * 输出结果自动存放在以视频文件名命名的文件夹中
  * 截取完成后，可直接打开输出目录查看结果

* 🔍 **自检功能**：

  * 启动时检查 `ffmpeg` / `ffprobe` 是否存在
  * 缺失时弹窗提示

---

## 📦 安装

1. 克隆仓库

   ```bash
   git clone https://github.com/xiaolu257/VideoFrameCollector-Single.git
   cd VideoFrameCollector-Single
   ```

2. 创建虚拟环境（推荐）

   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux / MacOS
   venv\Scripts\activate         # Windows
   ```

3. 安装依赖

   ```bash
   pip install -r requirements.txt
   ```

4. 项目内置 **ffmpeg / ffprobe**，用户无需单独安装或配置环境变量。

---

## 🚀 使用方法

1. 启动程序

   ```bash
   python main.py
   ```

2. 在界面中：

   * 选择需要处理的单个视频文件
   * 设置截取模式（每 N 秒 或 每 N 帧）
   * 选择输出格式（PNG 或 JPG）及参数
   * 点击 **开始处理**，等待完成

3. 处理完成后：

   * 输出文件夹会自动生成在指定目录下
   * 可直接双击结果记录，快速打开输出目录

---

## 🛠️ 打包为可执行文件

如果需要在无 Python 环境的机器上运行，可以使用 **PyInstaller** 打包：

```bash
python 打包程序.py
```

打包完成后，可执行文件（`VideoFrameCollector-Single.exe`）会位于：

```
dist/VideoFrameCollector-Single/
```

请确保 `ffmpeg/` 文件夹也随程序一同分发（若打包正常，`ffmpeg` 与 `ffprobe`
应当存在于 `dist/VideoFrameCollector-Single/_internal/ffmpeg` 下）。

---

## 📦 依赖说明

本项目依赖以下 Python 库（已在 `requirements.txt` 中列出）：

* PyQt6
* pyinstaller

⚠️ 注意事项：

* [ffmpeg](https://ffmpeg.org/) 与 [ffprobe](https://ffmpeg.org/ffprobe.html) 已 **内置在项目中**，无需单独安装。
* 程序启动时会自动检查 `ffmpeg` / `ffprobe` 是否存在。

开发环境额外依赖：

* [pyinstaller](https://pypi.org/project/pyinstaller/)（仅用于打包）

---

## 📷 截图

### 1️⃣ 界面展示

<img width="918" height="657" alt="image" src="https://github.com/user-attachments/assets/1427c611-76a1-4176-bcaa-efd3d38ea53d" />  

### 2️⃣ 参数设置并开始处理

<img width="918" height="660" alt="image" src="https://github.com/user-attachments/assets/624eb7f1-0642-409f-a774-70f1bfca4840" />  

### 3️⃣ 处理完成

<img width="915" height="658" alt="image" src="https://github.com/user-attachments/assets/782de6ec-eb67-4419-ade4-8e87c64956ca" />  

### 4️⃣ 输出目录示例

（文件夹名为 `<视频文件名>_帧提取_<日期时间>`） <img width="1919" height="1280" alt="image" src="https://github.com/user-attachments/assets/5598eec3-c0ee-4a67-aef8-49b4b9364171" />

### 5️⃣ 随机选择图片展示

<img width="1903" height="998" alt="image" src="https://github.com/user-attachments/assets/cb2a8022-89d7-445a-aacb-6168d9ec43e0" />  

---

## 📜 许可证

本项目基于 [MIT License](LICENSE) 开源，欢迎自由使用、修改和分发。

⚠️ 版权格言：

> 盗他人之功，非君子所为；妄称己作，损德亦伤名。
> 勿窃他人成果，自显其劳；尊重原作者，方成正道。

如有问题或交流需求，请联系：[1626309145@qq.com](mailto:1626309145@qq.com)
