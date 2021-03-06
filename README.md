# A simple example for training machine learning model

This example demonstrates the processes of collecting data and train a image classification machine learning model.

We are going to train a Hiragana (ひらがな) classifier (single character only).

Dataset will be generated from some fonts.

## Install dependencies

This project requires Python 3.6+ because I use f-string feature.

```bash
pip install -r requirements.txt
```

## What do we want to classify?

We need to specify a limited output characters that we want to classify. I put a list of basic Hiragana (without variants) in [`hiragana.txt`](./hiragana.txt). You may put more characters in there. Remember to encode them in UTF-8 encoding.

Because this is a classification problem, we need to define the output format. Specifically, we want to pin down which character will take which index position in the output. If we don't have this output order consistently, we might interpret the model output wrongly. We will generate a JSON file for specifying the output format. It will be a array of characters in which the character order has been defined. This is useful when we export the model to TensorFlow Lite or TensorFlow.js where the model doesn't contain any information about what the output is represented.

[notebook](./1-create-label.ipynb)

This notebook will guide you to generate the `labels.json` file. The order of characters are just the order which they appear in the [`hiragana.txt`](./hiragana.txt) file. There are more suitable ways to order these characters but for the sake of simplicity, this ordering method will get the job done.

## Where do we get the dataset?

When I got into machine learning, all the tutorials have nice and clean dataset ready for us to press a button and done. In this sample, we will have to create/find and clean the dataset ourselves. Well, I did clean the dataset to make this sample work. But I hope this example can help beginners who haven't able to do anything new beyond running through the tutorials.

We will have to collect Hiragana-compatible fonts to generate the character images and put them in the [`fonts`](./fonts) directory.

## Create the dataset

```sh
python3 create-dataset.py
```

By default, this script will take `labels.json` as input. Add `-h` for usage information.

## Inspect the dataset

```sh
python3 inspection-server.py
```

This will start a local webserver for inspecting and validating the dataset in browser at `http://localhost:3000/index.html`.

![Example inspection interface](https://i.imgur.com/1EeUpJE.png)

You can click on the label to show records or mark that label as done (all the records for that label have been reviewed). You can click on the image to mark the record as `invalid` or mark all the record with the same `font` as `invalid`. This process cannot be and should not be automated.

# Note

- I do apply `typing` for Python so most of the time you or me from the future can know where something comes from.
- I do have type hinting for JavaScript with `jshint`. I didn't choose TypeScript because I wanted to reduce dependencies.

# References

- `argparser` - [Python Documentation](https://docs.python.org/3/library/argparse.html)
- `decorator` - [Corey Schafer's video](https://www.youtube.com/watch?v=FsAPt_9Bf3U)
- `classmethod` - [Pythoc Documenation](https://docs.python.org/3/library/functions.html#classmethod)
