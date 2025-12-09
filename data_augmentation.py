import cv2
import numpy as np
import random
from PIL import Image, ImageEnhance

class DataAugmentation:
    def __init__(self):
        pass

    def random_rotation(self, image, angle_range=(-30, 30)):
        """随机旋转图像"""
        if isinstance(image, np.ndarray):
            height, width = image.shape[:2]
            angle = random.uniform(angle_range[0], angle_range[1])

            # 计算旋转中心
            center = (width // 2, height // 2)

            # 获取旋转矩阵
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

            # 应用旋转
            rotated = cv2.warpAffine(image, rotation_matrix, (width, height))
            return rotated
        else:
            angle = random.uniform(angle_range[0], angle_range[1])
            return image.rotate(angle, expand=True)

    def random_flip(self, image):
        """随机翻转图像（水平或垂直）"""
        flip_type = random.choice([0, 1, 2])  # 0:垂直, 1:水平, 2:不翻转

        if isinstance(image, np.ndarray):
            if flip_type == 0:
                return cv2.flip(image, 0)  # 垂直翻转
            elif flip_type == 1:
                return cv2.flip(image, 1)  # 水平翻转
            else:
                return image
        else:
            if flip_type == 0:
                return image.transpose(Image.FLIP_TOP_BOTTOM)
            elif flip_type == 1:
                return image.transpose(Image.FLIP_LEFT_RIGHT)
            else:
                return image

    def random_crop(self, image, crop_ratio=(0.7, 0.9)):
        """随机裁剪图像"""
        if isinstance(image, np.ndarray):
            height, width = image.shape[:2]
        else:
            width, height = image.size

        # 随机选择裁剪比例
        ratio = random.uniform(crop_ratio[0], crop_ratio[1])

        new_width = int(width * ratio)
        new_height = int(height * ratio)

        # 随机选择裁剪起始点
        start_x = random.randint(0, width - new_width)
        start_y = random.randint(0, height - new_height)

        if isinstance(image, np.ndarray):
            cropped = image[start_y:start_y + new_height, start_x:start_x + new_width]
            # 将裁剪后的图像调整回原始尺寸
            return cv2.resize(cropped, (width, height))
        else:
            cropped = image.crop((start_x, start_y, start_x + new_width, start_y + new_height))
            return cropped.resize((width, height))

    def random_scale(self, image, scale_range=(0.5, 1.5)):
        """随机缩放图像（保持在原图尺寸的画布内）"""
        scale = random.uniform(scale_range[0], scale_range[1])

        if isinstance(image, np.ndarray):
            orig_height, orig_width = image.shape[:2]
            new_width = int(orig_width * scale)
            new_height = int(orig_height * scale)

            # 缩放图像
            scaled = cv2.resize(image, (new_width, new_height))

            # 创建与原图相同尺寸的画布
            result = np.zeros((orig_height, orig_width, image.shape[2]), dtype=image.dtype)

            if scale > 1.0:
                # 放大：裁剪中心部分
                start_x = (new_width - orig_width) // 2
                start_y = (new_height - orig_height) // 2
                result = scaled[start_y:start_y + orig_height, start_x:start_x + orig_width]
            else:
                # 缩小：居中放置
                start_x = (orig_width - new_width) // 2
                start_y = (orig_height - new_height) // 2
                result[start_y:start_y + new_height, start_x:start_x + new_width] = scaled

            return result
        else:
            orig_width, orig_height = image.size
            new_width = int(orig_width * scale)
            new_height = int(orig_height * scale)

            # 缩放图像
            scaled = image.resize((new_width, new_height))

            # 创建与原图相同尺寸的画布
            from PIL import Image
            result = Image.new(image.mode, (orig_width, orig_height), (0, 0, 0))

            if scale > 1.0:
                # 放大：裁剪中心部分
                start_x = (new_width - orig_width) // 2
                start_y = (new_height - orig_height) // 2
                cropped = scaled.crop((start_x, start_y, start_x + orig_width, start_y + orig_height))
                result = cropped
            else:
                # 缩小：居中放置
                start_x = (orig_width - new_width) // 2
                start_y = (orig_height - new_height) // 2
                result.paste(scaled, (start_x, start_y))

            return result

    def color_jitter(self, image, brightness_range=(0.5, 1.8),
                    contrast_range=(0.5, 1.8), saturation_range=(0.3, 2.0)):
        """颜色抖动（亮度、对比度、饱和度）"""
        try:
            if isinstance(image, np.ndarray):
                # 转换为PIL图像进行颜色调整
                image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                image_pil = image.copy()

            # 随机调整亮度（更大范围）
            brightness_factor = random.uniform(brightness_range[0], brightness_range[1])
            enhancer = ImageEnhance.Brightness(image_pil)
            image_pil = enhancer.enhance(brightness_factor)

            # 随机调整对比度（更大范围）
            contrast_factor = random.uniform(contrast_range[0], contrast_range[1])
            enhancer = ImageEnhance.Contrast(image_pil)
            image_pil = enhancer.enhance(contrast_factor)

            # 随机调整饱和度（更大范围）
            saturation_factor = random.uniform(saturation_range[0], saturation_range[1])
            enhancer = ImageEnhance.Color(image_pil)
            image_pil = enhancer.enhance(saturation_factor)

            if isinstance(image, np.ndarray):
                # 转换回OpenCV格式
                return cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
            else:
                return image_pil
        except Exception as e:
            print(f"颜色抖动处理失败: {e}")
            return image

    def adjust_brightness(self, image):
        """随机调节亮度"""
        brightness = random.uniform(0.5, 1.8)
        if isinstance(image, np.ndarray):
            image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            image_pil = image.copy()

        enhancer = ImageEnhance.Brightness(image_pil)
        result = enhancer.enhance(brightness)

        if isinstance(image, np.ndarray):
            return cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)
        return result

    def adjust_contrast(self, image):
        """随机调节对比度"""
        contrast = random.uniform(0.5, 1.8)
        if isinstance(image, np.ndarray):
            image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            image_pil = image.copy()

        enhancer = ImageEnhance.Contrast(image_pil)
        result = enhancer.enhance(contrast)

        if isinstance(image, np.ndarray):
            return cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)
        return result

    def add_noise(self, image, noise_type='gaussian'):
        """添加噪声"""
        if isinstance(image, np.ndarray):
            img_array = image.copy()
        else:
            img_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        if noise_type == 'gaussian':
            # 高斯噪声
            noise = np.random.normal(0, 25, img_array.shape).astype(np.uint8)
            result = cv2.add(img_array, noise)
        else:
            # 椒盐噪声
            result = img_array.copy()
            num_salt = np.ceil(0.05 * img_array.size * 0.5)
            coords = [np.random.randint(0, i - 1, int(num_salt)) for i in img_array.shape]
            result[coords[0], coords[1], :] = 255

            num_pepper = np.ceil(0.05 * img_array.size * 0.5)
            coords = [np.random.randint(0, i - 1, int(num_pepper)) for i in img_array.shape]
            result[coords[0], coords[1], :] = 0

        if not isinstance(image, np.ndarray):
            return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
        return result

    def apply_blur(self, image, blur_type='gaussian'):
        """应用模糊效果"""
        if isinstance(image, np.ndarray):
            img_array = image.copy()
        else:
            img_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        if blur_type == 'gaussian':
            result = cv2.GaussianBlur(img_array, (15, 15), 0)
        else:
            result = cv2.medianBlur(img_array, 15)

        if not isinstance(image, np.ndarray):
            return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
        return result

    def apply_augmentation(self, image, augmentations=['rotation', 'flip', 'crop', 'scale', 'color'], **params):
        """应用指定的数据增强方法"""
        result = image.copy() if hasattr(image, 'copy') else image

        for aug in augmentations:
            if aug == 'rotation':
                result = self.random_rotation(result)
            elif aug == 'flip':
                result = self.random_flip(result)
            elif aug == 'crop':
                result = self.random_crop(result)
            elif aug == 'scale':
                result = self.random_scale(result)
            elif aug == 'color':
                result = self.color_jitter(result)
            elif aug == 'brightness':
                result = self.adjust_brightness(result)
            elif aug == 'contrast':
                result = self.adjust_contrast(result)
            elif aug == 'noise':
                noise_type = params.get('noise_type', 'gaussian')
                result = self.add_noise(result, noise_type)
            elif aug == 'blur':
                blur_type = params.get('blur_type', 'gaussian')
                result = self.apply_blur(result, blur_type)

        return result

    def augment_image_file(self, input_path, output_path, augmentations=['rotation', 'flip', 'crop', 'scale', 'color']):
        """处理图像文件"""
        try:
            # 读取图像
            image = cv2.imread(input_path)
            if image is None:
                raise ValueError(f"无法读取图像: {input_path}")

            # 应用增强
            augmented = self.apply_augmentation(image, augmentations)

            # 保存结果
            cv2.imwrite(output_path, augmented)
            return True
        except Exception as e:
            print(f"处理图像时出错: {e}")
            return False