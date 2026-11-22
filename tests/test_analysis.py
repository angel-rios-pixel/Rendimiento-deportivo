from core.analysis import regression,percent_change
from core.importer import extract
from pathlib import Path

def test_regression():
    r=regression([20,30,40,50],[1.0,.9,.8,.7]);assert abs(r['r2']-1)<1e-9

def test_change():assert percent_change(33,30)==10

def test_insufficient():assert regression([20,30],[1,.8]) is None
