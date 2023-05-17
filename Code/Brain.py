import datetime
from collections import Counter
import os
import pandas as pd
import re
from typing import Any, Dict, List, NewType, Tuple


ColumnIndex = NewType("ColumnIndex", str)
Token = NewType("Token", str)
TokenCount = NewType("TokenCount", int)
TokenisedSentence = List[Token]
TokensByColumn = Dict[ColumnIndex, TokenisedSentence]
SentencesByLength = Dict[TokenCount, List[TokenisedSentence]]
WordCombination = Tuple[int, Token, int]


def get_frequecy_vector(
    sentences: List[str],
    filter: List[str],
    delimiter: List[str],
    dataset: str,
) -> Tuple[Any, Any, Any]:
    """
    根据日志生成每条日志的频次向量。
    """
    # Mapping from sentence length to a list of sentences in token-representation.
    sentences_by_length: SentencesByLength = {}
    # Mapping from 'column' index to list of tokens.
    tokens_by_column: TokensByColumn = {}
    for line_num, s in enumerate(sentences):
        # Apply any regex filters, replacing them by a placeholder.
        for rgex in filter:
            s = re.sub(rgex, "<*>", s)
        # Remove any delimiters.
        for de in delimiter:
            s = re.sub(de, "", s)

        # Run any dataset specific regex replacements.
        if dataset == "HealthApp":
            s = re.sub(":", ": ", s)
            s = re.sub("=", "= ", s)
            s = re.sub("\|", "| ", s)
        if dataset == "Android":
            s = re.sub("\(", "( ", s)
            s = re.sub("\)", ") ", s)
        if dataset == "Android":
            s = re.sub(":", ": ", s)
            s = re.sub("=", "= ", s)
        if dataset == "HPC":
            s = re.sub("=", "= ", s)
            s = re.sub("-", "- ", s)
            s = re.sub(":", ": ", s)
        if dataset == "BGL":
            s = re.sub("=", "= ", s)
            s = re.sub("\.\.", ".. ", s)
            s = re.sub("\(", "( ", s)
            s = re.sub("\)", ") ", s)
        if dataset == "Hadoop":
            s = re.sub("_", "_ ", s)
            s = re.sub(":", ": ", s)
            s = re.sub("=", "= ", s)
            s = re.sub("\(", "( ", s)
            s = re.sub("\)", ") ", s)
        if dataset == "HDFS":
            s = re.sub(":", ": ", s)
        if dataset == "Linux":
            s = re.sub("=", "= ", s)
            s = re.sub(":", ": ", s)
        if dataset == "Spark":
            s = re.sub(":", ": ", s)
        if dataset == "Thunderbird":
            s = re.sub(":", ": ", s)
            s = re.sub("=", "= ", s)
        if dataset == "Windows":
            s = re.sub(":", ": ", s)
            s = re.sub("=", "= ", s)
            s = re.sub("\[", "[ ", s)
            s = re.sub("]", "] ", s)
        if dataset == "Zookeeper":
            s = re.sub(":", ": ", s)
            s = re.sub("=", "= ", s)

        # Replace commas with comma + space.
        s = re.sub(",", ", ", s)
        s = re.sub(" +", " ", s)
        s_tokens = [Token(x) for x in s.split(" ")]
        # Add line number to the beginning of the sentence.
        s_tokens.insert(0, Token(str(line_num)))
        # Add tokens to the map of tokens by column.
        for i, token in enumerate(s_tokens):
            tokens_by_column.setdefault(ColumnIndex(str(i)), []).append(token)
        # Add sentence to the map of sentences by length.
        token_count = TokenCount(len(s_tokens))
        sentences_by_length.setdefault(token_count, []).append(s_tokens)
    max_length = max(sentences_by_length.keys())

    # Mapping from (column_idx, token) tuple to frequency.
    # This basically counts how many times a word appears in a column.
    word_frequencies: Dict[Tuple[ColumnIndex, Token], int] = {}

    # Note: slight improvement over original, start at 1 rather than 0
    # because the 0th column just contains the line number.
    for column_idx in range(1, max_length):
        idx_str = ColumnIndex(str(column_idx))
        # Count the frequency of each word in the current column.
        for token in tokens_by_column[idx_str]:
            word = (idx_str, token)
            if word in word_frequencies.keys():  # 判断当前key是否已经存在
                word_frequencies[word] += 1
            else:
                word_frequencies[word] = 1

    # Mapping from sentence length to a list of sentences represented by word combinations.
    combinations: Dict[TokenCount, List[List[WordCombination]]] = {}
    # Mapping from sentence length to a nested list, where the outer list
    # represents sentences and the inner lists represent the frequency of
    # each word in the sentence.
    frequencies: Dict[TokenCount, List[List[int]]] = {}

    for key, tokenised_sentences in sentences_by_length.items():
        for sentence in tokenised_sentences:
            column_idx: int = 0
            sentence_word_combinations: List[WordCombination] = []
            sentence_word_frequencies: List[int] = []
            for token in sentence[1:]:
                word = (ColumnIndex(str(column_idx+1)), token)
                word_frequency = word_frequencies[word]
                combination = (word_frequency, token, column_idx)
                sentence_word_combinations.append(combination)
                sentence_word_frequencies.append(word_frequency)
                column_idx += 1
            combinations.setdefault(key, []).append(sentence_word_combinations)
            frequencies.setdefault(key, []).append(sentence_word_frequencies)
    return sentences_by_length, combinations, frequencies


def parse1(wordlist, frequency):
    """
    frequency为建立好的频次向量
    """
    index_list = []
    wait_set = {}
    count = 0
    for fre in frequency:
        number = Counter(fre)
        result = number.most_common()
        sorted_result = sorted(result, key=lambda tup: tup[0], reverse=True)
        sorted_result_reverse = sorted(result, key=lambda tup: tup[0])
        if result[0] == sorted_result[0]:
            inde = []
            for index, token in enumerate(fre):
                if token == result[0][0]:
                    inde.append(index)
            index_list.append(inde)
        else:
            index_list.append("placeholder")
            wait_set.setdefault(count, []).append(sorted_result_reverse)
        count += 1
    return index_list, wait_set


def tuple_generate(wordlist, frequency, frequency_common):
    sorted_frequency = {}
    sorted_frequency_common = {}
    sorted_frequency_tuple = {}
    for key in wordlist.keys():
        root_set = {""}
        for fre in frequency[key]:
            sorted_fre_reverse = sorted(fre, key=lambda tup: tup[0], reverse=True)
            root_set.add(sorted_fre_reverse[0])
            sorted_frequency.setdefault(key, []).append(sorted_fre_reverse)
        for fc in frequency_common[key]:
            number = Counter(fc)
            result = number.most_common()
            sorted_result = sorted(result, key=lambda tup: tup[1], reverse=True)
            sorted_fre = sorted(result, key=lambda tup: tup[0], reverse=True)
            sorted_frequency_common.setdefault(key, []).append(sorted_result)
            sorted_frequency_tuple.setdefault(key, []).append(sorted_fre)
    return sorted_frequency, sorted_frequency_common, sorted_frequency_tuple


class tupletree:
    def __init__(
        self,
        sorted_frequency,
        sorted_frequency_common,
        sorted_frequency_tuple,
        frequency,
        wordlist,
    ):
        self.sorted_frequency = sorted_frequency
        self.sorted_frequency_common = sorted_frequency_common
        self.sorted_frequency_tuple = sorted_frequency_tuple
        self.frequency = frequency
        self.wordlist = wordlist

    def find_root(self, threshold_per):
        root_set_detail = {}
        detail_inorder = {}
        root_set = {}
        i = 0
        for fc in self.sorted_frequency_common:
            count = self.wordlist[i]
            threshold = (max(fc, key=lambda tup: tup[0])[0]) * threshold_per
            m = 0
            for fc_w in fc:
                if fc_w[0] >= threshold:
                    a = self.sorted_frequency[i].append((int(count[0]), -1, -1))
                    root_set_detail.setdefault(fc_w, []).append(
                        self.sorted_frequency[i]
                    )
                    root_set.setdefault(fc_w, []).append(self.sorted_frequency_tuple[i])
                    detail_inorder.setdefault(fc_w, []).append(self.frequency[i])
                    break
                if fc_w[0] >= m:
                    candidate = fc_w
                    m = fc_w[0]
                if fc_w == fc[len(fc) - 1]:
                    root_set_detail.setdefault(candidate, []).append(
                        self.sorted_frequency[i]
                    )
                    root_set.setdefault(candidate, []).append(
                        self.sorted_frequency_tuple[i]
                    )
                    detail_inorder.setdefault(fc_w, []).append(self.frequency[i])
            i += 1
        return root_set_detail, root_set, detail_inorder

    def up_split(self, root_set_detail, root_set):
        new_root_set_detail = {}
        for key in root_set.keys():
            tree_node = root_set[key]
            father_count = []
            for node in tree_node:
                pos = node.index(key)
                for i in range(pos):
                    father_count.append(node[i])
            father_set = set(father_count)
            for father in father_set:
                if father_count.count(father) == key[0]:
                    continue
                else:
                    for i in range(len(root_set_detail[key])):
                        for k in range(len(root_set_detail[key][i])):
                            if father[0] == root_set_detail[key][i][k]:
                                root_set_detail[key][i][k] = (
                                    root_set_detail[key][i][k][0],
                                    "<*>",
                                    root_set_detail[key][i][k][2],
                                )
                    break
        return root_set_detail

    def down_split(self, root_set_detail, root_set, threshold, fr_inorder):
        for key in root_set.keys():
            thre = threshold
            detail_order = fr_inorder[key]
            m = []
            child = {}
            variable = {""}
            variable.remove("")
            variable_set = {""}
            variable_set.remove("")
            m_count = 0
            fist_sentence = detail_order[0]
            for det in fist_sentence:
                if det[0] != key[0]:
                    m.append(m_count)
                m_count += 1
            for i in m:
                for node in detail_order:
                    if i < len(node):
                        # child.setdefault(i, []).append(tuple([n for n in node[:i+1]]))
                        child.setdefault(i, []).append(node[i][1])
            v_flag = 0

            for i in m:
                next = {""}
                next.remove("")
                result = set(child[i])
                freq = len(result)
                if freq >= thre:
                    variable = variable.union(result)

                v_flag += 1
            i = 0
            while i < len(root_set_detail[key]):
                j = 0
                while j < len(root_set_detail[key][i]):
                    if isinstance(root_set_detail[key][i][j], tuple):
                        if root_set_detail[key][i][j][1] in variable:
                            root_set_detail[key][i][j] = (
                                root_set_detail[key][i][j][0],
                                "<*>",
                                root_set_detail[key][i][j][2],
                            )
                    j += 1
                i += 1
        return root_set_detail


def output_result(wordlist, parse_result, tag):
    template_set = {}
    for key in parse_result.keys():
        for pr in parse_result[key]:
            sort = sorted(pr, key=lambda tup: tup[2])
            i = 1
            template = []

            while i < len(sort):
                this = sort[i][1]
                if bool(re.search(r"/", this)):
                    template.append("<*>")
                    i += 1
                    continue
                if this.isdigit():
                    template.append("<*>")
                    i += 1
                    continue
                if bool("<*>" in this):
                    template.append("<*>")
                    i += 1
                    continue
                if tag == 1:
                    if bool(re.search(r"\d", this)):
                        template.append("<*>")
                        i += 1
                        continue
                template.append(sort[i][1])
                i += 1

            template = tuple(template)
            template_set.setdefault(template, []).append(pr[len(pr) - 1][0])
    return template_set


def parse(
    sentences: List[str],
    filter: List[str],
    dataset: str,
    threshold: int,
    delimiter: List[str],
    tag: int,
    starttime: datetime.datetime,
    efficiency: bool,
):
    wordlist, frequency, frequency_common = get_frequecy_vector(
        sentences, filter, delimiter, dataset
    )
    sorted_frequency, sorted_frequency_common, sorted_frequency_tuple = tuple_generate(
        wordlist, frequency, frequency_common
    )
    df_example = pd.read_csv(
        "../logs/" + dataset + "/" + dataset + "_2k.log_structured.csv",
        encoding="UTF-8",
        header=0,
    )
    structured = df_example["EventId"]
    template = df_example["EventTemplate"]
    a = list(template)
    group_accuracy_correct = 0
    template_set = {}
    loglines = 0
    correct_choose = 0
    for key in wordlist.keys():
        sf = sorted_frequency[key]
        sfc = sorted_frequency_common[key]
        sft = sorted_frequency_tuple[key]
        fr = frequency[key]
        wl = wordlist[key]
        Tree = tupletree(sf, sfc, sft, fr, wl)
        root_set_detail, root_set, fr_inorder = Tree.find_root(0)
        """
        ### code for root node choose evaluation.
        for k in root_set_detail:
            choose_flag=1
            for log in root_set_detail[k]:
                c=0
                loglines+=1
                while c <len(log)-1:
                    if log[c][0]==k[0]:
                        if "<*>" in log[c][1] and log[c][1] not in template[log[len(log)-1][0]]:
                            choose_flag=0
                    if choose_flag==0:
                        break
                    c+=1
                if choose_flag == 0:
                    break
                correct_choose+=1
        """

        root_set_detail = Tree.up_split(root_set_detail, root_set)
        parse_result = Tree.down_split(root_set_detail, root_set, threshold, fr_inorder)
        template_set.update(output_result(wordlist, parse_result, tag))
    """
    ### code for root node choose evaluation.
    print(
        "correct choose root noed ratio ==" + str(correct_choose / loglines) + "===detail===correct_choose:" + str(
            correct_choose) + " logline:" + str(loglines))
    """
    endtime = datetime.datetime.now()
    print("### Time cost4 ###" + str(endtime - starttime))
    if efficiency == True:
        return endtime
    """
    output parsing result
    """
    template = sentences
    template_num = 0
    group_accuracy_correct = 0
    for k1 in template_set.keys():
        group_accuracy = {""}
        group_accuracy.remove("")
        for i in template_set[k1]:
            group_accuracy.add(structured[i])
            template[i] = k1
            template_num += 1
        if len(group_accuracy) == 1:
            count = a.count(a[i])
            if count == len(template_set[k1]):
                group_accuracy_correct += len(template_set[k1])
    df_example["Template"] = template
    df_example.to_csv("../Parseresult/" + dataset + "result.csv", index=False)
    with open("../Parseresult/" + dataset + "_template.csv", "w") as f:
        template_num = 0
        for k1 in template_set.keys():
            f.write(" ".join(list(k1)))
            f.write("  " + str(len(template_set[k1])))
            f.write("\n")
        f.close()

    Groupaccuracy = group_accuracy_correct / 2000
    return Groupaccuracy


class format_log:  # this part of code is from LogPai https://github.com/LogPai
    def __init__(self, log_format, indir="./"):
        self.path = indir
        self.logName = None
        self.df_log = None
        self.log_format = log_format

    def format(self, logName):
        self.logName = logName

        self.load_data()

        return self.df_log

    def generate_logformat_regex(self, logformat):
        """Function to generate regular expression to split log messages"""
        headers = []
        splitters = re.split(r"(<[^<>]+>)", logformat)
        regex = ""
        for k in range(len(splitters)):
            if k % 2 == 0:
                splitter = re.sub(" +", "\\\s+", splitters[k])
                regex += splitter
            else:
                header = splitters[k].strip("<").strip(">")
                regex += "(?P<%s>.*?)" % header
                headers.append(header)
        regex = re.compile("^" + regex + "$")
        return headers, regex

    def log_to_dataframe(self, log_file, regex, headers, logformat):
        """Function to transform log file to dataframe"""
        log_messages = []
        linecount = 0
        with open(log_file, "r", encoding="UTF-8") as fin:
            for line in fin.readlines():
                try:
                    match = regex.search(line.strip())
                    message = [match.group(header) for header in headers]
                    log_messages.append(message)
                    linecount += 1
                except Exception as e:
                    pass
                if linecount == 2000000:
                    break
        logdf = pd.DataFrame(log_messages, columns=headers)
        logdf.insert(0, "LineId", None)
        logdf["LineId"] = [i + 1 for i in range(linecount)]
        return logdf

    def load_data(self):
        headers, regex = self.generate_logformat_regex(self.log_format)
        self.df_log = self.log_to_dataframe(
            os.path.join(self.path, self.logName), regex, headers, self.log_format
        )


"""
              else:
                  print(k1)
                  print(str(count)+'ground truth count')
                  print(len(template_set[k1]))
          else:
              print(k1)
              print('wrong merge'+str(len(group_accuracy)))

          """


# SB.get_eval_metric('../SaveFiles&Output/Parseresult/Proxifier/Proxifier88.csv','../SaveFiles&Output/Parseresult/Proxifier/template.csv')
"""

    'HDFS': {
        'log_file': 'HDFS/HDFS_2k.log',
        'log_format': '<Date> <Time> <Pid> <Level> <Component>: <Content>',
        'delimiter': ['[,!?=]']
    },
"""
