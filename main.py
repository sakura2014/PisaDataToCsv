#!/usr/bin/python
# coding=utf-8
"""
pisa 2000から2012までのtxtファイルをcsvファイルに変換します。
WindowsかLinuxで動作します（Macは不明）
"""

import csv
import hashlib
import json
import os
import sys
import zipfile
from urllib import parse
from urllib import request


def reporthook(blocknum, blocksize, size):
    """
    ダウンロード進捗表示
    """
    part_size = blocksize * blocknum
    if part_size > size:
        part_size = size
    progress = part_size / size * 100
    msg = "\r進捗: {:.0f}% ({}/{})".format(progress, part_size, size)
    print(msg, end="")


def unzip(filename, path="."):
    """
    unzip
    """
    with zipfile.ZipFile(filename, "r") as zip_file:
        zip_file.extractall(path=path)


def md5sum(filename):
    """
    md5sum
    """
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def download(url, md5):
    """
    download
    """
    filename = parse.urlparse(url)[2].split("/")[-1]
    if (os.path.isfile(filename)) and (md5sum(filename) == md5):
        print("[{}] が既に存在します。\n".format(filename))
    else:
        print("[{}]をダウンロードします。".format(filename))
        request.urlretrieve(url, filename, reporthook)
        print("\n")
    # unzip file
    if os.path.splitext(filename)[-1] == ".zip":
        unzip(filename)


def getsps(sps):
    """
    sps fileを読む。
    """
    start_list = []
    end_list = []
    var_list = []
    for textbr in open(sps, "rb"):
        text = textbr.decode("utf-8", "ignore")
        spss = text.strip(" /.\n")
        line = spss.replace("-", " - ")
        if len(line.split()) >= 4:
            if line.split()[1].isdigit() and line.split()[3].isdigit():
                start_list.append(line.split()[1])
                end_list.append(line.split()[3])
                var_list.append(line.split()[0])
    return [start_list, end_list, var_list]


def convert(txt, sps, filename):
    """
    csvに変換
    """
    start_list, end_list, var_list = getsps(sps)

    with open(filename + ".csv", "w", newline="") as csvfile:
        write = csv.writer(csvfile)
        write.writerow(var_list)
        num = 0
        num_lines = sum(1 for line in open(txt))
        print("[{}]を変換中・・・".format(txt))
        for line in open(txt):
            pisadata = []
            for (start, end) in zip(start_list, end_list):
                pisadata.append(line[int(start) - 1 : int(end)])
            write.writerow(pisadata)
            num += 1
            prog = num / num_lines * 100
            print("\r進捗: {:.0f}% ({}/{})".format(prog, num, num_lines), end="")


def convert_cnt(txt, sps, filename, cnts):
    """
    csvに変換（国別）
    """
    start_list, end_list, var_list = getsps(sps)

    for (num, cnt) in enumerate(cnts):
        with open(filename + "_" + cnt + ".csv", "w", newline="") as csvfile:
            write = csv.writer(csvfile)
            write.writerow(var_list)
            print("[{}]を変換中・・・[{}/{}]".format(cnt, num + 1, len(cnts)))
            for line in open(txt):
                if line.find(cnt) >= 0:
                    pisadata = []
                    for (start, end) in zip(start_list, end_list):
                        pisadata.append(line[int(start) - 1 : int(end)])
                    write.writerow(pisadata)


def select():
    """
    選択肢を表示
    """
    jsonfile = open("pisa.json", "r")
    pisadata = json.load(jsonfile)
    length = len(pisadata)
    print("必要なデータを選んでください。")
    print("['1'から'{}'の数値を入力]".format(length))
    for (i, key) in enumerate(pisadata):
        print(" ", i + 1, ": ", pisadata[key]["file"], sep="")
    while True:
        arg = input(">>> ")
        try:
            arg = int(arg)
            if not 0 < arg < length + 1:
                raise ValueError
        except ValueError:
            print("'1'から'{}'の数値を入力".format(length))
        else:
            break
    data_name = list(pisadata)[int(arg) - 1]
    data_dict = pisadata[data_name]
    return [data_name, data_dict]


def main():
    """
    main
    """
    data_name, data_dict = select()

    spsname = parse.urlparse(data_dict["sps url"])[2].split("/")[-1]
    cnt = data_dict["CNT"].split(",")

    # 保存用ディレクトリ生成
    if os.name == "posix":
        if os.path.exists("./" + data_name):
            os.chdir("./" + data_name)
        else:
            os.makedirs(data_name)
            os.chdir("./" + data_name)
    elif os.name == "nt":
        if os.path.exists(".\\" + data_name):
            os.chdir(".\\" + data_name)
        else:
            os.makedirs(data_name)
            os.chdir(".\\" + data_name)
    else:
        sys.exit("Windows・Linux以外では動作しません。")

    # ダウンロード
    download(data_dict["zip url"], data_dict["zip md5sum"])
    download(data_dict["sps url"], data_dict["sps md5sum"])

    # 変換
    print("変換オプション【1か2を押してください】")
    print(" 1: すべての国を1つにまとめたcsvファイルを生成します")
    print(" 2: 国ごとにcsvファイルを生成します")
    arg = input(">>> ")
    if arg == "1":
        convert(data_dict["txt name"], spsname, data_name)
        print("\ncsvファイルの生成が終了しました。")
    elif arg == "2":
        convert_cnt(data_dict["txt name"], spsname, data_name, cnt)
        print("csvファイルの生成が終了しました。")
    else:
        sys.exit("1か2以外が選択されました（終了します）")


if __name__ == "__main__":
    main()
