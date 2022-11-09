import sys
import os
import tgt
from tgt.core import Interval, IntervalTier, TextGrid
import wave
import contextlib


"""
Script to assign an interval in 
unaligned words so that the manual correction on
praat is easier. Also adds 'SIL' intervals
in the start and end if needed.

Input: (1) input_path: Path to input textGrid
       (2) data_dir: Path to directory tha contains 
           the audio file that correspond to the
           input textGrid.
       (3) output_dir: Path to directory to save the
        the new textGrid.
"""

def get_duration(fname):
    with contextlib.closing(wave.open(fname,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
    return duration

def flatten_text(inter):
    t = []
    words = inter.text.split(' ')
    num_words = len(words)
    x_min = inter.start_time
    # inter_length = round((float(inter.end_time) - float(inter.start_time)) / num_words, 4)
    inter_length = (float(inter.end_time) - float(inter.start_time)) / num_words

    x_max = float(x_min) + float(inter_length)
    for word in words:
        # t.append(Interval(round(x_min,4), round(x_max,4), word))
        t.append(Interval(round(x_min,4), round(x_max,4), word))

        x_min = x_max
        x_max = float(x_min) + float(inter_length)
    return t

def post_process(input_path, wav_path, output_path):
    cwd = os.getcwd()
    b_name = os.path.basename(input_path)
    wav_duration = get_duration(wav_path)


    grid = tgt.io.read_textgrid(input_path)
    intervals = grid.tiers[0].annotations



    # assign an interval to unaligned word #
    for i, inter in enumerate(intervals):
        if len(inter.text.split(' ')) > 1:
            str_time = inter.start_time
            flatt_inter = flatten_text(inter)
            grid.tiers[0].delete_annotation_by_start_time(str_time)
            grid.tiers[0].add_annotations(flatt_inter)

    # tier start_time == 0 and end_time == wav duration #
    grid.tiers[0].start_time = 0.0
    grid.tiers[0].end_time = wav_duration

    # chech if first word begins at 0.0 and if so ad 0.001 interval #
    if grid.tiers[0].annotations[0].start_time == 0:
        grid.tiers[0].annotations[0].start_time = 0.001
        grid.tiers[0].add_annotation(Interval(0.0, 0.001, ""))

    # add silence intervals #
    grid_sil = tgt.io.correct_start_end_times_and_fill_gaps(grid)

    new_tier = []
    tier = grid_sil.tiers[0]
    for i, inter in enumerate(tier[:-1]):
        if inter.start_time == inter.end_time: 
            continue
        if inter.text != "" and tier[i+1].text:
            new_tier.append(Interval(inter.start_time, inter.end_time - 0.001, inter.text))
            new_tier.append(Interval(inter.end_time - 0.001, tier[i+1].start_time, ""))
        elif inter.text == "" or tier[i+1].text == "":
            new_tier.append(inter)
    new_tier.append(tier[-1])
    grid_sil.tiers[0].objects = new_tier
    # sannity check #
    tiers = grid_sil.tiers[0].annotations
    new_grid = tgt.core.TextGrid(output_path)
    str_time = grid_sil.start_time
    end_time = grid_sil.end_time
    name = grid_sil.tiers[0].name
    interval_tier = tgt.core.IntervalTier(str_time, end_time, name, new_tier)
    new_grid.add_tier(interval_tier)

    for i in range(len(tiers) - 1):
        assert tiers[i].end_time <= tiers[i+1].start_time, f'Interval {i} end_time overlaps intervals {i+1} start_time'

    tgt.io.write_to_file(new_grid, output_path, format='long')


if __name__ == '__main__':
    input = sys.argv[1]
    wav = sys.argv[2]
    output = sys.argv[3]
    post_process(input, wav, output)
