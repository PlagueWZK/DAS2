# 图像数据增强系统 (DAS)

面向批量图像处理的轻量级数据增强 Web 应用，支持多图上传、增强、预览与打包下载。

## 功能概览

- 多图上传与拖拽导入
- 批量数据增强（旋转、翻转、裁剪、缩放、颜色抖动、亮度、对比度、噪声、模糊）
- 原图/处理后对比预览
- 一键打包下载
- 多线程并行处理

## 技术栈

- 后端：Flask、Werkzeug、Gunicorn
- 图像处理：OpenCV、Pillow、NumPy
- 前端：HTML/CSS/JavaScript

## 快速开始

```bash
pip install -r requirements.txt
python app.py
```

浏览器访问：`http://localhost:10000`

如需自定义端口，可设置环境变量：

```bash
set PORT=10000
```

## 使用流程

1. 上传图像（支持多选和拖拽）
2. 选择需要的增强方法
3. 点击“开始处理”
4. 预览原图和处理后结果
5. 下载单张或全部打包结果

## 主要接口

- `POST /upload`：表单字段 `files`，支持多文件
- `POST /augment`：`{"filenames": [], "augmentations": []}`
- `GET /preview/<filename>`：原图预览（Base64）
- `GET /preview_result/<filename>`：结果预览（Base64）
- `GET /download/<filename>`：下载单张结果
- `POST /download_all`：`{"filenames": []}`，返回 ZIP

## 项目结构

```
DAS/
├── app.py                 # Flask Web 应用与接口
├── data_augmentation.py   # 数据增强核心功能
├── requirements.txt       # 依赖列表
├── templates/
│   └── index.html         # 前端界面
├── uploads/               # 上传文件目录（运行时生成）
├── outputs/               # 处理后文件目录（运行时生成）
├── app.spec               # PyInstaller 打包配置
└── render.yaml            # Render 部署配置
```

## 打包与部署

- 本地打包：

```bash
pip install pyinstaller
pyinstaller app.spec
```

- Render 部署：使用 `render.yaml`，启动命令为 `gunicorn app:app`

