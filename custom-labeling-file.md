This document explains the format of the [`japanese-characters.txt`][./japanese-characters.txt] file. That file is used for labeling the output of the ML model.

The labels were first sorted by Unicode codepoint. However, I recognized some characters have similar patterns. Because of that, I grouped them together to reduce the number of labels.

The order of the labels is sorted by my opinion by looking at their similarities.

## The label file format

Each lines is a output label for the ML model.

__Label line format__

Example:

```
つづ	っ
つづ[Tab]っ
```

In the above example, all of the three characters (つづっ) are grouped in a single label. `つ` and `づ` can be used for creating dataset (from computer fonts) for this group but `っ` is not.
