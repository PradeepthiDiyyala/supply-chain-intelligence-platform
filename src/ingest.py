import json
from datetime import datetime, timezone
import pandas as pd
from .common import setup, logger, path, raw_files

def run():
    setup(); log=logger("ingest"); stamp=datetime.now(timezone.utc).isoformat(); manifest={}
    for name, file in raw_files().items():
        df=pd.read_csv(file, low_memory=False)
        df["__source_file"]=file.name; df["__ingested_at_utc"]=stamp
        df.to_parquet(path("bronze")/f"{name}.parquet", index=False)
        manifest[name]={"rows":len(df),"columns":list(df.columns)}
        log.info("Bronze %s: %d rows",name,len(df))
    (path("bronze")/"manifest.json").write_text(json.dumps({"ingested_at_utc":stamp,"tables":manifest},indent=2))
    return manifest
if __name__=="__main__": run()
