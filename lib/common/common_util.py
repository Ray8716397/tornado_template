import os


def logging(msg, fp):
    mkdir(os.path.dirname(fp))

    with open(fp, 'a') as f:
        f.write(msg + "\n")


def mkdir(fp):
    if not os.path.exists(fp):
        os.makedirs(fp)
