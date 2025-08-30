import pandas as pd

def load_training_data(path: str):
    return pd.read_csv(path)
