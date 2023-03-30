"""
Name: CoC PDF Tool v1.1
Description: The CoC PDF Tool is used to turn the survey information collected in Field Maps and exported from ArcGIS
Online into a CoC Form
information
Author(s): Code development - Jordan Deagan deagan.jordan@epa.gov; Timothy Boe boe.timothy@epa.gov
    pyzbar - Lawrence Hudson quicklizard@googlemail.com;
    OpenCV code - Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/;
Contact: Timothy Boe boe.timothy@epa.gov
# Requirements: Python 3.7+, numpy, pyzbar, imutils, opencv-python, Pillow, Kivy, reportlab, tk
"""

import os
import os.path
import sys
import time
import pytz
from datetime import datetime
from tkinter import *
from tzlocal import get_localzone
import pickle

# Import csv packages
import cv2
import csv
import imutils
import numpy as np
from PIL import Image
from pyzbar import pyzbar
from arcgis.gis import GIS
from pyzbar.pyzbar import ZBarSymbol
from imutils.video import VideoStream

import threading
from functools import partial
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.dropdown import DropDown
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.stacklayout import StackLayout
from kivy.resources import resource_add_path

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import BaseDocTemplate, Table, TableStyle, Paragraph, Frame, PageTemplate, PageBreak
from tkinter import Tk  # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename

"""
To be worked on:
    Add direct access
        restructure code to use either csv or gis
            No CSV Selected when layer is selected  <-- Fix this
            add check for valid source layer
            restructure appending source
                redesign internal storage to only store the necessities
            rename confirmation text to reference which source was used
"""

data_collected = False  # add check for csv or gis
video_getter = None
curDir = os.getcwd()
drop_menu_1 = DropDown()
drop_menu_2 = DropDown()
lab_drop_btn = Button(text='Select Lab', size_hint_y=None, height=40)
method_drop_btn = Button(text='Select Collection Method', size_hint_y=None, height=40)
selector = BoxLayout(orientation='horizontal')
sys_id = os.environ["COMPUTERNAME"]
epa_url = 'https://epa.maps.arcgis.com/home/content.html'
oneepa_url = 'https://oneepa.maps.arcgis.com/home/content.html'
epa_client_id = 'vpeanPqMcHdq7G6z' # EPA
oneepa_client_id = 'tEHtLLr2xrIVpp3k' # OneEPA
gis_owner = "jdeagan_oneepa"  # clear this out
gis_title = "Background Survey Test"  # clear this out
accessed_server = -1
sample_id_col = -1
date_time_col = -1
location_col = -1
sample_type_col = -1
sample_method_col = -1
sample_id_head = 'sample bag id'
date_time_head = 'start time/date'
location_head = 'combined id'
sample_type_head = 'sample type'
sample_method_head = 'collection method'
sample_id_gis = "Sample_Bag_ID"
date_time_gis = "Start_Time_Date"
location_gis = "Combined_ID"
sample_type_gis = "Sample_Type"
sample_method_gis = "Collection_Method"
video_source = 'Integrated'
contact = "Anne Busher; 440-539-0787"
contact_name = "Anne Busher"
contact_num = "440-539-0787"
location = ""
curMemory = ""
csvTitle = ""

trouble_characters = ['\t', '\n', '\r']  # characters that cause issues
bad_file_name_list = ['*', ':', '"', '<', '>', ',', '/', '|', '?', '\t', '\r', '\n', '\\']
empty_dict = []
# can't be used in a filename
special_characters = ["à", "á", "â", "ã", "ä", "å", "æ", "ç", "è", "é", "ê", "ë", "ì", "í", "î", "ï", "ð", "ñ", "ò",
                      "ó", "ô", "õ", "ö", "ø", "ù", "ú", "û", "ü", "ý", "þ", "ÿ", "À", "Á", "Â", "Ã", "Ä", "Å", "Æ",
                      "Ç", "È", "É", "Ê", "Ë", "Ì", "Í", "Î", "Ï", "Ð", "Ñ", "Ò", "Ó", "Ô", "Õ", "Ö", "Ø", "Ù", "Ú",
                      "Û", "Ü", "Ý", "Þ", "ß"]
code_characters = ["!@!a1!", "!@!a2!", "!@!a3!", "!@!a4!", "!@!a5!", "!@!a6!", "!@!a7!", "!@!c1!", "!@!e1!", "!@!e2!",
                   "!@!e3!", "!@!e4!", "!@!i1!", "!@!i2!", "!@!i3!", "!@!i4!", "!@!o1!", "!@!n1!", "!@!o2!", "!@!o3!",
                   "!@!o4!", "!@!o5!", "!@!o6!", "!@!o7!", "!@!u1!", "!@!u2!", "!@!u3!", "!@!u4!", "!@!y1!", "!@!b1!",
                   "!@!y2!", "!@!A1!", "!@!A2!", "!@!A3!", "!@!A4!", "!@!A5!", "!@!A6!", "!@!A7!", "!@!C1!", "!@!E1!",
                   "!@!E2!", "!@!E3!", "!@!E4!", "!@!I1!", "!@!I2!", "!@!I3!", "!@!I4!", "!@!O1!", "!@!N1!", "!@!O2!",
                   "!@!O3!", "!@!O4!", "!@!O5!", "!@!O6!", "!@!O7!", "!@!U1!", "!@!U2!", "!@!U3!", "!@!U4!", "!@!Y1!",
                   "!@!B1!", "!@!Y2!"]
char_dict_special_to_code = {"à": "!@!a1!", "á": "!@!a2!", "â": "!@!a3!", "ã": "!@!a4!", "ä": "!@!a5!", "å": "!@!a6!",
                             "æ": "!@!a7!", "ç": "!@!c1!", "è": "!@!e1!", "é": "!@!e1!", "ê": "!@!e3!", "ë": "!@!e4!",
                             "ì": "!@!i1!", "í": "!@!i2!", "î": "!@!i3!", "ï": "!@!i4!", "ð": "!@!o1!", "ñ": "!@!n1!",
                             "ò": "!@!o2!", "ó": "!@!o3!", "ô": "!@!o4!", "õ": "!@!o5!", "ö": "!@!o6!", "ø": "!@!o7!",
                             "ù": "!@!u1!", "ú": "!@!u2!", "û": "!@!u3!", "ü": "!@!u4!", "ý": "!@!y1!", "þ": "!@!b1!",
                             "ÿ": "!@!y2!", "À": "!@!A1!", "Á": "!@!A2!", "Â": "!@!A3!", "Ã": "!@!A4!", "Ä": "!@!A5!",
                             "Å": "!@!A6!", "Æ": "!@!A7!", "Ç": "!@!C1!", "È": "!@!E1!", "É": "!@!E2!", "Ê": "!@!E3!",
                             "Ë": "!@!E4!", "Ì": "!@!I1!", "Í": "!@!I2!", "Î": "!@!I3!", "Ï": "!@!I4!", "Ð": "!@!O1!",
                             "Ñ": "!@!N1!", "Ò": "!@!O2!", "Ó": "!@!O3!", "Ô": "!@!O4!", "Õ": "!@!O5!", "Ö": "!@!O6!",
                             "Ø": "!@!O7!", "Ù": "!@!U1!", "Ú": "!@!U2!", "Û": "!@!U3!", "Ü": "!@!U4!", "Ý": "!@!Y1!",
                             "Þ": "!@!B1!", "ß": "!@!Y2!"}
char_dict_code_to_special = {"!@!a1!": "à", "!@!a2!": "á", "!@!a3!": "â", "!@!a4!": "ã", "!@!a5!": "ä", "!@!a6!": "å",
                             "!@!a7!": "æ", "!@!c1!": "ç", "!@!e1!": "è", "!@!e2!": "é", "!@!e3!": "ê", "!@!e4!": "ë",
                             "!@!i1!": "ì", "!@!i2!": "í", "!@!i3!": "î", "!@!i4!": "ï", "!@!o1!": "ð", "!@!n1!": "ñ",
                             "!@!o2!": "ò", "!@!o3!": "ó", "!@!o4!": "ô", "!@!o5!": "õ", "!@!o6!": "ö", "!@!o7!": "ø",
                             "!@!u1!": "ù", "!@!u2!": "ú", "!@!u3!": "û", "!@!u4!": "ü", "!@!y1!": "ý", "!@!b1!": "þ",
                             "!@!y2!": "ÿ", "!@!A1!": "À", "!@!A2!": "Á", "!@!A3!": "Â", "!@!A4!": "Ã", "!@!A5!": "Ä",
                             "!@!A6!": "Å", "!@!A7!": "Æ", "!@!C1!": "Ç", "!@!E1!": "È", "!@!E2!": "É", "!@!E3!": "Ê",
                             "!@!E4!": "Ë", "!@!I1!": "Ì", "!@!I2!": "Í", "!@!I3!": "Î", "!@!I4!": "Ï", "!@!O1!": "Ð",
                             "!@!N1!": "Ñ", "!@!O2!": "Ò", "!@!O3!": "Ó", "!@!O4!": "Ô", "!@!O5!": "Õ", "!@!O6!": "Ö",
                             "!@!O7!": "Ø", "!@!U1!": "Ù", "!@!U2!": "Ú", "!@!U3!": "Û", "!@!U4!": "Ü", "!@!Y1!": "Ý",
                             "!@!B1!": "Þ", "!@!Y2!": "ß"}

bio_edd_header = ["LRN Sample ID (if different)", "Sample Type Sponge, Vac, or extract", "EPA Sample ID",
                  "Date Received", "Date Processed", "Date Plated", "Total Sample Volume mL (final extract)",
                  "CFU per 100 µL Spread Plate 10^-1", "", "", "CFU per 100 µL Spread Plate 10^-2", "", "",
                  "CFU per 100 µL Spread Plate 10^-3", "", "", "CFU per 100 µL Spread Plate 10^-4", "", "",
                  "CFU per 1 mL Micro Funnel Filter Plate 10^0", "", "",
                  "CFU per 5 mL Micro Funnel Filter Plate 10^0        (Grab samples only)", "",
                  "CFU per 10 mL Micro Funnel Filter Plate 10^0        (Grab samples only)", "", "CFU/Sample", "NOTES"]
chem_edd_header = ["Samp_No", "Lab_Location_ID", "Matrix_ID", "Sample_Type_Code", "Lab_Coc_No", "Date_Collected",
                   "Date_Received", "Date_Extracted", "Date_Analyzed", "Lab_Name", "Lab_Samp_No", "Lab_Batch_No",
                   "Analysis", "Analytical_Method", "Extraction_Method", "Cas_no", "Analyte", "Detected", "Result",
                   "Result_Qualifier", "Lab_Result_Qualifier", "Result_Units", "MDL", "MDL_Units", "Quantitation_Limit",
                   "Quantitation_Limit_Units", "Reporting_Limit", "Reporting_Limit_Units", "Reportable_Result",
                   "Result_Type_Code", "QC_Type", "Percent_Solids", "Percent_Lipids", "Percent_Moisture",
                   "Total_or_Dissolved", "Test_Type", "Basis", "Dilution_Factor", "Percent_Recovery",
                   "SubSample_Amount", "SubSample_Amount_Unit", "Final_Volume", "Final_Volume_Unit", "Comments",
                   "QAFlag", "QA_Date", "QA_Comment", "QA_UserName"]
sample_types = ["Bio", "Chem"]

dataList = []
curData = []
usedData = []
labInfo = []
found = []
pdf_details = []
headers = []

lab_counts = {}
containers = {}
preservative = {}
pop_counts = {}
bag_counts = {}

styles = getSampleStyleSheet()
style = styles['Normal']
# create custom styles for the table to use for the Paragraphs
tableStyle = ParagraphStyle('Table Body',
                            fontName="Helvetica",
                            fontSize=8,
                            parent=styles['Normal'],
                            alignment=0,  # Left side
                            spaceAfter=10)
leftTable = ParagraphStyle('Left Table Body',
                           fontName="Helvetica",
                           fontSize=8,
                           parent=styles['Normal'],
                           alignment=2,  # Right
                           spaceAfter=10)


# start the document


class BaseColors:
    HEADER = ''
    OKBLUE = '[color=#009999]'
    OKGREEN = '[color=#66cc00]'
    WARNING = '[color=#e3e129]'
    FAIL = '[color=#a72618]'
    ENDC = '[/color]'
    BOLD = ''
    UNDERLINE = ''


def build_pdf(lab_name, num, data, samp_type):
    global pdf_details, curDir, containers, preservative, bio_edd_header, chem_edd_header, sample_types, \
        bad_file_name_list, empty_dict
    # start the document
    name = lab_name + " " + num
    new_name = convert(name, bad_file_name_list, empty_dict, True)
    doc = BaseDocTemplate("%s/Generated Forms/%s_CoC.pdf" % (curDir, new_name),
                          pagesize=(11 * inch, 8.5 * inch),
                          rightMargin=50,
                          leftMargin=50,
                          topMargin=10,
                          bottomMargin=63)

    y = doc.bottomMargin + (doc.height / 4) + 65

    frame3 = Frame(doc.leftMargin,
                   y,
                   doc.width,
                   (doc.height / 2) - 35,
                   leftPadding=0,
                   bottomPadding=0,
                   rightPadding=0,
                   topPadding=0,
                   id='top')

    template = PageTemplate(id='main', frames=[frame3], onPage=all_write)
    doc.addPageTemplates([template])

    data2 = [
        ["Lab#", "Sample #", "Collection Method", "Sample\nType", "Collected", "Time\nCollected",
         "Numb\nCont", "Container", "Preservative"]
    ]

    edd_data = []
    if samp_type == sample_types[0]:
        edd_data = [bio_edd_header]
    elif samp_type == sample_types[1]:
        edd_data = [chem_edd_header]
    for i in range(len(data)):
        sample_part = data[i]
        if sample_part[4] == '':
            continue
        # print(sample_part)
        sample_tuple = (sample_part[1].lower(), sample_part[2].lower())
        colec = Paragraph("%s" % sample_part[1], tableStyle)
        sample_id = Paragraph("%s (%s)" % (sample_part[4], sample_part[0]), tableStyle)
        s_type = Paragraph("%s" % sample_part[2], tableStyle)
        # print(sample_part)

        # Move this block to when the date is pulled from the csv [

        time_value = sample_part[3]

        # ] Move this block to when the date is pulled from the csv

        coll_date = time_value.date()
        coll_time = time_value.time()
        # hour, minute, second = coll_time.split(':')
        # if coll_per == 'PM' and hour != '12':
        #     hour_int = int(hour)
        #     hour_int = hour_int + 12
        #     hour = str(hour_int)
        # elif coll_per == 'AM' and hour == '12':
        #     hour = "00"
        # coll_time = ':'.join([hour, minute, second])
        # print(coll_time)
        d_time = Paragraph("%s" % coll_date, tableStyle)
        c_time = Paragraph("%s" % coll_time, tableStyle)
        count = Paragraph("1", leftTable)
        if sample_tuple in containers.keys():
            contain = containers[sample_tuple]
            preserve = preservative[sample_tuple]
        else:
            contain = ""
            preserve = ""
        data2.append(["", sample_id, colec, s_type, d_time, c_time, count, contain, preserve])

        if samp_type == sample_types[0]:
            edd_data.append(["", sample_part[1], "%s (%s)" % (sample_part[4], sample_part[0])])
        elif samp_type == sample_types[1]:
            # add condition check for column locations
            edd_data.append(["%s (%s)" % (sample_part[4], sample_part[0]), lab_name,
                             "",  # ? Matrix
                             "", "", "%s %s" % (coll_date, coll_time), "", "", "", lab_name])

    # row heights should be determined automatically, except for the first row
    row_heights = len(data2) * [None]
    row_heights[0] = (inch / 2) + 10
    # set table to include previous data, establishing any important column widths
    t2 = Table(data2,
               colWidths=[inch, inch, (3 * inch / 2) + 10, None, inch - 10, inch - 10, inch / 2, None, None],
               rowHeights=row_heights,
               splitByRow=True,
               repeatRows=1)
    t2.setStyle(TableStyle([('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8),
                            ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('ALIGN', (6, 0), (6, -1), 'RIGHT'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                            ]))

    # put the table in a format the document will read
    text = [t2, PageBreak()]

    with open("%s/Generated Forms/%s_EDD.csv" % (curDir, new_name), 'w', newline='') as eddForm:
        writer = csv.writer(eddForm)

        for row in edd_data:
            writer.writerow(row)

    # build the document
    doc.build(text, canvasmaker=PageNumCanvas)


def form_number():
    today, t_time = str(datetime.today()).split()
    hour, minute, second = t_time.split(':')
    year, month, day = today.split('-')
    year = year[2:]
    second, remains = second.split('.')
    form_num = month + day + year + "-" + hour + minute + second
    return form_num


# create the function for writing all of the header information on every page
def head(canvas, docum):
    global pdf_details, location, contact
    details = pdf_details[0]
    canvas.saveState()
    # canvas.setFont('Times-Roman', 9)
    # canvas.drawString(doc.leftMargin, doc.height+30, "Page %d" % doc.page)
    canvas.setFont('Helvetica-Bold', 8)
    h = docum.height + 13
    canvas.drawString(docum.leftMargin + 4, h, "USEPA")
    canvas.drawCentredString((docum.width + 90) / 2, h, "CHAIN OF CUSTODY RECORD")
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawRightString(docum.width + 40, h, "No: %s" % form_number())
    canvas.setFont('Helvetica', 8)
    h = h - 13
    canvas.drawString(docum.leftMargin + 4, h, "DateShipped: ")
    canvas.drawCentredString((docum.width + 90) / 2, h, location)
    canvas.drawRightString(docum.width + 40, h, "Cooler #: ")
    h = h - 13
    canvas.drawString(docum.leftMargin + 4, h, "CarrierName: ")
    canvas.drawCentredString((docum.width + 90) / 2, h, "Lab Contact: %s" % details[1])
    canvas.drawRightString(docum.width + 40, h, "Lab: %s" % details[0])
    h = h - 13
    canvas.drawString(docum.leftMargin + 4, h, "AirbillNo: ")
    canvas.drawCentredString((docum.width + 90) / 2, h, "EPA Contact: %s" % contact)
    canvas.drawRightString(docum.width + 40, h, "Lab Phone: %s" % details[2])
    canvas.restoreState()


# create the function for drawing the lower 2 tables that don't get automatically filled in
def mid(canvas, docum):
    canvas.saveState()
    mid_y = (inch * 3) + 17
    # mid_y = mid_y - 13
    canvas.setFont('Helvetica-Bold', 8)
    # canvas.drawString((inch * 8) - 37, mid_y, "SAMPLES TRANSFERRED FROM")
    canvas.drawString((inch * 8) + 37, mid_y, "HAZMAT #")
    canvas.setFont('Helvetica', 8)
    canvas.drawString(inch - 18, mid_y, "Special Instructions:")
    mid_y = mid_y - 37
    canvas.drawString(inch - 13, mid_y, "Items/Reason        Relinquished by (Signature and Organization)            "
                                        "Date/Time              Received by (Signature and Organization)               "
                                        "Date/Time         Sample Condition Upon Receipt")
    canvas.rect(inch - 22, mid_y + 20, docum.width, (inch / 2) + 3, fill=0)
    canvas.line(8.4 * inch, mid_y + 20, 8.4 * inch, mid_y + 23 + (inch / 2))
    # canvas.line(7.4 * inch, mid_y + 10 + (inch / 2), 10.3 * inch, mid_y + 10 + (inch / 2))
    canvas.rect(inch - 22, inch - 5, docum.width, inch * 1.9)
    canvas.line(inch - 22, inch * 2.65, inch - 22 + docum.width, inch * 2.65)
    canvas.line(inch - 22, inch * 2.3, inch - 22 + docum.width, inch * 2.3)
    canvas.line(inch - 22, inch * 1.95, inch - 22 + docum.width, inch * 1.95)
    canvas.line(inch - 22, inch * 1.6, inch - 22 + docum.width, inch * 1.6)
    canvas.line(inch - 22, inch * 1.26, inch - 22 + docum.width, inch * 1.26)
    canvas.line(1.65 * inch, inch - 5, 1.65 * inch, inch * 2.82)
    canvas.line(4.15 * inch, inch - 5, 4.15 * inch, inch * 2.82)
    canvas.line(5.1 * inch, inch - 5, 5.1 * inch, inch * 2.82)
    canvas.line(7.6 * inch, inch - 5, 7.6 * inch, inch * 2.82)
    canvas.line(8.55 * inch, inch - 5, 8.55 * inch, inch * 2.82)
    canvas.restoreState()


# call the other 2 functions
def all_write(canvas, docum):
    head(canvas, docum)
    mid(canvas, docum)


def store(main_screen):
    global data_collected
    screen_label = main_screen.ids.screen_label

    root = Tk()
    root.title('Storage Directory')
    root.withdraw()
    store_path = askopenfilename()
    if os.path.exists(store_path):  # if they chose one
        if store_path[-4:] == '.csv':

            data_collected = True
        else:
            screen_label.text = f"{BaseColors.WARNING}The file selected was " \
                                f"not a CSV{BaseColors.ENDC}"
            data_collected = False
    else:
        screen_label.text = f"{BaseColors.WARNING}A file was NOT selected{BaseColors.ENDC}"
        data_collected = False
    return store_path


def convert(data_to_convert, character_list, conversion_dict, is_for_file_name=False,
            is_for_trouble=False):
    old_data = data_to_convert  # saving original data before variable is modified

    for char in character_list:  # iterate through chars in character_list and convert if necessary
        if char in data_to_convert:
            data_to_convert = data_to_convert.replace(char, conversion_dict[
                char]) if not is_for_file_name else data_to_convert.replace(char, "-") \
                if not is_for_trouble else data_to_convert.replace(char,
                                                                   " ")
            # data is converted to the appropriate character(s) depending on if the conversion is for a bad file name,
            # or to remove trouble characters, or simply to convert special chars to code chars
    if old_data != data_to_convert and is_for_file_name and is_for_trouble is not True:
        # if the data was converted, and it was for a bad file name and not only for a trouble character,
        # print this to user
        print("Error saving file with name %s, saved as %s instead." % (old_data, data_to_convert))
    return data_to_convert


os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'


class PageNumCanvas(Canvas):
    """
    http://code.activestate.com/recipes/546511-page-x-of-y-with-reportlab/
    http://code.activestate.com/recipes/576832/
    """

    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """Constructor"""
        Canvas.__init__(self, *args, **kwargs)
        self.pages = []

    # ----------------------------------------------------------------------
    def showPage(self):
        """
        On a page break, add information to the list
        """
        self.pages.append(dict(self.__dict__))
        self._startPage()

    # ----------------------------------------------------------------------
    def save(self):
        """
        Add the page number to each page (page x of y)
        """
        page_count = len(self.pages)

        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            Canvas.showPage(self)

        Canvas.save(self)

    # ----------------------------------------------------------------------
    def draw_page_number(self, page_count):
        """
        Add the page number
        """
        page = "Page %s of %s" % (self._pageNumber, page_count)
        self.setFont("Helvetica", 8)
        self.drawRightString(1.27 * inch, (8 * inch) - 5, page)


class MainScreenWidget(BoxLayout):
    num_rows = 0
    sys_id = os.environ["COMPUTERNAME"]
    btn = None

    def __init__(self, **kwargs):  # start the program and bind the 'X' button the exit function
        super(MainScreenWidget, self).__init__(**kwargs)
        # print(hasattr(super(), "__getattr__"))
        Window.bind(on_request_close=self.exit)
        # print("bind")
        self.btn = self.ids.startpdf
        # print("init")

    def clear(self):
        screen_label = self.ids.screen_label
        screen_label.text = ""

    @staticmethod
    def can_start():
        global data_collected
        if not data_collected:
            return False
        elif location == '':
            return False
        return True

    def exit(self, *args):
        exit_widget = ExitWidget()
        exit_widget.exit_widget_popup = Popup(
            title="                             Are you sure you want to quit?\n(unsaved data, "
                  "such as from an open QR Reader, will be lost)", content=exit_widget, size_hint=(None, None),
            size=(417, 155), auto_dismiss=True)
        exit_widget.exit_widget_popup.open()
        return True

    def scan(self):
        global selector, lab_drop_btn
        screen_label = self.ids.screen_label
        if not self.can_start():
            screen_label.text = f"{BaseColors.WARNING}CSV or Location not provided, " \
                                f"please correct{BaseColors.ENDC}"
            return False
        scan_button = ScanWidget()
        scan_button.main_window = self
        scan_button.scan_widget_popup = Popup(
            title="                      Select the lab for this selection of data\n                            "
                  "Select from the dropdown below", content=scan_button, size_hint=(None, None),
            size=(417, 180), auto_dismiss=False)
        top_half = scan_button.ids.tophalf
        top_half.add_widget(lab_drop_btn)

        scan_button.scan_widget_popup.open()

        return True

    def auto_pop(self):
        global selector, lab_drop_btn, method_drop_btn
        screen_label = self.ids.screen_label
        if not self.can_start():
            screen_label.text = f"{BaseColors.WARNING}CSV or Location not provided, " \
                                f"please correct{BaseColors.ENDC}"
            return False
        populate_button = PopulateWidget()
        populate_button.main_window = self
        populate_button.populate_widget_popup = Popup(
            title="                      Select the lab for this selection of data\n                            "
                  "Select from the dropdown below", content=populate_button, size_hint=(None, None),
            size=(417, 230), auto_dismiss=False)
        top_half = populate_button.ids.tophalf
        top_half.add_widget(lab_drop_btn)
        mid_sect = populate_button.ids.popdetails
        mid_sect.add_widget(method_drop_btn)

        populate_button.populate_widget_popup.open()

        return True

    def add_row(self, name, excess):
        # print(name)
        # print(excess)
        self.num_rows += 1
        new_row = RowWidget()
        new_row.main_screen = self

        new_row.ids.rownumber.text = str(self.num_rows)
        new_row.ids.samplefield.text = name
        btn = new_row.ids.buttonsection.children[0]
        # print(btn)
        btn.bind(on_release=self.remove_row)

        rows_section = self.ids.middlesection
        rows_section.height += 61
        rows_section.add_widget(new_row)

    def choose_type(self):
        samp_type = ContaminantWidget()
        samp_type.main_window = self
        samp_type.contam_widget_popup = Popup(title="select a Sample Type", content=samp_type,
                                              size_hint=(None, None),
                                              size=(500, 150), auto_dismiss=False)
        samp_type.main_screen = self
        samp_type.contam_widget_popup.open()

    def start_pdf(self, samp_type):
        global pdf_details, usedData, dataList, curData, lab_counts, pop_counts
        error_text = "CoC PDF cannot be made with zero samples selected\nPlease select samples then try again"
        lab_name = pdf_details[0][0]
        if len(curData) == 0:
            self.start_error(error_text)
            return False

        # Add popup for selecting sample type

        num = str(form_number())
        build_pdf(lab_name, num, curData, samp_type)
        # print("Built")
        count = lab_counts[lab_name] + len(curData)
        lab_counts[lab_name] = count
        # print("start Append")
        for sample in curData:
            usedData.append(sample)
        # print("Append")
        curData.clear()
        self.store_used()
        rows_section = self.ids.middlesection
        rows_section.clear_widgets()
        rows_section.height = 0
        pdf_details.clear()
        # print("start Count")
        for key in pop_counts.keys():
            pop_counts[key] = 0
        # print("Count")
        self.btn.pos = (-300, 10)
        self.num_rows = 0
        self.ids.screen_label.text = "Samples used: %d/%d\n" % (len(usedData), len(dataList))
        # print("finish")
        # Add body text for labs that have samples: check if lab has samples, display count for that lab

    def add_button(self):
        self.btn.pos = (10, 10)

    def video_start(self):
        global curData, dataList, video_getter, video_source, found, bag_counts
        screen_label = self.ids.screen_label

        # self.ids.screen_label.text = "test"

        self.add_button()
        try:
            if video_source == 'Integrated':  # start correct camera based on user choice at beginning
                video_getter = VideoStream(src=0).start()  # for integrated/built in webcam
            elif video_source == 'Separate':
                video_getter = VideoStream(src=1, resolution=(960, 720), ).start()
                # for separate webcam (usually USB connected)
            elif video_source == 'PiCamera':
                video_getter = VideoStream(usePiCamera=True).start()
        except:  # if an error occurs in creating video stream, print to user and return
            screen_label.text = f"{BaseColors.FAIL}An error occurred starting the QR Reader. " \
                                f"Check your cameras and try again.{BaseColors.ENDC}"
            video_getter = None
            self.main_window.ids.auto.pos = (370, 10)
            return

        # time.sleep(5.0)  # give camera time

        while True:
            frame = video_getter.frame

            frame = imutils.resize(frame, width=400)

            barcodes = pyzbar.decode(frame, symbols=[ZBarSymbol.QRCODE])

            # loop over the detected barcodes
            for barcode in barcodes:
                # extract the bounding box location of the barcode and draw the bounding box surrounding the
                # barcode on the image
                (x, y, w, h) = barcode.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                # the barcode data is a bytes object so if we want to draw it on our output image we need to convert it
                # to a string first
                barcode_data = barcode.data.decode("utf-8")

                # Convert barcodeData code chars back to special chars
                barcode_data = convert(barcode_data, code_characters, char_dict_code_to_special)

                # Draw the barcode data and barcode type on the image
                img = Image.new('RGB', (400, 15), color='white')
                img.putalpha(0)

                pil_image = Image.fromarray(frame)  # convert frame to pil image format, then to numpy array
                pil_image.paste(img, box=(x, y - 15),
                                mask=img)  # not sure exactly what's going on here, but it is vital I believe
                frame = np.array(pil_image)

                finder = filter(lambda a: barcode_data in a, dataList)
                test_list = list(finder)
                if barcode_data in bag_counts.keys():
                    sample = test_list[0]
                    if [sample[0], sample[4]] not in found:
                        found.append([sample[0], sample[4]])
                        curData.append(sample)
                        Clock.schedule_once(partial(self.add_row, barcode_data))
                        screen_label.text = f"{BaseColors.OKGREEN}%s added to outgoing sample list" \
                                            f"{BaseColors.ENDC}" % barcode_data
                        if bag_counts[barcode_data] > 1:  # duplication check
                            screen_label.text = f"{BaseColors.WARNING}%s has been added, but %s instances of the " \
                                                f"label were found in the csv file {BaseColors.ENDC}" % \
                                                (barcode_data, bag_counts[barcode_data])
                else:
                    screen_label.text = f"{BaseColors.WARNING}%s not in provided csv file" \
                                        f"{BaseColors.ENDC}" % barcode_data
                    # print(barcode_data)

            # show the output frame
            cv2.imshow("QR Toolbox", frame)

            if (cv2.waitKey(1) == ord("q")) or (cv2.getWindowProperty('QR Toolbox', cv2.WND_PROP_VISIBLE) < 1):
                break

        if video_getter is not None:
            video_getter.stop()  # reset and close everything related to the video stream
            video_getter.stream.release()
            video_getter = None
        if self.num_rows == 0:
            self.btn.pos = (-300, 10)
        cv2.destroyAllWindows()

    def remove_row(self, value):
        global curData, found
        btn_section = value.parent
        row = btn_section.parent
        num = int(row.ids.rownumber.text)

        root = self.ids.middlesection
        for item in root.children[:]:
            if int(item.ids.rownumber.text) <= num:
                continue
            elif int(item.ids.rownumber.text) > num:
                new_num = int(item.ids.rownumber.text) - 1
                item.ids.rownumber.text = str(new_num)
        sample = curData.pop(num - 1)
        if [sample[0], sample[4]] in found:
            found.remove([sample[0], sample[4]])
        root.remove_widget(row)
        root.height -= 61
        self.num_rows -= 1

    def select_storage(self):
        global contact_num, contact_name
        storage_location = StorageWidget()
        storage_location.storage_popup = Popup(title="Select a storage location", content=storage_location,
                                               size_hint=(None, None),
                                               size=(500, 310), auto_dismiss=False)
        storage_location.main_screen = self
        storage_location.ids.contact_name.text = contact_name
        storage_location.ids.contact_num.text = contact_num
        storage_location.storage_popup.open()

    def settings(self):
        setting = SettingWidget()
        setting.setup_popup = Popup(title="Settings:", content=setting,
                                    size_hint=(None, None),
                                    size=(500, 360), auto_dismiss=True)
        setting.main_screen = self
        setting.setup_popup.open()

    def start_error(self, text):
        error_widget = ErrorMessageWidget()
        error_widget.ids.message.text = f"{BaseColors.WARNING}%s{BaseColors.ENDC}" % text
        error_widget.error_widget_popup = Popup(
            title="", content=error_widget, size_hint=(None, None),
            size=(417, 100), auto_dismiss=True)
        error_widget.error_widget_popup.open()

        # time.sleep(20.0)
        #
        # error_widget.error_widget_popup.dismiss()
        return True

    def get_memory(self):
        mem_location = MemoryWidget()
        mem_location.memory_popup = Popup(title="Select a memory file", content=mem_location,
                                          size_hint=(None, None),
                                          size=(500, 150), auto_dismiss=False)
        mem_location.main_screen = self
        mem_location.memory_popup.open()

    def store_used(self):
        global curMemory, usedData, lab_counts
        temp_list = usedData.copy()
        temp_list.append(list(lab_counts.items()))
        with open(curMemory, "wb+") as mem_file:
            pickle.dump(temp_list, mem_file)

    def grab_used(self):
        global curMemory, usedData, found, lab_counts
        with open(curMemory, "rb") as mem_file:
            temp_list = pickle.load(mem_file)
        usedData = temp_list[:len(temp_list) - 1]
        for sample in usedData:
            found.append([sample[0], sample[4]])
        dict_list = temp_list[-1]
        for item in dict_list:
            lab_counts[item[0]] = item[1]

    def find_online(self, source, popup):
        online_layer = OnlineWidget()
        online_layer.online_popup = Popup(title="Enter layer information", content=online_layer,
                                          size_hint=(None, None),
                                          size=(500, 350), auto_dismiss=False)
        online_layer.main_screen = self
        online_layer.popup_widget = popup
        online_layer.source_class = source
        online_layer.online_popup.open()


class ScreenWidget(ScrollView):
    pass


class RowWidget(StackLayout):
    main_screen = None


class ScanWidget(BoxLayout):
    main_window = None
    scan_widget_popup = None

    def start_scan(self):
        global pdf_details
        error_text = "One or more required fields were not filled out\nPlease go back and fix this"
        labels = lab_drop_btn.text
        for lab in labInfo:
            if lab[0] == labels:
                labels = lab
                break
        if labels == lab_drop_btn.text:
            self.main_window.start_error(error_text)
            return False
        pdf_details = [labels]
        # self.main_window.ids.auto.pos = (-200, 10)
        # self.main_window.ids.screen_label.text = "Samples used: %d/%d" % (len(usedData), len(dataList))
        self.rem_drop()
        threading.Thread(target=self.main_window.video_start, daemon=True).start()
        # self.main_window.video_start()

    def rem_drop(self):
        top_half = self.ids.tophalf
        top_half.remove_widget(lab_drop_btn)
        lab_drop_btn.text = "Select Lab"
        self.scan_widget_popup.dismiss()


class PopulateWidget(BoxLayout):
    main_window = None
    populate_widget_popup = None

    def start_pop(self):
        global pdf_details
        error_text = "One or more required fields were not filled out\nPlease go back and fix this"
        labels = lab_drop_btn.text
        num_samples = self.ids.popcount.text
        if num_samples == '':
            self.main_window.start_error(error_text)
            return False
        type_samples = method_drop_btn.text
        if type_samples == '' or type_samples == "Select Collection Method":
            self.main_window.start_error(error_text)
            return False
        for lab in labInfo:
            if lab[0] == labels:
                labels = lab
                break
        if labels == lab_drop_btn.text:
            self.main_window.start_error(error_text)
            return False
        pdf_details = [labels]
        # self.main_window.ids.scan.pos = (-200, 10)
        # self.main_window.ids.screen_label.text = "Samples used: %d/%d" % (len(usedData), len(dataList))
        self.populate(num_samples, type_samples)
        self.rem_drop()

    def rem_drop(self):
        top_half = self.ids.tophalf
        top_half.remove_widget(lab_drop_btn)
        lab_drop_btn.text = "Select Lab"
        mid_sect = self.ids.popdetails
        mid_sect.remove_widget(method_drop_btn)
        method_drop_btn.text = "Select Collection Method"
        self.populate_widget_popup.dismiss()

    def populate(self, num_sample, type_samples):
        global curData, dataList, found, pop_counts, bag_counts
        screen_label = self.main_window.ids.screen_label
        count = int(num_sample)
        warning_text = f"{BaseColors.WARNING}Warning: {BaseColors.ENDC}"
        # print(len(warning_text))
        type_samples = type_samples.lower()
        i = 0
        track = pop_counts[type_samples]
        # base = 0
        temp_data = []

        # any not returning any, only 1 of 6

        # if type_samples.lower() in pop_counts:
        #     base = pop_counts[type_samples.lower()]
        #     count += base
        if track >= len(dataList):
            warning_text = warning_text + "All %s samples have been found in the csv at least once\n " \
                                          "Starting search back from the beginning\n" % type_samples
            track = 0

        for match in dataList[track:]:
            if match[1].lower() == type_samples or type_samples == "any":
                # print(match[4] + ": " + str(dataList.count(match[4])))
                if match[4] == "":
                    continue
                elif [match[0], match[4]] in found:  # add duplication error/check
                    continue
                if bag_counts[match[4]] > 1:
                    warning_text = warning_text + "Sample %s is in the dataset %s times\n" % \
                                   (match[4], bag_counts[match[4]])
                temp_data.append(match)
                found.append([match[0], match[4]])
                i += 1
                if i >= count:
                    new_index = dataList.index(match) + 1
                    pop_counts[type_samples] = new_index
                    if type_samples == "any":
                        for samp_types in pop_counts.keys():
                            if pop_counts[samp_types] < new_index:
                                pop_counts[samp_types] = new_index
                    break
            if dataList.index(match) == len(dataList) - 1:
                pop_counts[type_samples] = len(dataList)
                warning_text = warning_text + f"{BaseColors.WARNING}Only %d samples found with " \
                                              f"type %s{BaseColors.ENDC}" % (i, type_samples)

        # pop_counts[type_samples.lower()] = count
        if len(warning_text) > 33:
            screen_label.text = warning_text

        # print(header)
        for sample in temp_data:
            self.main_window.add_row(sample[4], 0)
            curData.append(sample)
        self.main_window.add_button()


class ExitWidget(BoxLayout):
    exit_widget_popup = None

    """ This function closes the program if the user clicked 'Yes' when asked """

    def confirm_exit(self):
        self.get_root_window().close()
        App.get_running_app().stop()


class StorageWidget(BoxLayout):
    # initial csv selection
    text = "Select the data source with the sample data"
    storage_popup = None
    main_screen = None

    def store_data(self):
        global dataList, bag_counts, location, contact_name, contact_num, contact, lab_counts, usedData, pop_counts
        screen_label = self.main_screen.ids.screen_label
        dataList = []  # need to reset pointers for pop, getting "all x found restarting search warning"
        bag_counts = {}
        usedData = []
        for key in pop_counts.keys():
            pop_counts[key] = 0
        for lab in lab_counts.keys():
            lab_counts[lab] = 0
        location = self.ids.location.text
        contact_name = self.ids.contact_name.text
        contact_num = self.ids.contact_num.text
        contact = "%s; %s" % (contact_name, contact_num)
        return screen_label

    def get_csv_file(self):
        global dataList, data_collected, sample_id_col, date_time_col, location_col, location_head, sample_id_head, \
            sample_type_head, date_time_head, sample_type_col, sample_method_col, sample_method_head, headers, \
            csvTitle, bag_counts
        screen_label = self.store_data()
        filename = store(self.main_screen)
        if data_collected:  # from a csv, restructure this
            with open(filename, "r", encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                all_samples = list(reader)
            headers = all_samples[0]
            for col in headers:
                if col.lower() == location_head:
                    location_col = headers.index(col)
                elif col.lower() == sample_id_head:
                    sample_id_col = headers.index(col)
                elif col.lower() == date_time_head:
                    date_time_col = headers.index(col)
                elif col.lower() == sample_type_head:
                    sample_type_col = headers.index(col)
                elif col.lower() == sample_method_head:
                    sample_method_col = headers.index(col)
            all_samples = all_samples[1:]
            for sample in all_samples:
                if sample[sample_id_col] == '':
                    continue
                if sample[sample_id_col] not in bag_counts.keys():
                    bag_counts[sample[sample_id_col]] = 0
                fixed_time = sample[date_time_col].replace(',','')
                temp_time = datetime.strptime(fixed_time, "%m/%d/%Y %I:%M:%S %p")
                timezone = get_localzone()
                time_value = temp_time.replace(tzinfo=pytz.utc).astimezone(timezone)
                dataList.append([sample[location_col], sample[sample_method_col], sample[sample_type_col],
                                 time_value, sample[sample_id_col]])
                bag_counts[sample[sample_id_col]] += 1
            temp = filename.split('/')
            csvTitle = temp[-1].split('.')[0]
            # print(bag_counts)
            # found = []
            screen_label.text = f"{BaseColors.OKGREEN}CSV Selected: {temp[-1]}{BaseColors.ENDC}\n" \
                                f"{len(dataList)}"
            self.storage_popup.dismiss()
            self.main_screen.get_memory()
        # print(location)

    def get_online_layer(self):
        screen_label = self.store_data()  # do something to set the label
        # print(StorageWidget)
        # print(type(StorageWidget))
        # print(type(self))
        self.main_screen.find_online(self, self.storage_popup)


class OnlineWidget(BoxLayout):
    online_popup = None
    main_screen = None
    popup_widget = None
    source_class = None

    def access_layer(self):
        global accessed_server, gis_owner, gis_title, epa_client_id, epa_url, oneepa_url, oneepa_client_id, \
            sample_id_gis, sample_method_gis, sample_type_gis, location_gis, date_time_gis, data_collected, dataList, \
            bag_counts, usedData, lab_counts, csvTitle
        # set in checks for text fields being empty
        if self.ids.epa_server.state == 'down':
            accessed_server = 0
        elif self.ids.oneepa_server.state == 'down':
            accessed_server = 1
        else:
            accessed_server = -1
        gis_owner = self.ids.owner.text
        gis_title = self.ids.layer.text
        screen_label = self.main_screen.ids.screen_label
        query = 'type:feature AND owner:%s AND title:"%s"' % (gis_owner, gis_title)
        source = type(self.source_class)
        print(source)

        match accessed_server:
            case 0:
                url = epa_url
                client_id = epa_client_id
                # print(url)
            case 1:
                url = oneepa_url
                client_id = oneepa_client_id
                # print("test")
            case _:
                url = ""
                client_id = ""
                # set error here
                # print("fail")
        gis = GIS(url, client_id=client_id)
        gis_query = gis.content.search(query=query, max_items=15)
        if len(gis_query) == 0:
            # error message
            data_collected = False
            return
        else:
            data_collected = True
            self.online_popup.dismiss()
            self.popup_widget.dismiss()
        first = gis_query[0]
        gis_name = first.title
        print(gis_name)
        layers = first.layers
        initial = layers[0]
        features = initial.query(
            out_fields=[location_gis, sample_method_gis, sample_type_gis, date_time_gis, sample_id_gis],
            return_geometry=False
        ).to_dict()['features']
        print(features)
        for i in range(len(features)):
            temp = features[i]['attributes']
            if temp[sample_id_gis] == None:
                continue
            if temp[sample_id_gis] not in bag_counts.keys():
                bag_counts[temp[sample_id_gis]] = 0
            s = temp[date_time_gis] / 1000.0
            temp_time = datetime.fromtimestamp(s)  # .strptime('%Y-%m-%d %H:%M:%S')
            # print(temp_time)
            dataList.append([temp[location_gis], temp[sample_method_gis], temp[sample_type_gis], temp_time, temp[sample_id_gis]])
            bag_counts[temp[sample_id_gis]] += 1
        # print(count[0][3])
        print(dataList)
        if source == StorageWidget:
            usedData = []
            csvTitle = gis_name
            for lab in lab_counts.keys():
                lab_counts[lab] = 0
            screen_label.text = f"{BaseColors.OKGREEN}layer Selected: {gis_name}{BaseColors.ENDC}\n" \
                                f"{len(dataList)}"
            self.main_screen.get_memory()
        elif source == AppendWidget:
            screen_label.text = f"{BaseColors.OKGREEN}layer Added: {gis_name}{BaseColors.ENDC}\n" \
                                f"{len(dataList)}"


class AppendWidget(BoxLayout):
    append_popup = None
    main_screen = None

    def add_csv(self):
        global dataList, data_collected, sample_id_col, date_time_col, location_col, location, bag_counts, \
            location_head, sample_id_head, sample_type_head, date_time_head, sample_type_col, sample_method_col, \
            sample_method_head, headers

        filename = store(self.main_screen)
        screen_label = self.main_screen.ids.screen_label
        all_samples = []
        if data_collected:
            with open(filename, "r", encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                all_samples = list(reader)
            headers = all_samples[0]
            for col in headers:
                if col.lower() == location_head:
                    location_col = headers.index(col)
                elif col.lower() == sample_id_head:
                    sample_id_col = headers.index(col)
                elif col.lower() == date_time_head:
                    date_time_col = headers.index(col)
                elif col.lower() == sample_type_head:
                    sample_type_col = headers.index(col)
                elif col.lower() == sample_method_head:
                    sample_method_col = headers.index(col)
            all_samples = all_samples[1:]
            for sample in all_samples:
                if sample[sample_id_col] == '':
                    continue
                else:
                    finder = filter(lambda a: sample[location_col] in a, dataList)
                    existing = list(finder)
                    copies = []
                    # print(existing)
                    for finding in existing:
                        if finding[location_col] == sample[location_col]:
                            copies.append(finding)
                            break
                    if len(copies) == 0:
                        if sample[sample_id_col] not in bag_counts.keys():
                            bag_counts[sample[sample_id_col]] = 0
                        fixed_time = sample[date_time_col].replace(',','')
                        temp_time = datetime.strptime(fixed_time, "%m/%d/%Y %I:%M:%S %p")
                        timezone = get_localzone()
                        time_value = temp_time.replace(tzinfo=pytz.utc).astimezone(timezone)
                        dataList.append([sample[location_col], sample[sample_method_col], sample[sample_type_col],
                                         time_value, sample[sample_id_col]])
                        bag_counts[sample[sample_id_col]] += 1
            # print(dataList)
            temp = filename.split('/')

            screen_label.text = f"{BaseColors.OKGREEN}CSV added: {temp[-1]}{BaseColors.ENDC}\n" \
                            f"{len(dataList)}"
            self.append_popup.dismiss()

    def add_gis(self):
        self.main_screen.find_online(self, self.append_popup)


class SettingWidget(BoxLayout):
    main_screen = None
    setup_popup = None

    def show_count(self):
        global lab_counts
        lab_widget = LabCountWidget()
        temp_text = ""
        height = 50
        for lab in lab_counts.keys():
            temp_text = temp_text + "\n%s: %d Samples\n" % (lab, lab_counts[lab])
            height += 40
        lab_widget.ids.message.text = temp_text
        lab_widget.lab_widget_popup = Popup(title="Samples assigned per lab", content=lab_widget,
                                            size_hint=(None, None),
                                            size=(400, height), auto_dismiss=True)
        lab_widget.lab_widget_popup.open()

    def camera_source(self):
        camera = CameraWidget()
        camera.camera_popup = Popup(title="Select a camera source", content=camera,
                                    size_hint=(None, None),
                                    size=(261, 375), auto_dismiss=True)
        camera.main_screen = self.main_screen
        camera.camera_popup.open()

    def storage(self):
        global contact_num, contact_name, location
        storage_location = StorageWidget()
        storage_location.storage_popup = Popup(title="Select a storage location", content=storage_location,
                                               size_hint=(None, None),
                                               size=(500, 310), auto_dismiss=True)
        storage_location.main_screen = self.main_screen
        storage_location.ids.location.text = location
        storage_location.ids.contact_name.text = contact_name
        storage_location.ids.contact_num.text = contact_num
        storage_location.storage_popup.open()

    def append(self):
        append = AppendWidget()
        append.append_popup = Popup(title="select a CSV to append", content=append,
                                    size_hint=(None, None),
                                    size=(500, 150), auto_dismiss=False)
        append.main_screen = self.main_screen
        append.append_popup.open()

    def memory(self):
        self.main_screen.get_memory()

    def headers(self):
        header = AlterHeaderWidget()
        header.header_popup = Popup(title="What are the Header Titles", content=header,
                                    size_hint=(None, None),
                                    size=(500, 250), auto_dismiss=False)
        header.main_screen = self.main_screen
        header.setup()
        header.header_popup.open()


#
# class StoreSettingWidget(BoxLayout):
#     text = "Select the CSV with the sample data"
#     storage_popup = None
#
#     def get_csv_file(self):
#         global dataList, data_collected, sample_id_col, date_time_col, location_col, location, sample_type_col, \
#             sample_method_col, sample_method_head, sample_id_head, sample_type_head, location_head, date_time_head, \
#             headers, csvTitle, bag_counts, location, contact, contact_name, contact_num
#         screen_label = self.main_screen.ids.screen_label
#         filename = store(self.main_screen)
#         dataList = []
#         bag_counts = {}
#         location = self.ids.location.text
#         contact_name = self.ids.contact_name.text
#         contact_num = self.ids.contact_num.text
#         contact = "%s: %s" % (contact_name, contact_num)
#         if data_collected:
#             with open(filename, "r", encoding='utf-8-sig') as csvfile:
#                 reader = csv.reader(csvfile)
#                 allSamples = list(reader)
#             headers = allSamples[0]
#             for col in headers:
#                 if col.lower() == location_head:
#                     location_col = headers.index(col)
#                 elif col.lower() == sample_id_head:
#                     sample_id_col = headers.index(col)
#                 elif col.lower() == date_time_head:
#                     date_time_col = headers.index(col)
#                 elif col.lower() == sample_type_head:
#                     sample_type_col = headers.index(col)
#                 elif col.lower() == sample_method_head:
#                     sample_method_col = headers.index(col)
#             allSamples = allSamples[1:]
#             for sample in allSamples:
#                 if sample[sample_id_col] == '':
#                     continue
#                 if sample[sample_id_col] not in bag_counts.keys():
#                     bag_counts[sample[sample_id_col]] = 0
#                 dataList.append(sample)
#                 bag_counts[sample[sample_id_col]] += 1
#             temp = filename.split('/')
#             csvTitle = temp[-1].split('.')[0]
#             # print(bag_counts)
#             temp = filename.split('/')
#             csvTitle = temp[-1].split('.')[0]
#             # print(csvTitle)
#             screen_label.text = f"{BaseColors.OKGREEN}CSV Selected: {temp[-1]}{BaseColors.ENDC}\n" \
#                                 f"{len(dataList)}"
#             self.storage_popup.dismiss()


class AlterHeaderWidget(BoxLayout):
    header_popup = None

    def setup(self):
        global location_head, sample_id_head, sample_type_head, date_time_head, sample_method_head
        self.ids.location.text = location_head
        self.ids.bag_id.text = sample_id_head
        self.ids.type.text = sample_type_head
        self.ids.date.text = date_time_head
        self.ids.method.text = sample_method_head

    def finish(self):
        global location_head, sample_id_head, sample_type_head, date_time_head, sample_method_head, \
            sample_method_col, sample_type_col, sample_id_col, location_col, date_time_col, \
            dataList, data_collected, headers

        location_head = self.ids.location.text
        sample_id_head = self.ids.bag_id.text
        sample_type_head = self.ids.type.text
        date_time_head = self.ids.date.text
        sample_method_head = self.ids.method.text

        if data_collected:
            for col in headers:
                if col.lower() == location_head:
                    location_col = headers.index(col)
                elif col.lower() == sample_id_head:
                    sample_id_col = headers.index(col)
                elif col.lower() == date_time_head:
                    date_time_col = headers.index(col)
                elif col.lower() == sample_type_head:
                    sample_type_col = headers.index(col)
                elif col.lower() == sample_method_head:
                    sample_method_col = headers.index(col)


class MemoryWidget(BoxLayout):
    memory_popup = None
    main_screen = None

    def no_memory(self):
        global curDir, curMemory, csvTitle, bad_file_name_list, empty_dict
        new_name = convert(csvTitle, bad_file_name_list, empty_dict, True)
        curMemory = "%s/%s_Memory.txt" % (curDir, new_name)

    def find_memory(self):
        global curMemory
        screen_label = self.main_screen.ids.screen_label
        root = Tk()
        root.title('Storage Directory')
        root.withdraw()
        mem_path = askopenfilename()
        if os.path.exists(mem_path):  # if they chose one
            if mem_path[-4:] == '.txt':
                curMemory = mem_path
                self.main_screen.grab_used()
                screen_label.text = "Samples used: %d/%d" % (len(usedData), len(dataList))
                self.memory_popup.dismiss()
            else:
                screen_label.text = f"{BaseColors.WARNING}The file selected was " \
                                    f"not a TXT{BaseColors.ENDC}"
        else:
            screen_label.text = f"{BaseColors.WARNING}A file was NOT selected{BaseColors.ENDC}"


class CameraWidget(BoxLayout):

    @staticmethod
    def set_camera(camera):
        global video_source
        video_source = camera


class ErrorMessageWidget(BoxLayout):
    error_widget_popup = None


class LabCountWidget(BoxLayout):
    lab_widget_popup = None


class ContaminantWidget(BoxLayout):
    main_window = None
    contam_widget_popup = None

    def set_sample_type(self, count):
        global sample_types
        self.main_window.start_pdf(sample_types[count])
        # print("finish")


class COCPDFToolApp(App):
    main_screen = None

    def build(self):
        self.main_screen = MainScreenWidget()
        # print("main")
        Window.size = (900, 650)
        # print("built")
        return self.main_screen

    def get_labs(self):
        global labInfo, drop_menu_1, lab_drop_btn, lab_counts
        lab_file = curDir + "\\labs.csv"
        with open(lab_file, "r", encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            labInfo = list(reader)
        for lab in range(len(labInfo)):
            if lab == 0:
                continue
            info = labInfo[lab]
            lab_counts[info[0]] = 0
            btn = Button(text='%s' % info[0], size_hint_y=None, height=30)
            btn.bind(on_release=lambda button: drop_menu_1.select(button.text))
            drop_menu_1.add_widget(btn)
        lab_drop_btn.bind(on_release=drop_menu_1.open)
        drop_menu_1.bind(on_select=lambda instance, x: setattr(lab_drop_btn, 'text', x))

    def get_containers(self):
        global containers, preservative, pop_counts, method_drop_btn, drop_menu_2
        con_file = curDir + "\\containers.csv"
        temp_methods = []
        with open(con_file, "r", encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            temp_list = list(reader)
        # print(temp_list)
        for con in range(len(temp_list)):
            if con == 0:
                continue
            contain = temp_list[con]
            if contain[0] not in temp_methods:
                temp_methods.append(contain[0])
                btn = Button(text='%s' % contain[0], size_hint_y=None, height=30)
                btn.bind(on_release=lambda button: drop_menu_2.select(button.text))
                drop_menu_2.add_widget(btn)
            contain[0] = contain[0].lower()
            contain[1] = contain[1].lower()
            containers[tuple(contain[:2])] = contain[2]
            preservative[tuple(contain[:2])] = contain[3]
            if contain[0] not in pop_counts.keys():
                pop_counts[contain[0]] = 0
        pop_counts["any"] = 0
        btn = Button(text='Any', size_hint_y=None, height=30)
        btn.bind(on_release=lambda button: drop_menu_2.select(button.text))
        drop_menu_2.add_widget(btn)
        method_drop_btn.bind(on_release=drop_menu_2.open)
        drop_menu_2.bind(on_select=lambda instance, x: setattr(method_drop_btn, 'text', x))
        # print(preservative[("rmc","field blank")])
        # print(containers)
        # print(pop_counts)

    def on_start(self):
        self.get_labs()
        self.get_containers()
        self.main_screen.select_storage()


if __name__ == '__main__':
    try:
        if hasattr(sys, '_MEIPASS'):
            resource_add_path(os.path.join(sys._MEIPASS))
        app = COCPDFToolApp()
        app.run()
    except Exception as e:
        print(e)
        input("Press enter.")
