import json, joblib, duckdb, pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,roc_auc_score,average_precision_score,confusion_matrix
from .common import setup,logger,path
from .features import FEATURES,NUMERIC,CATEGORICAL,build_training_frame

def run():
    setup(); log=logger("train"); db=path("warehouse")
    if not db.exists(): raise FileNotFoundError("Run python -m src.warehouse first")
    con=duckdb.connect(str(db),read_only=True)
    try: df=con.execute("SELECT * FROM fact_orders").df()
    finally: con.close()
    df["order_purchase_timestamp"]=pd.to_datetime(df.order_purchase_timestamp,utc=True)
    frame=build_training_frame(df).sort_values("order_purchase_timestamp")
    if len(frame)<100: raise ValueError("Insufficient labelled delivered orders")
    cut=int(.8*len(frame)); tr,te=frame.iloc[:cut],frame.iloc[cut:]
    prep=ColumnTransformer([("num",Pipeline([("impute",SimpleImputer(strategy="median")),("scale",StandardScaler())]),NUMERIC),
      ("cat",Pipeline([("impute",SimpleImputer(strategy="most_frequent")),("ohe",OneHotEncoder(handle_unknown="ignore"))]),CATEGORICAL)])
    model=Pipeline([("prep",prep),("rf",RandomForestClassifier(n_estimators=350,max_depth=14,min_samples_leaf=4,
      class_weight="balanced_subsample",random_state=42,n_jobs=-1))])
    model.fit(tr[FEATURES],tr.target); prob=model.predict_proba(te[FEATURES])[:,1]; pred=(prob>=.5).astype(int)
    metrics={"target":"late_delivery","train_rows":len(tr),"test_rows":len(te),
      "test_start":str(te.order_purchase_timestamp.min()),"test_end":str(te.order_purchase_timestamp.max()),
      "threshold":.5,"accuracy":float(accuracy_score(te.target,pred)),
      "precision":float(precision_score(te.target,pred,zero_division=0)),
      "recall":float(recall_score(te.target,pred,zero_division=0)),
      "f1":float(f1_score(te.target,pred,zero_division=0)),
      "roc_auc":float(roc_auc_score(te.target,prob)) if te.target.nunique()>1 else None,
      "average_precision":float(average_precision_score(te.target,prob)),
      "confusion_matrix":confusion_matrix(te.target,pred).tolist(),
      "features":FEATURES,"evaluation":"chronological 80/20 holdout; historical data"}
    joblib.dump(model,path("artifacts")/"delivery_risk_model.joblib")
    (path("artifacts")/"metrics.json").write_text(json.dumps(metrics,indent=2))
    log.info("Model trained; F1=%.3f ROC-AUC=%s",metrics["f1"],metrics["roc_auc"])
    return metrics
if __name__=="__main__": print(json.dumps(run(),indent=2))
