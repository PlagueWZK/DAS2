# 图像数据增强系统

一个简单的图像数据增强Web应用，支持多种图像增强方法。

## 功能特性

- 随机旋转：在指定角度范围内随机旋转图像
- 随机翻转：水平或垂直翻转图像
- 随机裁剪：按比例随机裁剪图像
- 随机缩放：按比例随机缩放图像
- 颜色抖动：随机调整图像的亮度、对比度和饱和度

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
python app.py
```

应用将在 http://localhost:5000 启动

## 使用方法

1. 打开浏览器访问 http://localhost:5000
2. 上传图像文件（支持拖拽上传）
3. 选择需要应用的数据增强方法
4. 点击"应用数据增强"按钮
5. 查看原始图像和增强后的图像对比
6. 下载增强后的图像

## 支持的图像格式

- PNG
- JPG/JPEG
- GIF
- BMP

## 文件结构

```
DAS2/
├── app.py                 # Flask Web应用
├── data_augmentation.py   # 数据增强核心功能
├── requirements.txt       # 依赖包列表
├── templates/
│   └── index.html        # 前端界面
├── uploads/              # 上传文件存储目录
└── outputs/              # 处理后文件存储目录
```