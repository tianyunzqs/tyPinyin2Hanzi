# -*- coding: utf-8 -*-
# @Time        : 2022/6/8 11:37
# @Author      : tianyunzqs
# @Description :

import os
import re
import time
import json
from tqdm import tqdm


def ty_py2hz_char_test(dir_path):
    char_pinyin = []
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
            if len(char_text) != len(pinyin_text.split()):
                print("长度不一致", filename)
                continue
            char_pinyin.append({'text': char_text, 'pinyin': pinyin_text.split()})

    with open('thchs30.txt', 'w', encoding='utf-8') as f:
        for item in char_pinyin:
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')
    t2 = time.time()
    print(t2 - t1)


if __name__ == '__main__':
    ty_py2hz_char_test(r'D:\dataset\语音识别\data_thchs30\data')
