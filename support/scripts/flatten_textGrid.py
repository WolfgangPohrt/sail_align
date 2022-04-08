import sys
import subprocess
import os
import tgt
from tgt.core import Interval, IntervalTier, TextGrid
import pathlib
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
        t.append(Interval(x_min, x_max, word))

        x_min = x_max
        x_max = float(x_min) + float(inter_length)
    return t

def post_process(input_path, wav_path, output_path):
    cwd = os.getcwd()
    b_name = os.path.basename(input_path)
    wav_name = b_name[:-8]+'wav'
    wav_duration = get_duration(wav_path)


    grid = tgt.io.read_textgrid(input_path)
    intervals = grid.tiers[0].annotations

    # for kalid long alignment unaligned words #
    # for i, inter in enumerate(intervals):
    #     unali_words = []
    #     unali_regions = []
    #     unali_fl = False
    #     if inter.start_time == -1:
    #         start_time = intervals[i-1].end_time
    #         unali_fl = True
    #     if unali_fl == True:
    #         unali_words.append(inter.text)
    #     if unali_fl == True and inter.start_time != -1:
    #         end_time = inter.end_time
    #         unali_fl = False
    #         unali_words = []
    #         unali_regions.append(Interval(start_time, end_time, ' '.join(unali_words)))
    # grid.tiers[0].delete_annotation_by_start_time(-1)
    # for region in unali_regions:
    #     grid.tiers[0].add_annotation(region)

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



    # sannity check #
    tiers = grid_sil.tiers[0].annotations
    for i in range(len(tiers) - 1):
        assert tiers[i].end_time <= tiers[i+1].start_time, f'Interval {i} end_time overlaps intervals {i+1} start_time'


    # write textGrid #
    tgt.io.write_to_file(grid_sil, output_path, format='long')


if __name__ == '__main__':
    input = sys.argv[1]
    wav = sys.argv[2]
    output = sys.argv[3]
    post_process(input, wav, output)
