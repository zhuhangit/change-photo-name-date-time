# Change photo name by photo date/time and vice versa.
# 功能：
# 1. 检查照片Exif中的是否存在日期信息
# 2. 缺失日期照片拷贝至“tmp”文件夹，保留文件创建日期
# 3. 支持 png 格式校验、支持子文件夹

import os, time, piexif, re
import re
import shutil
from sys import exception

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


def check_exif(photo_path):
    '''
    检查文件是否有Exif，Exif中是否有拍摄时间
    '''
    try:
        exif_dict = piexif.load(photo_path)  # 读取Exif信息
        return piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']
    except:
        return False


def get_time_from_exif(photo_path):
    '''
    从Exif中提取照片时间，返回格式为2021:04:22 07:07:07
    '''
    exif_dict = piexif.load(photo_path)  # 照片的Exif
    photo_time = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal]  # bytes
    photo_time = bytes.decode(photo_time)  # 解码后为2021:04:22 07:07:07
    return photo_time


def check_photo_exif(folder):
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
        if check_format(photo_path) in ['JPG', 'JPEG', 'PNG']:
            check_photo(photo_name, photo_path, folder)
        else:
            if not path.isfile(os.path.join(folder, photo_name)) and not photo_name.__eq__('tmp'):
                # 文件夹递归
                check_photo_exif(os.path.join(folder, photo_name))


def check_photo(photo_name, photo_path, folder):
    '''
    读取exif信息
    '''
    try:
        file_path = photo_path
        with Image.open(file_path) as img:
            # 确保图像是 PNG 格式
            if img.format == 'PNG':
                # 检查是否有 EXIF 数据
                exif_data = img.info.get('exif')
                # 将 EXIF 数据转换为字典
                exif_dict = piexif.load(exif_data)
                # 检查并修改 DateTimeOriginal 字段
                datetime_original = exif_dict['Exif'].get(piexif.ExifIFD.DateTimeOriginal)
                # png存在空值
                if datetime_original == None:
                    raise Exception(None)
                print('\t png DateTimeOriginal', datetime_original)
            else:
                exif_dict = piexif.load(photo_path)  # 读取现有Exif信息
                # 设置Exif信息，注意DateTime在ImageIFD里面
                print('\t 0th', exif_dict['0th'][piexif.ImageIFD.DateTime])
                print('\t Exif DateTimeOriginal', exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal])
                print('\t Exif DateTimeDigitized', exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized])
    except Exception as ex:
        exif_load_error.append(photo_name)
        print('  Exif load error：',ex)
        # 源文件路径
        source_file = photo_path
        # 目标目录
        target_directory = folder + '/tmp/'
        # 创建目标目录（如果不存在）
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)
        # 复制文件到目标目录，同时保留元数据
        shutil.copy2(source_file, target_directory)
        print("\t 文件复制成功！")


# ------------------------------------------------------------------
## main
# ------------------------------------------------------------------
if __name__ == '__main__':
    '''
    folder: 需要检查的照片文件夹路径
    '''
    folder = r'/Users/apple/Desktop/2026'  # 此处改为需要修改的照片文件夹路径
    no_exif, exif_load_error, no_time_in_name = [[] for i in range(3)]
    check_photo_exif(folder)

    # 统计不能执行的照片文件
    if no_exif:
        print('Photos_no_exif:\n', no_exif)
    if exif_load_error:
        print('Photos_exif_load_error:\n', exif_load_error.__len__(), exif_load_error)
    if no_time_in_name:
        print('Photos_no_time_in_name:\n', no_time_in_name)
