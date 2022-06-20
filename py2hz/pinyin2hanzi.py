# -*- coding: utf-8 -*-
# @Time        : 2022/6/1 17:56
# @Author      : tianyunzqs
# @Description :

import os
import re
import gzip
import pickle
import collections
from pypinyin import lazy_pinyin
from Pinyin2Hanzi import DefaultDagParams, dag, simplify_pinyin
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MIN_FLOAT = -3.14e100
MIN_INF = float("-inf")

_remove_tone_dict = {
    'ā': 'a',
    'á': 'a',
    'ǎ': 'a',
    'à': 'a',
    'ē': 'e',
    'é': 'e',
    'ě': 'e',
    'è': 'e',
    'ī': 'i',
    'í': 'i',
    'ǐ': 'i',
    'ì': 'i',
    'ō': 'o',
    'ó': 'o',
    'ǒ': 'o',
    'ò': 'o',
    'ū': 'u',
    'ú': 'u',
    'ǔ': 'u',
    'ù': 'u',
    'ü': 'v',
    'ǖ': 'v',
    'ǘ': 'v',
    'ǚ': 'v',
    'ǜ': 'v',
    'ń': 'n',
    'ň': 'n',
    '': 'm',
}


class TYPinyin2Hanzi(object):
    def __init__(self, model_type='char', init=True, HMM=True):
        self.model_type = model_type
        self.init = "_init" if init else ""
        self.hmm = "_hmm" if HMM else ""
        self.states, self.trans_p, self.start_p, self.emit_p = self.load_hmm_model(self.model_type)

    @staticmethod
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

    def load_hmm_model(self, model_type='char'):
        if model_type == 'word':
            model_file_name = f'model_word{self.init}{self.hmm}.gzip'
        elif model_type == 'char':
            model_file_name = f'model_char{self.init}.gzip'
        else:
            raise Exception("Unsupported model type (must char or word).")

        with gzip.open(os.path.join(project_path, 'models', model_file_name), 'rb') as f:
            states, trans_p, start_p, emit_p = pickle.load(f)
        return states, trans_p, start_p, emit_p

    @classmethod
    def remove_pinyin_tone(cls, pinyin_s_l):
        if isinstance(pinyin_s_l, str):
            res = ""
            for p in pinyin_s_l:
                res += _remove_tone_dict.get(p, p)
            return res
        elif isinstance(pinyin_s_l, (list, set, tuple)):
            res = []
            for pp in pinyin_s_l:
                one_item = ""
                for p in pp:
                    one_item += _remove_tone_dict.get(p, p)
                res.append(one_item)
            return res
        else:
            raise Exception("Unsupported type.")

    def split_pinyin(self, pinyin_list):
        res = []
        tmp = []
        flag = True
        for pinyin in pinyin_list:
            if pinyin not in self.states:
                if tmp:
                    res.append((flag, tmp))
                    tmp = []
                flag = False
            else:
                if not flag and tmp:
                    res.append((flag, tmp))
                    tmp = []
                flag = True
            tmp.append(pinyin)
        if tmp:
            res.append((flag, tmp))
        return res

    @staticmethod
    def viterbi(obs, states, start_p, trans_p, emit_p, model_type='char'):
        V = [{}]  # tabular
        mem_path = [{}]
        all_states = trans_p.keys()
        for y in states.get(obs[0], all_states):  # init
            if model_type == 'word' and y[-1] == 'I':
                continue
            V[0][y] = start_p[y] + emit_p[y].get(obs[0], MIN_FLOAT)
            mem_path[0][y] = ''
        for t in range(1, len(obs)):
            V.append({})
            mem_path.append({})
            prev_states = [x for x in mem_path[t - 1].keys() if len(trans_p[x]) > 0]

            prev_states_expect_next = set((y for x in prev_states for y in trans_p[x].keys()))
            obs_states = set(states.get(obs[t], all_states)) & prev_states_expect_next

            if not obs_states:
                obs_states = prev_states_expect_next if prev_states_expect_next else all_states

            for y in obs_states:
                prob, state = max(
                    (V[t - 1][y0] + trans_p[y0].get(y, MIN_INF) + emit_p[y].get(obs[t], MIN_FLOAT), y0)
                    for y0 in prev_states)
                V[t][y] = prob
                mem_path[t][y] = state

        if model_type == 'word':
            last = [(V[-1][y], y) for y in mem_path[-1].keys() if y[-1] != 'B']
        elif model_type == 'char':
            last = [(V[-1][y], y) for y in mem_path[-1].keys()]
        else:
            raise Exception("Unsupported model type (must char or word).")

        prob, state = max(last)

        route = [None] * len(obs)
        i = len(obs) - 1
        while i >= 0:
            route[i] = state
            state = mem_path[i][state]
            i -= 1
        return prob, route

    def ty_pinyin2hanzi_api(self, pinyin_list):
        probs, routes = [], []
        for flag, plist in self.split_pinyin(pinyin_list):
            if flag:
                prob, route = self.viterbi(
                    plist, self.states, self.start_p, self.trans_p, self.emit_p, self.model_type)
                probs.append(prob)
                routes.extend(route)
            else:
                routes.extend(plist)
        return sum(probs) / len(probs), routes

    @classmethod
    def pinyin2hanzi_api(cls, pinyin_list, path_num=1):
        pinyin_list = [simplify_pinyin(item) for item in pinyin_list]
        dagParams = DefaultDagParams()
        result = dag(dagParams, pinyin_list, path_num=path_num, log=False)  # path_num代表候选集个数
        result = [(item.score, item.path) for item in result]
        return result


if __name__ == '__main__':
    import time
    ty_py2hz_char = TYPinyin2Hanzi(model_type='char', init=False)
    ty_py2hz_char_init = TYPinyin2Hanzi(model_type='char', init=True)

    ty_py2hz_word = TYPinyin2Hanzi(model_type='word', init=False, HMM=False)
    ty_py2hz_word_inti = TYPinyin2Hanzi(model_type='word', init=True, HMM=False)

    ty_py2hz_word_hmm = TYPinyin2Hanzi(model_type='word', init=False, HMM=True)
    ty_py2hz_word_inti_hmm = TYPinyin2Hanzi(model_type='word', init=True, HMM=True)

    while True:
        content = input("text: ")
        # content = "他认为无论是脑血栓还是脑溢血均为颅内血液循环障碍脑组织受损所致"
        if re.search(r'[\u4e00-\u9fa5]', content):
            _pinyin_list = lazy_pinyin(content)
        else:
            _pinyin_list = content.split()

        t1 = time.time()
        _prob_char, _route_char = ty_py2hz_char.ty_pinyin2hanzi_api(_pinyin_list)
        t2 = time.time()
        _prob_char_inti, _route_char_init = ty_py2hz_char_init.ty_pinyin2hanzi_api(_pinyin_list)
        t3 = time.time()
        _prob_word, _route_word = ty_py2hz_word.ty_pinyin2hanzi_api(_pinyin_list)
        t4 = time.time()
        _prob_word_inti, _route_word_inti = ty_py2hz_word_inti.ty_pinyin2hanzi_api(_pinyin_list)
        t5 = time.time()
        _prob_word_hmm, _route_word_hmm = ty_py2hz_word_hmm.ty_pinyin2hanzi_api(_pinyin_list)
        t6 = time.time()
        _prob_word_inti_hmm, _route_word_inti_hmm = ty_py2hz_word_inti_hmm.ty_pinyin2hanzi_api(_pinyin_list)
        t7 = time.time()
        _res = ty_py2hz_char.pinyin2hanzi_api(_pinyin_list)
        t8 = time.time()
        print((t2 - t1), _prob_char, _route_char)
        print((t3 - t2), _prob_char_inti, _route_char_init)
        print((t4 - t3), _prob_word, _route_word)
        print((t5 - t4), _prob_word_inti, _route_word_inti)
        print((t6 - t5), _prob_word_hmm, _route_word_hmm)
        print((t7 - t6), _prob_word_inti_hmm, _route_word_inti_hmm)
        print((t8 - t7), _res)
