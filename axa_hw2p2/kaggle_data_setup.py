# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/kaggle_data_import.ipynb (unless otherwise specified).

__all__ = []

# Cell
# !pip install Kaggle
# %cd ../.kaggle/
# !pwd

# Cell
# Credentials

# import json
# token = {"username":"alejandroxag","key":"c36bca85da2adb89b094f2f02902a5db"}
# print(token)
# with open('kaggle.json', 'w') as file:
#     json.dump(token, file)

# Cell
# %cd ..

# Cell
# Connection setup

# !chmod 600 .kaggle/kaggle.json
# !cp .kaggle/kaggle.json /home/alejandroxag/.kaggle/
# !kaggle config set -n path -v nbs/data

# Cell
# !kaggle competitions download -c 11785-spring2021-hw2p2s1-face-classification

# Cell
# !kaggle competitions download -c 11785-spring2021-hw2p2s2-face-verification

# Cell
# Data unziping

from zipfile import ZipFile

# with ZipFile('nbs/data/competitions/11785-spring2021-hw2p2s1-face-classification/11785-spring2021-hw2p2s1-face-classification.zip', ) as zf: zf.extractall(path='nbs/data/s1')

# with ZipFile('nbs/data/competitions/11785-spring2021-hw2p2s2-face-verification/11785-spring2021-hw2p2s2-face-verification.zip', ) as zf: zf.extractall(path='nbs/data/s2')
