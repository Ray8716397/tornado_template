import os
import pandas as pd


def split_csv(csv_path, step, start_cut=0, end_cut=0):
    """
    分割csv文件
    :param csv_path: csv特征文件路径
    :param step: 按多少帧分割
    :param start_cut: 丢弃前多少帧
    :param end_cut: 丢弃后多少帧
    :return:
    """
    # init
    output_dirpath = csv_path.split(".csv")[0]
    target_name = os.path.basename(output_dirpath)

    # read
    df = pd.read_csv(csv_path)

    if df.shape[0] == step:
        return
    # preprocess
    # 不满step(1800帧)则填满
    elif df.shape[0] < step:
        empty_row = [0 for i in range(df.shape[1])]

        fixed_num = step - df.shape[0]
        for i in range(0, fixed_num):
            # df = df.append(df.iloc[-1])
            df.loc[df.shape[0]] = empty_row

    # 去除多余帧数据
    else:
        duplicate = df.shape[0]-step
        if duplicate % 2 == 0:
            start_cut = int(duplicate / 2)
            end_cut = start_cut
        else:
            start_cut = int(duplicate/2)
            end_cut = start_cut + 1

        if start_cut > 0 and df.shape[0] > start_cut:
            df = df.iloc[start_cut:]
        if end_cut > 0 and df.shape[0] > start_cut:
            df = df.iloc[:df.shape[0]-end_cut]

    df.to_csv(csv_path, index=False)


if __name__ == '__main__':
    split_csv('/home/ray/Workspace/project/Emotiw2021-Engagement-Prediction-KDDI/test.csv', 1800, start_cut=0, end_cut=0)