import pandas as pd
from src.features import FEATURES,single_frame
def test_prediction_schema():
    x=single_frame({k:1 for k in FEATURES})
    assert list(x.columns)==FEATURES and len(x)==1
