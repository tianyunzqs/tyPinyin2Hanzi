# -*- coding: utf-8 -*-
# @Time        : 2022/6/1 18:51
# @Author      : tianyunzqs
# @Description :

import os
import re
import time
import json
from tqdm import tqdm
from py2hz.pinyin2hanzi import TYPinyin2Hanzi


def ty_py2hz_char_test_origin(dir_path):
    correct_num, total_num = 0, 0
    k = 0
    t1 = time.time()
    for filename in tqdm(os.listdir(dir_path)):
        if not filename.endswith('.trn'):
            continue
        # k += 1
        # if k > 500:
        #     break
        with open(os.path.join(dir_path, filename), 'r', encoding='utf-8') as f:
            char_text = f.readline().replace(' ', '').strip()
            pinyin_text = re.sub(r'[0-9]', '', f.readline().strip())
            try:
                _, route = ty_py2hz_char.ty_pinyin2hanzi_api(pinyin_text.split())
            except:
                print(char_text, filename)
                raise Exception("error")
            if len(char_text) != len(route):
                print("长度不一致", filename)
                continue
            correct_num += sum([a == b[0] for a, b in zip(char_text, route)])
            total_num += len(char_text)
    t2 = time.time()
    print("=" * 20, "ty_py2hz_char_test", "=" * 20)
    print(f'{correct_num} / {total_num} = {correct_num/total_num}')
    print(t2 - t1)


def ty_py2hz_word_test_origin(dir_path):
    correct_num, total_num = 0, 0
    k = 0
    t1 = time.time()
    for filename in tqdm(os.listdir(dir_path)):
        if not filename.endswith('.trn'):
            continue
        # k += 1
        # if k > 10:
        #     break
        with open(os.path.join(dir_path, filename), 'r', encoding='utf-8') as f:
            char_text = f.readline().replace(' ', '').strip()
            pinyin_text = re.sub(r'[0-9]', '', f.readline().strip())
            try:
                _, route = ty_py2hz_word.ty_pinyin2hanzi_api(pinyin_text.split())
            except:
                print(char_text, filename)
                raise Exception("error")
            if len(char_text) != len(route):
                print("长度不一致", filename)
                continue
            correct_num += sum([a == b[0] for a, b in zip(char_text, route)])
            total_num += len(char_text)
    t2 = time.time()
    print("=" * 20, "ty_py2hz_word_test", "=" * 20)
    print(f'{correct_num} / {total_num} = {correct_num/total_num}')
    print(t2 - t1)


def py2hz_test_origin(dir_path):
    correct_num, total_num = 0, 0
    k = 0
    t1 = time.time()
    for filename in tqdm(os.listdir(dir_path)):
        if not filename.endswith('.trn'):
            continue
        # k += 1
        # if k > 10:
        #     break
        with open(os.path.join(dir_path, filename), 'r', encoding='utf-8') as f:
            char_text = f.readline().replace(' ', '').strip()
            pinyin_text = re.sub(r'[0-9]', '', f.readline().strip())
            try:
                _, route = ty_py2hz_char.pinyin2hanzi_api(pinyin_text.split(), path_num=1)[0]
            except:
                print(char_text, filename)
                raise Exception("error")
            route = ''.join(route)
            if len(char_text) != len(route):
                print("长度不一致", filename)
                continue
            correct_num += sum([a == b[0] for a, b in zip(char_text, route)])
            total_num += len(char_text)
    t2 = time.time()
    print("=" * 20, "py2hz_test", "=" * 20)
    print(f'{correct_num} / {total_num} = {correct_num/total_num}')
    print(t2 - t1)


def ty_py2hz_char_test(path):
    correct_num, total_num = 0, 0
    t1 = time.time()
    with open(path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            line_json = json.loads(line)
            char_text = line_json['text']
            pinyin_list = line_json['pinyin']
            try:
                _, route = ty_py2hz_char.ty_pinyin2hanzi_api(pinyin_list)
            except:
                print(line_json)
                raise Exception("error")
            correct_num += sum([a == b[0] for a, b in zip(char_text, route)])
            total_num += len(char_text)
    t2 = time.time()
    print("=" * 20, "ty_py2hz_char_test", "=" * 20)
    print(f'{correct_num} / {total_num} = {correct_num/total_num}')
    print(t2 - t1)


def ty_py2hz_test(path, fun):
    correct_num, total_num = 0, 0
    k = 0
    t1 = time.time()
    with open(path, 'r', encoding='utf-8') as f:
        for line in tqdm(f.readlines()):
            # k += 1
            # if k > 10:
            #     break
            line_json = json.loads(line)
            char_text = line_json['text']
            pinyin_list = line_json['pinyin']
            try:
                _, route = fun(pinyin_list)
            except:
                print(line_json)
                raise Exception("error")
            correct_num += sum([a == b[0] for a, b in zip(char_text, route)])
            total_num += len(char_text)
    t2 = time.time()
    print("=" * 20, fun.__name__, "=" * 20)
    print(f'{correct_num} / {total_num} = {correct_num/total_num}')
    print(t2 - t1)


def py2hz_test(path):
    correct_num, total_num = 0, 0
    k = 0
    t1 = time.time()
    with open(path, 'r', encoding='utf-8') as f:
        for line in tqdm(f.readlines()):
            # k += 1
            # if k > 10:
            #     break
            line_json = json.loads(line)
            char_text = line_json['text']
            pinyin_list = line_json['pinyin']
            try:
                _, route = ty_py2hz_char.pinyin2hanzi_api(pinyin_list, path_num=1)[0]
            except:
                print(line_json)
                raise Exception("error")
            correct_num += sum([a == b for a, b in zip(char_text, ''.join(route))])
            total_num += len(char_text)
    t2 = time.time()
    print("=" * 20, "ty_py2hz_char.pinyin2hanzi_api", "=" * 20)
    print(f'{correct_num} / {total_num} = {correct_num/total_num}')
    print(t2 - t1)


if __name__ == '__main__':
    # ty_py2hz_char_test_origin(r'D:\dataset\语音识别\data_thchs30\data')
    # ty_py2hz_word_test_origin(r'D:\dataset\语音识别\data_thchs30\data')
    # py2hz_test_origin(r'D:\dataset\语音识别\data_thchs30\data')

    # 不带init的char模型
    ty_py2hz_char = TYPinyin2Hanzi(model_type='char', init=False)
    ty_py2hz_test('thchs30.txt', ty_py2hz_char.ty_pinyin2hanzi_api)

    # 带init的char模型
    ty_py2hz_char_init = TYPinyin2Hanzi(model_type='char', init=True)
    ty_py2hz_test('thchs30.txt', ty_py2hz_char_init.ty_pinyin2hanzi_api)

    # 不带init，带HMM的word模型
    ty_py2hz_word_hmm = TYPinyin2Hanzi(model_type='word', init=False, HMM=True)
    ty_py2hz_test('thchs30.txt', ty_py2hz_word_hmm.ty_pinyin2hanzi_api)

    # 不带init，不带HMM的word模型
    ty_py2hz_word = TYPinyin2Hanzi(model_type='word', init=False, HMM=False)
    ty_py2hz_test('thchs30.txt', ty_py2hz_word.ty_pinyin2hanzi_api)

    # 带init，带HMM的word模型
    ty_py2hz_word_init_hmm = TYPinyin2Hanzi(model_type='word', init=True, HMM=True)
    ty_py2hz_test('thchs30.txt', ty_py2hz_word_init_hmm.ty_pinyin2hanzi_api)

    # 带init，不带HMM的word模型
    ty_py2hz_word_init = TYPinyin2Hanzi(model_type='word', init=True, HMM=False)
    ty_py2hz_test('thchs30.txt', ty_py2hz_word_init.ty_pinyin2hanzi_api)

    # Pinyin2Hanzi模型
    ty_py2hz_char = TYPinyin2Hanzi(model_type='char', init=False)
    py2hz_test('thchs30.txt')
