# DAS 图像数据增强系统说明

面向批量图像上传、在线预览与数据增强处理的 Flask Web 应用。后端以 Flask + OpenCV + Pillow 完成图像处理，前端为纯 HTML/CSS/JS 单页。

## 目录概览
- `app.py`：Flask 服务、REST 接口、批量任务并发调度。
- `data_augmentation.py`：数据增强算法合集。
- `templates/index.html`：前端 UI/交互逻辑（拖拽上传、勾选增强项、批量处理、ZIP 下载）。
- `uploads/`、`outputs/`：分别存放原图与处理结果（启动时自动创建）。
- `render.yaml`：Render 部署模板（gunicorn）。
- `app.spec`：PyInstaller 打包配置。
- `requirements.txt`：运行依赖。

## 快速开始
1) 安装依赖：`pip install -r requirements.txt`  
2) 启动开发：`python app.py`（默认监听 `0.0.0.0:10000`，可用环境变量 `PORT` 覆盖）  
3) 浏览器访问 `http://localhost:10000`，拖拽/选择图片后勾选增强项并开始处理。  
4) 下载结果：单张（`/download/<filename>`）或 ZIP（前端“下载全部”调用 `/download_all`）。

运行配置要点：
- 允许格式：png/jpg/jpeg/gif/bmp。
- 文件大小：单请求最大 256MB（`app.config['MAX_CONTENT_LENGTH']`）。
- 以 `uuid4_原文件名` 形式存储，避免重名覆盖。

## 核心数据流
1) 前端拖拽/选择文件，逐个 POST `/upload`，服务端落盘至 `uploads/` 并返回唯一文件名。  
2) 选中增强项后，前端 POST `/augment`，传入 `filenames` 与 `augmentations` 列表。  
3) 后端用 `ThreadPoolExecutor`（<=8 worker）并行处理，生成结果存 `outputs/`；处理顺序与提交顺序一一对应。  
4) 前端调用 `/preview`、`/preview_result` 获取 Base64 预览，或调用 `/download`/`/download_all` 获取文件。

## HTTP 接口
| 方法 | 路径 | 主要入参 | 主要返回 | 说明 |
| --- | --- | --- | --- | --- |
| POST | `/upload` | `files`（multipart，多张） | 成功标记、唯一文件名数组 | 逐文件校验格式并保存；返回 `uuid4_原名` |
| POST | `/augment` | JSON：`filenames`、`augmentations` | 逐文件结果数组、成功数提示 | 并发调用数据增强；默认噪声/模糊参数写死 |
| GET | `/preview/<filename>` | 路径参数 | Base64 `data:image/jpeg;base64,...` | 读取 `uploads/` 的原图预览 |
| GET | `/preview_result/<filename>` | 路径参数 | Base64 数据 | 读取 `outputs/` 的处理结果预览 |
| GET | `/download/<filename>` | 路径参数 | 文件流 | 单文件下载（在 `outputs/` 查找） |
| POST | `/download_all` | JSON：`filenames` | ZIP 文件流 | 将给定结果文件打包 |

## 数据增强细节（真实参数）
实现位于 `data_augmentation.py`，操作顺序按传入列表依次执行，结果不断叠加。

- `rotation`：以图像中心为轴，均匀随机角度 `[-30°, 30°]`，尺寸保持原始宽高（不扩边）。  
- `flip`：随机三选一（垂直 / 水平 / 不翻转）。  
- `crop`：随机选取裁剪比例 `[0.7, 0.9]`，截取后再 resize 回原尺寸。  
- `scale`：随机缩放系数 `[0.5, 1.5]`，放大则居中裁掉多余区域，缩小则居中贴到原画布。  
- `color`（抖动）：在 PIL 空间按顺序调整亮度、对比度、饱和度，范围分别为 `[0.5,1.8]`、`[0.5,1.8]`、`[0.3,2.0]`。  
- `brightness`：亮度 `[0.5, 1.8]`。  
- `contrast`：对比度 `[0.5, 1.8]`。  
- `noise`：默认高斯噪声，均值 0、标准差 25；若传 `noise_type != 'gaussian'`，则使用 5% 像素盐噪 + 5% 像素椒噪。  
- `blur`：默认 15×15 高斯模糊；若传 `blur_type != 'gaussian'`，用 15 核大小的中值滤波。  

补充说明：
- `apply_augmentation` 的默认链路是 `['rotation','flip','crop','scale','color']`，前端会按勾选覆盖。  
- `augment_image_file` 是文件级封装：读入 -> 调用链路 -> `cv2.imwrite`。  
- 非 ndarray 图像也支持（走 Pillow 分支），但前端上传流最终都读为 ndarray。

## 前端交互要点（`templates/index.html`）
- 布局：左侧文件/增强项，中部原图 & 结果预览，右侧结果列表；顶部状态栏。  
- 上传：支持点击选择与拖拽；逐文件调用 `/upload`，成功后自动选中第一张并拉取 `/preview`。  
- 增强：收集勾选的 `input[type=checkbox]` 值；禁用状态下不允许点击。  
- 结果展示：成功项在右侧列表带 ✓，失败项带 ×；点击文件名重新加载预览。  
- 下载：成功结果集可一键 ZIP，或单文件下载（右侧入口调用后端）。  
- 体验：处理时展示旋转 loading 圈，消息区 5 秒自动消失。

## 并发与健壮性
- 并发：每次 `/augment` 请求用 `ThreadPoolExecutor`，worker 数 `min(8, CPU 核心)`；任务进度存于 `task_progress`，但当前前端未轮询此状态。  
- 容错：读取失败或文件缺失会在结果中标记错误并不中断其他文件；异常返回 JSON 错误信息。  
- 存储：上传/输出目录自动创建；文件名带 UUID，防止冲突。

## 部署 / 打包
- 生产示例：`render.yaml` 以 `gunicorn app:app` 启动，Python 3.9。  
- 本地打包：`app.spec` 供 PyInstaller 生成可执行文件，包含 `templates`、`static` 目录数据打包配置。

## 可能的扩展建议
- 替换 Base64 预览为按需缩略图接口以降低网络传输。  
- 前端增加进度轮询或 WebSocket，利用已有 `task_progress`。  
- 允许自定义每类增强的参数（范围、顺序），并持久化配置预设。

## 关键技术要点
- Flask 轻量 Web 服务：多端口部署灵活，`ThreadPoolExecutor` 并发批量处理，接口返回 JSON 结构化结果。
- OpenCV + Pillow 协同：OpenCV 负责矩阵级变换与高斯/中值滤波，Pillow 提供亮度/对比度/饱和度等色彩域增强。
- 随机增强管线：旋转、翻转、裁剪、缩放、色彩抖动、亮度/对比度、噪声、模糊按勾选顺序叠加，参数范围全随机化，生成多样性。
- 文件安全与命名：`uuid4_原名` 避免覆盖，限定扩展名与最大体积，上传/输出目录自动创建。
- 前后端联动预览：Base64 预览接口，前端拖拽上传、动态勾选、结果列表/下载，处理期 loading 与消息提示。

## 实践难点与应对
- 大文件/多文件并发：使用线程池限流（<=8 worker），避免一次性阻塞；对单个文件失败不影响其余，结果数组注明成功/失败。
- 图像尺寸保持与居中：旋转/缩放后保持原尺寸画布；缩小时居中贴图，放大时居中裁剪；裁剪后 resize 回原尺寸，确保前端显示统一。
- 色彩空间转换：Pillow 与 OpenCV 在 RGB/BGR 间转换，避免通道错位；异常捕获兜底返回原图避免崩溃。
- 预览与下载性能：Base64 方便直接嵌入，但体积较大；可扩展缩略图接口或 CDN/缓存策略减轻前端负担。
- 任务进度反馈：后端已有 `task_progress`，当前前端未轮询；可扩展定时查询或 WebSocket，增强用户体验。

## 应用前景/场景
- 计算机视觉数据集扩充：分类、检测、分割任务的快速多样化增广，提升模型泛化。
- 小样本/隐私场景：在本地或内网部署，批量生成变体，减少真实数据采集成本。
- 质检与鲁棒性验证：模拟噪声、模糊、旋转、裁剪等干扰，测试模型在复杂场景下的稳定性。
- 教学与演示：可视化展示各类增强对图像的影响，用于课堂或培训 PPT 演示。
- 生产前处理组件：可嵌入标注/训练流水线，或配合 AutoML/训练平台作为前置数据处理服务。
