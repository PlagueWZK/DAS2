# 图像数据增强系统（DAS）项目文档

## 项目概述
图像数据增强系统（DAS）是一个基于 Flask 的轻量级 Web 应用，面向批量图像处理与数据增强场景。系统提供上传、增强、预览、批量下载等能力，支持多种常见增强策略，适用于训练数据扩充与快速可视化验证。

## 目标与范围
- 让用户在浏览器中完成多图上传与增强处理
- 提供可视化的原图/处理后对比预览
- 支持一键打包下载增强结果
- 保障处理性能（并行处理）与基本安全策略（文件类型与大小限制）

## 核心功能
- 多图上传与拖拽导入
- 批量数据增强：旋转、翻转、裁剪、缩放、颜色抖动、亮度、对比度、噪声、模糊
- 原图/结果图预览
- ZIP 打包下载

## 系统架构
- 前端：`templates/index.html` 纯 HTML/CSS/JS
- 后端：`app.py` 提供文件处理与 API 接口
- 增强算法：`data_augmentation.py` 提供图像增强实现
- 部署：`render.yaml` 使用 Gunicorn 启动；`app.spec` 支持 PyInstaller 打包

## 关键模块说明

### 1) Web 服务与路由（`app.py`）
- 初始化路径：运行时基准目录、模板目录
- 上传与输出目录：`uploads/`、`outputs/`（启动时自动创建）
- 接口定义：
  - `/upload`：多文件上传
  - `/augment`：批量增强与并行处理
  - `/preview/<filename>`：原图预览
  - `/preview_result/<filename>`：增强结果预览
  - `/download/<filename>`：单张下载
  - `/download_all`：批量打包下载
- 并行处理：`ThreadPoolExecutor`，最大线程数为 `min(8, CPU核数)`
- 安全限制：文件扩展名过滤与 256MB 上传大小限制

### 2) 数据增强实现（`data_augmentation.py`）
- 基于 OpenCV 与 Pillow 实现增强算法
- 支持多种增强：旋转、翻转、裁剪、缩放、颜色抖动、亮度/对比度调整、噪声与模糊
- `apply_augmentation()` 支持按列表组合增强步骤

### 3) 前端交互（`templates/index.html`）
- 左侧：上传与增强选项
- 中间：原图/结果图预览
- 右侧：处理结果列表
- JS 处理上传、状态更新、结果预览与下载

## 数据与接口设计

### 上传接口
- URL：`POST /upload`
- 表单字段：`files`（支持多文件）
- 响应：成功返回上传文件列表及原始文件名

### 增强接口
- URL：`POST /augment`
- 请求示例：
  ```json
  {
    "filenames": ["uuid_xxx.jpg"],
    "augmentations": ["rotation", "flip", "color"]
  }
  ```
- 响应：每个文件的处理结果（成功/失败与输出文件名）

### 预览接口
- `GET /preview/<filename>`：返回原图 Base64
- `GET /preview_result/<filename>`：返回增强结果 Base64

### 下载接口
- `GET /download/<filename>`：单张下载
- `POST /download_all`：传入 `filenames` 列表，返回 ZIP

## 部署与运行

### 本地运行
```bash
pip install -r requirements.txt
python app.py
```
浏览器访问：`http://localhost:10000`

### Render 部署
- 配置文件：`render.yaml`
- 启动命令：`gunicorn app:app`

### 打包发布
```bash
pip install pyinstaller
pyinstaller app.spec
```

## 分工说明（项目三人协作）

- 王忠睿：数据增强算法设计与实现，OpenCV/Pillow 图像处理链路
- 王政凯：后端架构与接口实现，文件管理与并行处理，部署/打包配置
- 魏佳：前端界面设计与交互逻辑，上传/预览/下载流程打通

## 运行验证（建议）
- 上传 3~5 张图片，选择 2~3 种增强方式
- 验证原图与结果预览一致性
- 验证批量下载 ZIP 可用性

## 风险与改进方向
- 大文件与高分辨率图片可能导致内存占用增加
- Base64 预览在批量场景下可能影响响应速度
- 可增加任务进度 API、增强参数可视化配置、历史记录与自动清理机制


