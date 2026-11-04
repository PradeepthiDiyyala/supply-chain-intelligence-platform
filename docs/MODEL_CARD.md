# Model card: late-delivery risk

**Target:** 1 when actual customer delivery is later than estimated delivery; 0 for delivered on/before estimate. Undelivered orders are excluded.

**Inputs:** purchase hour/day/month, estimated delivery horizon, item count, GMV/freight, seller/product counts, payment installments/type count and customer state.

**Leakage controls:** actual delivery date/duration, review score/text and other post-delivery fields are not predictors.

**Evaluation:** chronological 80/20 split; metrics include accuracy, precision, recall, F1, ROC-AUC, average precision and confusion matrix. Results are saved to `artifacts/metrics.json`.

**Limitations:** historical 2016–2018 data; labels only for delivered orders; single holdout; probabilities are not calibrated; no live carrier events. Validate across time/regions, calibrate and monitor before operational use.
