# `score_log_CL_iid_*`
The files ending in `_cvX.csv`, where `X` is 1–5, are cross-validation
folds/runs with errors and accuracies.

## The exception
The files starting with `score_log_CL_iid_run2MAX_` only contain one
row of values each.
This is because the original run used in the paper was lost, except for
the maximum accuracy of each file.
Each file, therefore, only contains an arbitrary error value of 0.0 and
a its maximum accuracy.
The accuracy values are used for the Bayesian comparisons.
