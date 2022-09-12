
import sys
import codecs
"""
This script converts an alignment from lab
format to textGrid format.

Input: lab_file: Path to lab file
Output: Outputs textGrid file to stfout.
"""


def lab2textgrid(lab_file, textGrid_file):

    with codecs.open(lab_file, 'r', 'utf-8') as f:
            lines = f.readlines()

    with codecs.open(textGrid_file, 'w', 'utf-8') as f:
        f.write("File type = \"ooTextFile\"\n")
        f.write("Object class = \"TextGrid\"\n")

        start_times = []
        end_times = []
        labels = []
        for ln in lines:
            ln = ln.rstrip('\r\n')
            ln_info = ln.split()
            if len(ln_info) > 0:
                start_times.append(ln_info.pop(0))
                end_times.append(ln_info.pop(0))
                labels.append(" ".join(ln_info))

        n_segments = len(start_times)
        f.write("xmin = {}\n".format(start_times[0]))
        f.write("xmax = {}\n".format(end_times[-1]))
        f.write("tiers? <exists>\n")
        f.write("size = 1\n")
        f.write("item []:\n")
        f.write("item [1]:\n")
        f.write("class = \"IntervalTier\"\n")
        f.write("name = \"phono\"\n")
        f.write("xmin = {}\n".format(start_times[0]))
        f.write("xmax = {}\n".format(end_times[-1]))
        f.write("intervals: size = {}\n".format(str(n_segments)))

        for count in range(n_segments):
            f.write("intervals [{}]\n".format(str(count+1)))
            f.write("xmin = {}\n".format(start_times[count]))
            f.write("xmax = {}\n".format(end_times[count]))
            f.write("text = \"{}\"\n".format(labels[count]))





if __name__=="__main__":
    lab_file = sys.argv[1]
    textGrid_file = sys.argv[2]
    lab2textgrid(lab_file, textGrid_file)
