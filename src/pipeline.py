import argparse
from . import ingest,transform,warehouse,train,advanced_analytics
def main():
    p=argparse.ArgumentParser(); p.add_argument("--all",action="store_true"); a=p.parse_args()
    if a.all:
        ingest.run(); transform.run(); warehouse.run(); train.run(); advanced_analytics.run()
    else: p.print_help()
if __name__=="__main__": main()
