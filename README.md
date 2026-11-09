# Video to GIF

Turns videos (or parts of them) into GIFs. Put your videos in the `input` folder, run the script, and get the GIFs in
the `output` folder.

It uses a 256-color palette made for each clip, so the GIFs have much better colors than a basic conversion.

## Folder layout

```
video_to_gif/
├── make_gifs.py       the script
├── requirements.txt   Python packages to install
├── README.md          this file
├── input/             put your videos here
└── output/            GIFs appear here, with the same names
```

## Setup (one time)

1. Install **Python 3.9 or newer** from https://www.python.org/downloads/
   (on Windows, tick "Add Python to PATH" during install).
2. Open a terminal in the `video_to_gif` folder and run:

   ```
   pip install -r requirements.txt
   ```

   This installs a copy of **ffmpeg**, the program that makes the GIFs. If ffmpeg is already installed on your
   computer, the script uses that one instead, and this step is optional.

## How to use

1. Copy the videos into the `input` folder.
2. Open a terminal in the `video_to_gif` folder and run:

   ```
   python make_gifs.py
   ```

3. It asks three questions. Press Enter to accept the default for any of them:
   - **Start at**: where the GIF starts, like `5` (5 seconds) or `1:30` (1 minute 30). Default: the beginning.
   - **How many seconds long**: default is until the end of the video.
   - **Width in pixels**: default 480. The height follows automatically.
4. The GIFs are saved in `output`. For example, `input/funny.mp4` becomes `output/funny.gif`.

The same settings are used for every video in `input`, so when you want a different part of each video, put one
video in at a time.

You can also give the settings straight away so it doesn't ask:

| Command | What it does |
|---|---|
| `python make_gifs.py` | Asks where to start, how long, and how wide |
| `python make_gifs.py -s 0:05 -d 3` | 3 seconds, starting at 0:05 |
| `python make_gifs.py -s 1:10 -e 1:14` | From 1:10 to 1:14 |
| `python make_gifs.py -d 4 -w 320` | First 4 seconds, 320 pixels wide |
| `python make_gifs.py -d 4 --fps 20` | Smoother (bigger file) |
| `python make_gifs.py -d 4 --max-mb 8` | At most 8 MB |
| `python make_gifs.py -d 4 --no-loop` | Plays once instead of looping |
| `python make_gifs.py --help` | Shows all options |

## Options

| Option | Default | Meaning |
|---|---|---|
| `-s`, `--start` | beginning | Where to start: seconds (`5`, `12.5`) or minutes:seconds (`1:30`) or hours:minutes:seconds (`1:02:03`) |
| `-d`, `--duration` | until the end | How many seconds long |
| `-e`, `--end` | | Where to stop, instead of `-d` |
| `-w`, `--width` | `480` | Width in pixels. Videos narrower than this keep their size |
| `--fps` | `12` | Frames per second. `10`-`15` looks fine for most GIFs. Higher is smoother but bigger |
| `--max-mb` | none | Keep each GIF at most this many MB. It makes the GIF narrower, then choppier, until it fits |
| `--no-loop` | off | Play once instead of looping forever |
| `-i`, `--input` | `input` folder | Folder to read videos from |
| `-o`, `--output` | `output` folder | Folder to save GIFs to |

**Videos it accepts:** `.mp4 .mkv .mov .webm .avi .m4v .wmv .flv .mpg .mpeg .3gp .ts .mts`, and `.gif` (to cut or
shrink an existing GIF). Other files are listed as "ignored" and left alone.

## Keeping GIFs small

GIFs are an old format and get big fast. A few seconds of video can easily be 5-10 MB. In order of how much they help:

1. **Shorter**: use `-d` to keep it to a few seconds.
2. **Narrower**: `-w 320` makes a file about half the size of `-w 480`.
3. **Fewer frames**: `--fps 10` instead of 12-15.
4. **Calm footage**: shaky or busy videos make bigger GIFs than still shots.

Or use `--max-mb` and let the script do it. Common limits: Discord 10 MB (free accounts), Slack and many forums 5-10 MB.

## Good to know

- **Original videos are never changed or deleted.** The script only reads from `input`.
- **GIFs have no sound.**
- **If you don't set a length, the whole video is used**, and the script warns you when that's over 30 seconds
  because the GIF will be huge.
- **Running it again overwrites earlier GIFs** with the same name in `output`.
- **Videos with the same name but different extensions**, like `clip.mp4` and `clip.mov`, keep their old extension in
  the new name so neither overwrites the other: `clip_mp4.gif` and `clip_mov.gif`.
- **Subfolders inside `input` are not scanned.** Put the videos directly in `input`.

## Troubleshooting

**`Error: ffmpeg was not found`**

Run `pip install -r requirements.txt` from inside the `video_to_gif` folder.

**`it's only 0:10 long, so it ends before ...`**

The start time is past the end of that video. Use an earlier `-s`.

**`couldn't get ... under ... MB`**

Even the smallest, choppiest version is too big. Make the clip shorter with `-d`.

**The colors look grainy**

That's the dithering a GIF needs to fake more than 256 colors. It's less noticeable at bigger widths.

**`'python' is not recognized`**

Python isn't on your PATH. On Windows, try `py make_gifs.py` instead, or reinstall Python with "Add Python to PATH" ticked.
