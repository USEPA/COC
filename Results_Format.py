import os
import csv

from tkinter import Tk
from tkinter.filedialog import askopenfilename

result_path = ""
output_path = ""
source_path = "C:/Users/jdeagan/OneDrive - Environmental Protection Agency (EPA)/Profile/Desktop/Projects/OTECRA/ArcGIS files/"
background = "OTECRA_R0_Samples_0.csv"
round_one = "OTECRA_R1_Samples_0.csv"
round_two = "OTECRA_R2_Samples_0.csv"
media_blank = "Media_Blanks_Base_0.csv"
assurance_1 = "Assurance Samples_0.csv"
assurance_2 = "Assurance Samples_1.csv"
waste_sample = "Waste_Samples_0.csv"
data_collected = False
source_samples = []
result_samples = []
header = []


def store():
    global result_path, data_collected, result_samples, output_path, header

    root = Tk()
    root.title('Select Result CSV')
    root.withdraw()
    result_path = askopenfilename()
    if os.path.exists(result_path):  # if they chose one
        if result_path[-4:] == '.csv':
            result_file = result_path[:-4]
            output_path = "%s_reformat.csv" % result_file
            with open(result_path, "r", encoding='utf-8-sig') as result_csv:
                reader = csv.reader(result_csv)
                temp = list(reader)
                header = temp[0]
                result_samples = temp[1:]
            data_collected = True
        else:
            print("File not a csv")
            data_collected = False
    else:
        print("File not chosen")
        data_collected = False


class ResultFormat:

    def __init__(self):
        global source_path, background, round_one, round_two, assurance_1, assurance_2, waste_sample, media_blank, source_samples
        collected = [background, round_one, round_two, assurance_1, assurance_2, waste_sample, media_blank]
        for file in collected:
            temp_source = source_path + file
            with open(temp_source, "r", encoding='utf-8-sig') as source_csv:
                reader = csv.reader(source_csv)
                temp = list(reader)
                sample_item = [temp[0].index("Sample Bag ID"), temp[0].index("Combined ID")]
                for sample in temp[1:]:
                    source_samples.append([sample[sample_item[0]], sample[sample_item[1]]])
        self.split()

    def split(self):
        global data_collected, header, result_samples, output_path, source_samples
        while not data_collected:
            store()
        temp_header = [header[0], "Combined ID"]
        header = temp_header + header[1:]
        new_results = [header]
        for sample in result_samples:
            # print(sample[0])
            sample_bag, location = sample[0].split('(')
            sample_bag = sample_bag.strip()
            for part in source_samples:
                if part[0] == sample_bag:
                    original = part
                    break
            if ')' in location:
                location = location.replace(')', '')
            else:
                location = original[1]
            # print(sample_bag + ", " + location)
            new_list = [sample_bag, location] + sample[1:]
            new_results.append(new_list)
        with open(output_path, 'w', newline='') as output_file:
            writer = csv.writer(output_file)

            for row in new_results:
                writer.writerow(row)
        # print(new_results)  do something with resulting list


if __name__ == "__main__":
    ResultFormat()
