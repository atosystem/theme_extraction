# Theme Extraction
A tool for extraction musical theme
## Preparation
```
pip install -r requirements.txt
```

## Usage
```
usage: main.py [-h] [--theme THEME] [--comp COMP] [--result RESULT]
               [--midi MIDI] [-v]

Theme Extraction This program extract polymophic themes from polymophic full
compositions via altered LCS algorithm. The extraction result is saved in pkl
file and can also output to midi file for visulization.

optional arguments:
  -h, --help       show this help message and exit
  --theme THEME    theme midi file path
  --comp COMP      full composition midi file path
  --result RESULT  theme extraction result file path (.pkl)
  --midi MIDI      theme extraction result midi file path
  -v, --verbose    set verbose
```

## Files
```
.
├── LCS.py
├── main.py
├── motif_labeling.py
├── README.md
├── requirements.txt
└── sample_data
    ├── full_composition
    │   └── Beethoven_Op007-01.mid
    └── theme
        └── MTD0827_Beethoven_Op007-01.mid
```
