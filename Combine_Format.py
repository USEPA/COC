import os
import csv

from tkinter import Tk
from tkinter.filedialog import askopenfilename

result_path = ""
output_path = ""
source_path = "C:/Users/jdeagan/OneDrive - Environmental Protection Agency (EPA)/Profile/Desktop/Projects/OTECRA/"
background = "OTECRA_R0_Samples_0.csv"
round_one = "OTECRA_R1_Samples_0.csv"
round_two = "OTECRA_R2_Samples_0.csv"
media_blank = "Media_Blanks_Base_0.csv"
assurance_1 = "Assurance Samples_0.csv"
assurance_2 = "Assurance Samples_1.csv"
waste_sample = "Waste_Samples_0.csv"
formated = "OTECRA Final_112922_"
data_collected = False
source_samples = []
header = []


class CombineFormat:

    def __init__(self):
        global source_path, source_samples, formated, header
        for count in range(1, 7):
            file = "%s%s_reformat.csv" % (formated, count)
            temp_source = source_path + file
            with open(temp_source, "r", encoding='utf-8-sig') as source_csv:
                reader = csv.reader(source_csv)
                temp = list(reader)
                header = temp[0]
                header[0] = "Sample Bag ID"
                for sample in temp[1:]:
                    source_samples.append(sample)
        self.join()

    def join(self):
        global data_collected, header, background, round_one, round_two, assurance_1, assurance_2, \
            waste_sample, media_blank, output_path, source_samples
        collected = [background, round_one, round_two, assurance_1, assurance_2, waste_sample, media_blank]
        for file in collected:
            temp_source = "%sArcGIS files/%s" % (source_path, file)
            path, form = temp_source.split('.')
            output_path = "%s_joined.csv" % path
            temp_header = header[:]
            result_samples = []
            with open(temp_source, "r", encoding='utf-8-sig') as source_csv:
                reader = csv.reader(source_csv)
                temp = list(reader)
                base_head = temp[0][:]
                base_head.remove("Sample Bag ID")
                base_head.remove("Combined ID")
                temp_header.insert(0, base_head[0])
                temp_header = temp_header + base_head[1:]
                result_samples = [temp_header]
                base_head = temp[0][:]
                # print(base_head)
                index = base_head.index("Sample Bag ID")
                index_2 = base_head.index("Combined ID")
                for sample in temp[1:]:
                    bag_id = sample[index]
                    samp_part = []
                    for alternate in source_samples:
                        if alternate[0] == bag_id:
                            samp_part = alternate[:]
                            break
                    if samp_part:
                        pass
                    else:
                        samp_part = [bag_id,'','','','','','','','']
                    samp_part.insert(0, sample[0])
                    samp_part[2] = sample.pop(index_2)
                    sample.remove(bag_id)
                    samp_part = samp_part + sample[1:]
                    result_samples.append(samp_part)
                with open(output_path, 'w', newline='') as output_file:
                    writer = csv.writer(output_file)

                    for row in result_samples:
                        writer.writerow(row)

        # print(new_results)  do something with resulting list


if __name__ == "__main__":
    CombineFormat()
