# Spec: Generalize Demo Montage

Make a new branch for this code called generalize\_demo\_montage. Use the Microsoft Docs MCP server whenever you need to look up documentation for a function.

demo\_montage.py takes in a single MP4 video, and then uses Azure AI Video Translation

Modify demo\_montage.py in the following manner:

*   On the command line, it should take 3 parameters
    *   input: the input filename in MP4 format
    *   output: the output filename in MP4 format
    *   timestamps
        *   The filename of a JSON file that contains the timestamps where the translations should begin and end. The format should look like this:

```
[
  {
    "start": "00:00",
    "translate": "no"
  },
  {
    "start": "00:08",
    "language": "Danish",
    "translate": "yes"
  },
  {
    "start": "00:20",
    "language": "Spanish",
    "translate": "yes"
  },
  {
    "start": "00:31",
    "language": "Chinese",
    "translate": "yes"
  },
  {
    "start": "00:44",
    "language": "Japanese",
    "translate": "yes"
  },
  {
    "start": "00:53",
    "language": "French",
    "translate": "yes"
  },
  {
    "start": "01:02",
    "language": "German",
    "translate": "yes"
  },
  {
    "start": "01:09",
    "language": "Dutch",
    "translate": "yes"
  },
  {
    "start": "01:18",
    "translate": "no"
  }
]
```

Also add a sample\_timestamps.json file with the above example.

From this point forward, the app should work very similarly to how it did before.

*   It should first chop the videos up into subvideos, from each start time to the next entry's start time - 0.001s.
    *   In the example above, there should be a subvideo from 00:00 to 00:07:999 that is not translated, and then a video from 00:08.000 to 00.19.999 that is translated to Danish, and so on.
*   It should then translate each video segment into the language specified (except those marked as translate:no)
*   It should finally stitch the video segments back together and save it to the file specified as the output file.