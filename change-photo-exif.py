# Change photo name by photo date/time and vice versa.
# 功能：
# 1. 根据照片名称修改照片日期：根据照片名中包含的日期信息，修改照片Exif中的日期信息
# 2. 根据照片日期修改照片名称：根据照片Exif中的日期信息，按照统一格式重命名照片

import os, time, piexif, re
import platform
import re
import shutil
import time
from datetime import datetime
from sys import excepthook

from PIL import Image
from os import path


# ------------------------------------------------------------------
## general functions
# ------------------------------------------------------------------
def check_format(photo_path):
    '''
    检查文件类型是否为图片格式，返回文件后缀类型，大写字母
    '''
    return str.upper(os.path.splitext(photo_path)[1][1:])


def change_photo_exif(folder, name):
    '''
    修改该路径下的所有JPG照片的时间
    '''
    count = 0
    file_num = len(os.listdir(folder))
    for photo_name in os.listdir(folder):
        # 展示剩余文件数量 + 正在处理的文件名
        print(f'{file_num - count} Working on file: {photo_name}')
        count += 1
        photo_path = os.path.join(folder, photo_name)  # 照片的绝对路径
        # 仅处理 tmp 文件夹
        if check_format(photo_path) in ['JPG', 'JPEG', 'PNG'] and name.__eq__("tmp"):
            check_photo(photo_name, photo_path, folder)
        else:
            if not path.isfile(os.path.join(folder, photo_name)):
                # 文件夹递归
                change_photo_exif(os.path.join(folder, photo_name), photo_name)


def check_photo(photo_name, photo_path, folder):
    '''
    获取文件创建时间，导入exif信息
    '''
    file_path = photo_path
    # 获取文件状态信息
    file_stat = os.stat(file_path)
    # 获取创建时间（Windows 下是 st_ctime）
    # 根据操作系统选择使用的属性
    if platform.system() == 'Darwin':
        # macOS 下, st_birthtime 是创建时间
        creation_time = file_stat.st_birthtime
    else:
        creation_time = file_stat.st_ctime
    # 将时间戳转换为可读格式
    readable_time = datetime.fromtimestamp(creation_time).strftime('%Y:%m:%d %H:%M:%S')
    photo_time = readable_time
    try:
        with Image.open(file_path) as img:
            # 确保图像是 PNG 格式
            if img.format == 'PNG':
                # 检查是否有 EXIF 数据
                exif_data = img.info.get('exif')
                if exif_data is None:
                    # 创建初始 EXIF 数据字典
                    exif_dict = {
                        "0th": {},
                        "Exif": {},
                        "GPS": {},
                        "Interop": {},
                        "1st": {}
                    }
                else:
                    # 将 EXIF 数据转换为字典
                    exif_dict = piexif.load(exif_data)
                # 检查并修改 DateTimeOriginal 字段
                datetime_original = exif_dict['Exif'].get(piexif.ExifIFD.DateTimeOriginal)
                if datetime_original:
                    print(f"原始时间: {datetime_original.decode('utf-8')}")
                # 修改时间，例如更改为当前时间
                new_datetime = photo_time.encode('utf-8')  # 使用字节字符串格式
                exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = new_datetime
                # 保存修改后的 EXIF 数据
                exif_bytes = piexif.dump(exif_dict)
                # 更新图像的 EXIF 数据
                img.save(file_path, exif=exif_bytes)
                print(f'  Done, photo time has been changed to {new_datetime}')
            else:
                exif_dict = piexif.load(photo_path)  # 读取现有Exif信息
                # 设置Exif信息，注意DateTime在ImageIFD里面
                exif_dict['0th'][piexif.ImageIFD.DateTime] = photo_time
                exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = photo_time
                exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = photo_time
                try:
                    exif_bytes = piexif.dump(exif_dict)
                    piexif.insert(exif_bytes, photo_path)  # 插入Exif信息
                    print(f'  Done, photo time has been changed to {photo_time}')
                    change_success.append(photo_name)
                except:
                    print(f'  Exif dump error')
    except Exception as e:
        exif_load_error.append(photo_name)
        print('  Exif load error：', e)


# ------------------------------------------------------------------
## main
# ------------------------------------------------------------------
if __name__ == '__main__':
    '''
    folder: 需要修改的照片文件夹路径
    '''
    folder = r'/Users/apple/Desktop/2016'  # 此处改为需要修改的照片文件夹路径
    # folder += r'/tmp'  # 默认使用临时文件夹
    name = ''
    no_exif, exif_load_error, no_time_in_name, change_success = [[] for i in range(4)]
    change_photo_exif(folder, name)

    # 统计不能执行的照片文件
    if no_exif:
        print('Photos_no_exif:\n', no_exif)
    if exif_load_error:
        print('Photos_exif_load_error:\n', exif_load_error)
    if no_time_in_name:
        print('Photos_no_time_in_name:\n', no_time_in_name)
    if change_success:
        print('Photos_change_success:\n', len(change_success), change_success)
