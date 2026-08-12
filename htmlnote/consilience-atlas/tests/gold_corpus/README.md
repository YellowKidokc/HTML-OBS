# Gold Corpus (spec Y)

Drop frozen reference papers here as `<name>.txt` plus `<name>.gold.json`
containing expected atom boundaries / classifications / dependencies.

`test_gold.py` (Milestone 2) will compare a new engine/prompt version against
these and report: boundary agreement, classification agreement, dependency
agreement, missing atoms, extra atoms, confidence calibration.

Never judge model improvements by "this looks pretty good."
