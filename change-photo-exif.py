# Change photo name by photo date/time and vice versa.
# 功能【推荐】：
# 1. 根据照片创建日期，修改 exif 信息
# 2. 仅处理“tmp”文件夹
# 3. 支持 png 信息修改、支持子文件夹、增强型 EXIF 错误恢复机制

import os, piexif
import platform
from datetime import datetime
from PIL import Image

# ------------------------------------------------------------------
## general functions
# ------------------------------------------------------------------
def check_format(photo_path):
    '''
    检查文件类型是否为图片格式，返回文件后缀类型，大写字母
    '''
    return str.upper(os.path.splitext(photo_path)[1][1:])

def safe_dump_exif(exif_dict, photo_time_bytes):
    '''
    安全导出 EXIF 数据的核心拦截函数：
    处理因 iOS/macOS 私有标签或复杂字节流导致的 piexif.dump 崩溃问题。
    '''
    # 1. 预先清理最容易导致崩溃的异常标签（例如 MakerNote, SceneType, UserComment）
    tags_to_remove = [piexif.ExifIFD.MakerNote, piexif.ExifIFD.SceneType, piexif.ExifIFD.UserComment]
    for tag in tags_to_remove:
        if tag in exif_dict.get('Exif', {}):
            del exif_dict['Exif'][tag]

    try:
        # 尝试标准导出
        return piexif.dump(exif_dict)
    except Exception:
        # 2. 降级方案：如果原有其他 EXIF 结构依然损坏导致崩溃，强行剥离，构建纯净的极简 EXIF
        clean_exif = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}}
        clean_exif['0th'][piexif.ImageIFD.DateTime] = photo_time_bytes

        # 尽最大努力保留原有最核心的属性 (方向、品牌、机型)
        safe_0th_tags = [piexif.ImageIFD.Orientation, piexif.ImageIFD.Make, piexif.ImageIFD.Model]
        for tag in safe_0th_tags:
            if tag in exif_dict.get('0th', {}):
                clean_exif['0th'][tag] = exif_dict['0th'][tag]

        clean_exif['Exif'][piexif.ExifIFD.DateTimeOriginal] = photo_time_bytes
        clean_exif['Exif'][piexif.ExifIFD.DateTimeDigitized] = photo_time_bytes

        return piexif.dump(clean_exif)

def change_photo_exif(folder, name):
    '''
    修改该路径下的所有照片的时间
    '''
    # 过滤隐藏文件 (如 macOS 下的 .DS_Store)，防止意外报错
    files = [f for f in os.listdir(folder) if not f.startswith('.')]
    file_num = len(files)
    count = 0

    for photo_name in files:
        print(f'{file_num - count} Working on file: {photo_name}')
        count += 1
        photo_path = os.path.join(folder, photo_name)

        if os.path.isfile(photo_path):
            if check_format(photo_path) in ['JPG', 'JPEG', 'PNG'] and name == "tmp":
                check_photo(photo_name, photo_path, folder)
        else:
            # 文件夹递归
            change_photo_exif(photo_path, photo_name)

def check_photo(photo_name, photo_path, folder):
    '''
    获取文件创建时间，导入exif信息
    '''
    file_path = photo_path
    file_stat = os.stat(file_path)

    # 提取时间
    if platform.system() == 'Darwin':
        creation_time = file_stat.st_birthtime
    else:
        creation_time = file_stat.st_ctime

    readable_time = datetime.fromtimestamp(creation_time).strftime('%Y:%m:%d %H:%M:%S')
    photo_time_bytes = readable_time.encode('utf-8')

    try:
        fmt = check_format(file_path)

        # ----------------- 处理 PNG -----------------
        if fmt == 'PNG':
            with Image.open(file_path) as img:
                img_copy = img.copy()
                exif_data = img.info.get('exif')
                icc_profile = img.info.get('icc_profile')

            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}}
            if exif_data:
                try:
                    # 兼容部分新版 PIL 返回 Image.Exif 对象而非 bytes 的情况
                    if hasattr(exif_data, 'tobytes'):
                        exif_data = exif_data.tobytes()
                    exif_dict = piexif.load(exif_data)
                except Exception:
                    pass # 若原始 EXIF 格式极为混乱导致读取失败，则直接使用上方空字典新建

            # 修改三大时间标签
            exif_dict['0th'][piexif.ImageIFD.DateTime] = photo_time_bytes
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = photo_time_bytes
            exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = photo_time_bytes

            # 使用加强型导出函数
            exif_bytes = safe_dump_exif(exif_dict, photo_time_bytes)

            # 组织保存参数
            save_kwargs = {"exif": exif_bytes}
            if icc_profile:
                save_kwargs["icc_profile"] = icc_profile

            img_copy.save(file_path, "PNG", **save_kwargs)

            print(f'  Done, PNG photo time has been changed to {readable_time}')
            change_success.append(photo_name)

        # ----------------- 处理 JPG/JPEG -----------------
        elif fmt in ['JPG', 'JPEG']:
            try:
                exif_dict = piexif.load(file_path)
            except Exception:
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}}

            exif_dict['0th'][piexif.ImageIFD.DateTime] = photo_time_bytes
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = photo_time_bytes
            exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = photo_time_bytes

            # 使用加强型导出函数
            exif_bytes = safe_dump_exif(exif_dict, photo_time_bytes)
            piexif.insert(exif_bytes, file_path)

            print(f'  Done, JPG photo time has been changed to {readable_time}')
            change_success.append(photo_name)

    except Exception as e:
        exif_load_error.append(photo_name)
        print(f'  Exif error for {photo_name}: {e}')

# ------------------------------------------------------------------
## main
# ------------------------------------------------------------------
if __name__ == '__main__':
    folder = r'/Users/apple/Downloads/2026'  # 此处改为需要修改的照片文件夹路径
    name = ''

    no_exif, exif_load_error, no_time_in_name, change_success = [], [], [], []

    change_photo_exif(folder, name)

    # 打印最终统计信息
    if no_exif:
        print('\nPhotos_no_exif:\n', no_exif)
    if exif_load_error:
        print('\nPhotos_exif_load_error:\n', exif_load_error)
    if no_time_in_name:
        print('\nPhotos_no_time_in_name:\n', no_time_in_name)
    if change_success:
        print(f'\nPhotos_change_success (Total: {len(change_success)}):\n', change_success)