# Common ability execution audit

Original run 45779571455 reached real 2019 calibration after passing source and synthetic graph gates, but failed on a pandas name collision (`t.first` resolves a method). No empirical result was returned or inspected. Replace all affected accesses with bracket column indexing, add calibration/evaluation regression with first-meeting and disconnected pair masks. Frozen data, weights, penalties, calibration grid, endpoints, split and support rules are unchanged. This is a software repair, not a new empirical model.
