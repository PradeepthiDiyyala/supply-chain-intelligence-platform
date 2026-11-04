import pandas as pd
def test_geolocation_aggregation_reduces_duplicate_zip_rows():
    d=pd.DataFrame({"zip":["01234","01234","05678"],"lat":[-23.,-23.2,-22.]})
    g=d.groupby("zip",as_index=False).agg(lat=("lat","mean"))
    assert len(g)==2 and round(g.loc[g.zip=="01234","lat"].iloc[0],1)==-23.1
def test_late_target():
    actual=pd.to_datetime(["2020-01-03","2020-01-01",None],utc=True)
    estimate=pd.to_datetime(["2020-01-02"]*3,utc=True)
    assert ((actual.notna())&(actual>estimate)).astype(int).tolist()==[1,0,0]
