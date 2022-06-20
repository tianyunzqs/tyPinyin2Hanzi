# -*- coding: utf-8 -*-
# @Time        : 2022/6/1 17:50
# @Author      : tianyunzqs
# @Description :

import os
import sys
import re
import math
import json
import time
import collections
import gzip
import pickle
import jieba
from tqdm import tqdm
from pypinyin import lazy_pinyin
from pypinyin import load_phrases_dict
from pypinyin import load_single_dict
from pypinyin_dict.phrase_pinyin_data import large_pinyin

platform = sys.platform
if platform == 'win32':
    path_THUCNews = r'D:\dataset\THUCNews'
    path_personDaily1998 = r'D:\dataset\人民日报1998\199801\1998012.txt'
    path_personDaily2014 = r'D:\dataset\人民日报2014\people-pos.txt'
    path_zhwiki = r'D:\dataset\维基百科\wiki_zh\zhwiki\zhwiki_2017_03.clean'
elif platform == 'linux':
    path_THUCNews = r'/home/zqs/dataset/THUCNews'
    path_personDaily1998 = r'/home/zqs/dataset/persondaily1998/1998012.txt'
    path_personDaily2014 = r'/home/zqs/dataset/persondaily2014/people-pos.txt'
    path_zhwiki = r'/home/zqs/dataset/zhwiki/zhwiki_2017_03.clean'
else:
    raise Exception("Unsupported platform (must win32 or linux).")


def __init__pypinyin():
    large_pinyin.load()
    load_phrases_dict({u'开户行': [[u'ka1i'], [u'hu4'], [u'hang2']]})
    load_phrases_dict({u'发卡行': [[u'fa4'], [u'ka3'], [u'hang2']]})
    load_phrases_dict({u'放款行': [[u'fa4ng'], [u'kua3n'], [u'hang2']]})
    load_phrases_dict({u'茧行': [[u'jia3n'], [u'hang2']]})
    load_phrases_dict({u'行号': [[u'hang2'], [u'ha4o']]})
    load_phrases_dict({u'各地': [[u'ge4'], [u'di4']]})
    load_phrases_dict({u'借还款': [[u'jie4'], [u'hua2n'], [u'kua3n']]})
    load_phrases_dict({u'时间为': [[u'shi2'], [u'jia1n'], [u'we2i']]})
    load_phrases_dict({u'为准': [[u'we2i'], [u'zhu3n']]})
    load_phrases_dict({u'色差': [[u'se4'], [u'cha1']]})
    load_phrases_dict({u'反弹': [[u'fa3n'], [u'ta2n']]})
    load_phrases_dict({u'反弹道': [[u'fa3n'], [u'da4n'], [u'da4o']]})
    load_phrases_dict({u'反弹导弹': [[u'fa3n'], [u'da4n'], [u'da3o'], [u'da4n']]})
    load_phrases_dict({u'反弹武器': [[u'fa3n'], [u'da4n'], [u'wu3'], [u'qi4']]})
    load_phrases_dict({u'弹棉花': [[u'ta2n'], [u'mia2n'], [u'hua1']]})
    load_phrases_dict({u'拜拜': [[u'ba4i'], [u'ba1i']]})
    load_phrases_dict({u'长文': [[u'cha2ng'], [u'wen2']]})
    load_phrases_dict({u'桔子': [[u'ju2'], [u'zi3']]})
    load_phrases_dict({u'种下': [[u'zho4ng'], [u'xia4']]})
    # 调整字的拼音顺序
    load_single_dict({ord(u'地'): u'de,di4'})


def get_sample(text):
    te = text.split()
    ttt = ""
    ind = 0
    name_list = list()
    for tt in te:
        w_p = tt.split("/", 1)
        if len(w_p) == 1:
            ttt += w_p[0]
            continue
        if w_p[0] == "" and "/" in w_p[1]:
            w_p[0] = "/"
            w_p[1] = w_p[1][1:]
        if "[" in w_p[0]:
            w_p[0] = w_p[0].replace("[", "")
        if "]" in w_p[1]:
            w_p[1] = w_p[1][:w_p[1].index("]")]
        if w_p[1] == "nr":
            name_list.append((ind, w_p[0]))
        ind += len(w_p[0])
        ttt += w_p[0]
    return ttt, name_list


def load_state(path, model_type='char'):
    state = collections.defaultdict(set)
    with open(path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            _pinyin, _chars = line.strip().split('\t')
            for _char in _chars:
                if model_type == 'word':
                    state[_pinyin] |= {(_char, BI) for BI in ['B', 'I', 'S']}
                elif model_type == 'char':
                    state[_pinyin].add(_char)
                else:
                    raise Exception("Unsupported model type (must char or word).")
    return state


def load_corpus_thuc_news(dirpath):
    for path in os.listdir(dirpath):
        if not path.endswith('txt'):
            continue
        with open(os.path.join(dirpath, path), 'r', encoding='utf-8') as f:
            for line in tqdm(f.readlines(), desc=path):
                line = line.strip()
                if not line:
                    continue
                for sent in re.split(r"[^\u4e00-\u9fa5]", line):
                    if not sent:
                        continue
                    yield sent


def load_corpus_person_daily(path, encoding):
    with open(path, 'r', encoding=encoding) as f:
        for line in tqdm(f.readlines(), desc="person_daily"):
            line, _ = get_sample(line)
            for sent in re.split(r"[^\u4e00-\u9fa5]", line):
                if not sent:
                    continue
                yield sent


def load_corpus_wiki(path):
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(tqdm(f.readlines(), desc="wiki")):
            # if i > 1000:
            #     break
            for sent in re.split(r"[^\u4e00-\u9fa5]", line):
                if not sent:
                    continue
                yield sent


def load_corpus_all(state_path, model_type='char', HMM=True):
    trans_f = collections.defaultdict(dict)
    start_f = collections.Counter()
    emit_f = collections.defaultdict(dict)

    state = load_state(state_path, model_type)

    def statistic_word(sent):
        words = jieba.lcut(sent, HMM=HMM)
        sent_pinyin = lazy_pinyin(sent)

        char_pinyin_tag = list()
        k = 0
        for word in words:
            if len(word) == 1:
                char_pinyin_tag.append((word, sent_pinyin[k], 'S'))
                # 防止state中收录不完全，或者自定义拼音
                state[sent_pinyin[k]].add((word, 'S'))
            else:
                for idx, char in enumerate(word):
                    if idx == 0:
                        char_pinyin_tag.append((char, sent_pinyin[k + idx], 'B'))
                        state[sent_pinyin[k + idx]].add((char, 'B'))
                    else:
                        char_pinyin_tag.append((char, sent_pinyin[k + idx], 'I'))
                        state[sent_pinyin[k + idx]].add((char, 'I'))
            k += len(word)

        start_f.update([(item[0], item[2]) for item in char_pinyin_tag])

        for item in char_pinyin_tag:
            if item[1] not in emit_f[(item[0], item[2])]:
                emit_f[(item[0], item[2])][item[1]] = 0
            emit_f[(item[0], item[2])][item[1]] += 1

        if len(sent) >= 2:
            i = 0
            while i < len(sent) - 1:
                item1 = (char_pinyin_tag[i][0], char_pinyin_tag[i][2])
                item2 = (char_pinyin_tag[i+1][0], char_pinyin_tag[i+1][2])
                if item2 not in trans_f[item1]:
                    trans_f[item1][item2] = 0
                trans_f[item1][item2] += 1
                i += 1

                # if sent[i + 1] not in trans_f[sent[i]]:
                #     trans_f[sent[i]][sent[i + 1]] = 0
                # trans_f[sent[i]][sent[i + 1]] += 1
                # i += 1

    def statistic_char(sent):
        sent_pinyin = lazy_pinyin(sent)

        start_f.update(sent)

        for char, char_pinyin in zip(sent, sent_pinyin):
            state[char_pinyin].add(char)  # 防止state中收录不完全，或者自定义拼音
            if char_pinyin not in emit_f[char]:
                emit_f[char][char_pinyin] = 0
            emit_f[char][char_pinyin] += 1

        if len(sent) >= 2:
            i = 0
            while i < len(sent) - 1:
                if sent[i + 1] not in trans_f[sent[i]]:
                    trans_f[sent[i]][sent[i + 1]] = 0
                trans_f[sent[i]][sent[i + 1]] += 1
                i += 1

    if model_type == 'char':
        deal_fun = statistic_char
    elif model_type == 'word':
        deal_fun = statistic_word
    else:
        raise Exception("Unsupported model type (must char or word).")

    for sentence in load_corpus_thuc_news(path_THUCNews):
        deal_fun(sentence)
    for sentence in load_corpus_person_daily(path_personDaily1998, 'gbk'):
        deal_fun(sentence)
    for sentence in load_corpus_person_daily(path_personDaily2014, 'utf-8'):
        deal_fun(sentence)
    for sentence in load_corpus_wiki(path_zhwiki):
        deal_fun(sentence)

    trans_p = collections.defaultdict(dict)
    start_p = collections.Counter()
    emit_p = collections.defaultdict(dict)

    # 转移概率
    for _tf1, _tf2 in trans_f.items():
        _tf2_total = sum(_tf2.values())
        for _tf21, _tf22 in _tf2.items():
            trans_p[_tf1][_tf21] = math.log(_tf22 / _tf2_total)

    # 初始概率
    _sf_total = sum(start_f.values())
    for _sf1, _sf2 in start_f.items():
        start_p[_sf1] = math.log(_sf2 / _sf_total)

    # 发射概率
    for _ef1, _ef2 in emit_f.items():
        _ef2_total = sum(_ef2.values())
        for _ef21, _ef22 in _ef2.items():
            emit_p[_ef1][_ef21] = math.log(_ef22 / _ef2_total)

    return state, trans_p, start_p, emit_p


def gen_trie_by_list(data_list: list) -> dict:
    trie = dict()
    for word in data_list:
        p = trie
        for w in word:
            if w not in p:
                p[w] = {}
            p = p[w]
        p[""] = word
    return trie


def extract_words_search(text, trie):
    """
    在输入文本text中抽取trie中的词语，包含位置重叠
    :param text: 输入文本
    :param trie: 词典树
    :return: 词语及其下标
    """
    result = []
    N = len(text)
    i, j = 0, 0
    p = trie
    while i < N:
        c = text[j]
        if c in p:
            p = p[c]
            if '' in p:
                result.append((p[''], i, j + 1))
            j += 1
            if j >= N:
                i += 1
                j = i
                p = trie
        else:
            p = trie
            i += 1
            j = i
    return result


def filter_words():
    words_freq = collections.Counter()
    words = [word.strip() for word in open('dict2.txt', 'r', encoding='utf-8').readlines()]
    words_trie = gen_trie_by_list(words)
    for sentence in load_corpus_thuc_news(path_THUCNews):
        words_freq.update([word for word, _, _ in extract_words_search(sentence, words_trie)])
    for sentence in load_corpus_person_daily(path_personDaily1998, 'gbk'):
        words_freq.update([word for word, _, _ in extract_words_search(sentence, words_trie)])
    for sentence in load_corpus_person_daily(path_personDaily2014, 'utf-8'):
        words_freq.update([word for word, _, _ in extract_words_search(sentence, words_trie)])
    for sentence in load_corpus_wiki(path_zhwiki):
        words_freq.update([word for word, _, _ in extract_words_search(sentence, words_trie)])

    with open('dict3.txt', 'w', encoding='utf-8') as f:
        for word, freq in words_freq.items():
            f.write(word + ' ' + str(freq) + '\n')


def train_model(model_type='char', init=False, HMM=True):
    t1 = time.time()
    if init:
        __init__pypinyin()
    suffix = "_init" if init else ""
    hmm = "_hmm" if HMM else ""
    state, trans_p, start_p, emit_p = load_corpus_all('all_char.txt', model_type=model_type, HMM=HMM)
    with gzip.open(f'model_{model_type}{suffix}{hmm}.gzip', 'wb') as f:
        pickle.dump((state, trans_p, start_p, emit_p), f)

    t2 = time.time()
    print(t2 - t1)


if __name__ == '__main__':
    # train_model(model_type='char', init=False)
    # train_model(model_type='char', init=True)
    train_model(model_type='word', init=False, HMM=False)
    train_model(model_type='word', init=False, HMM=True)
    train_model(model_type='word', init=True, HMM=False)
    train_model(model_type='word', init=True, HMM=True)
    # t1 = time.time()
    # __init__pypinyin()
    # _state, _trans_p, _start_p, _emit_p = load_corpus_all('all_char.txt', model_type='char')
    # # with open('trans_p.json', 'w', encoding='utf-8') as f:
    # #     json.dump(_trans_p, f, ensure_ascii=False, indent=2)
    # #
    # # with open('start_p.json', 'w', encoding='utf-8') as f:
    # #     json.dump(_start_p, f, ensure_ascii=False, indent=2)
    # #
    # # with open('emit_p.json', 'w', encoding='utf-8') as f:
    # #     json.dump(_emit_p, f, ensure_ascii=False, indent=2)
    #
    # with gzip.open('model_char.gzip', 'wb') as f:
    #     pickle.dump((_state, _trans_p, _start_p, _emit_p), f)
    #
    # t2 = time.time()
    # print(t2 - t1)
