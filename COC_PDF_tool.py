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
# import time
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
from reportlab.platypus.flowables import Flowable
from tkinter import Tk  # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename

"""
To be worked on:
    Add direct access
        restructure code to use either csv or gis
            add check for valid source layer
            restructure appending source
                redesign internal storage to only store the necessities
            rename confirmation text to reference which source was used
    figure out why it doesn't run on regular laptops
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
epa_client_id = 'vpeanPqMcHdq7G6z'  # EPA
oneepa_client_id = 'tEHtLLr2xrIVpp3k'  # OneEPA
gis_owner = "jdeagan_epa"  # clear this out
gis_title = "Water Collection Test"  # clear this out
accessed_server = -1
col_indexes = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
csv_headers = ['collection method', 'sample type', 'time/date collected', 'sample bag id', 'sodium thiosulfate added',
               'free chlorine (mg/l)', 'ph', 'temperature (°c)', 'total dissolved solids (ppm)', 'conductivity (μs/cm)',
               'salinity (ppm)', 'volume', 'other water measurement(s)', 'start meter reading', 'end meter reading',
               'flow rate measurements (l/min)', 'uf start time', 'uf end time']
gis_headers = ["collection_method", "sample_type", "start_time_date", "sample_bag_id", "sodium", "free_chlorine", "ph",
               "temperature", "dissolved_solids", "conductivity", "salinity", "volume", "other_measurement",
               "start_meter", "end_meter", "flow_rate", "uf_start_time", "uf_end_time"]
video_source = 'Integrated'
contact = "Mia Mattioli; 404-718-5643"
contact_name = "Mia Mattioli"
contact_num = "404-718-5643"
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
style = styles['BodyText']
# create custom styles for the table to use for the Paragraphs
tableStyle = ParagraphStyle('Table Body',
                            fontName="Helvetica",
                            fontSize=7,
                            parent=style,
                            alignment=0,  # Left side
                            spaceAfter=10)
leftTable = ParagraphStyle('Left Table Body',
                           fontName="Helvetica",
                           fontSize=7,
                           parent=style,
                           alignment=2,  # Right
                           spaceAfter=10)
headerStyle = ParagraphStyle('Header Body',
                             fontName="Helvetica",
                             fontSize=7,
                             parent=styles['Heading2'],
                             alignment=0,  # Left side
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


class VerticalText(Flowable):

    def __init__(self, text):
        Flowable.__init__(self)
        self.text = text

    def draw(self):
        canvas = self.canv
        canvas.rotate(90)
        fs = canvas._fontsize
        canvas.translate(1, -fs / 1.2)  # canvas._leading?
        canvas.drawString(0, 0, self.text)

    def wrap(self, aW, aH):
        canv = self.canv
        fn, fs = canv._fontname, canv._fontsize
        return canv._leading, 1 + canv.stringWidth(self.text, fn, fs)


class VerticalTexts(Flowable):

    def __init__(self, text):
        Flowable.__init__(self)
        self.text = text

    def draw(self):
        canvas = self.canv
        canvas.rotate(90)
        fs = canvas._fontsize
        canvas.translate(1, -fs / 2)  # canvas._leading?
        temp_text = self.text.split('\n')
        for item in range(len(temp_text)):
            canvas.drawString(0, item * -10, temp_text[item])

    def wrap(self, aW, aH):
        canv = self.canv
        fn, fs = canv._fontname, canv._fontsize
        return canv._leading, 1 + canv.stringWidth(self.text, fn, fs)


def build_pdf(num, data):
    global pdf_details, curDir, containers, preservative, bad_file_name_list, empty_dict, contact_name, contact_num
    lab_short = pdf_details[0][0]
    lab_name = pdf_details[0][1]
    # start the document
    name = lab_short + " " + num
    new_name = convert(name, bad_file_name_list, empty_dict, True)
    doc = BaseDocTemplate("%s/Generated Forms/%s_CoC.pdf" % (curDir, new_name),
                          pagesize=(11 * inch, 8.5 * inch),
                          rightMargin=inch * 0.6,
                          leftMargin=inch * 0.6,
                          topMargin=inch * 0.6,
                          bottomMargin=inch * 0.6)

    # y1 = doc.bottomMargin + (doc.height / 4) + 65
    # y2 = doc.bottomMargin + 50

    frame3 = Frame(doc.leftMargin,
                   doc.bottomMargin,
                   doc.width,
                   doc.height,
                   leftPadding=0,
                   bottomPadding=0,
                   rightPadding=0,
                   topPadding=0,
                   id='top')

    template1 = PageTemplate(id='main', frames=[frame3])
    header1 = [
        ["CENTERS FOR DISEASE CONTROL AND PREVENTION", "", "", "", "", "CHAIN OF CUSTODY RECORD", "", "", "", "", "",
         "", "", ""],
        ["WATERBORNE DISEASE PREVENTION BRANCH", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        [f"SHIP TO: {lab_name}", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        [f"ATTN: {contact_name}", "", "", "", f"PHONE: {contact_num}", "", "", "", "", "", "", "", "", ""],
        ["CLIENT NAME:", "", "", "", "PROJECT:",
         VerticalTexts("Grab (G), Composite (C), or\nUltrafilter (UF)"),
         VerticalText("Sodium Thiosulfate Added (Y/N)"),
         VerticalTexts("Free chlorine (mg/L, enter total\nchlorine on reverse)"),
         VerticalText("pH"), VerticalText("Temperature (°C)"), VerticalText("Total Dissolved Solids (ppm)"),
         VerticalText("Conductivity (μS/cm)"), VerticalText("Salinity (ppm)"), "CSID\n(LAB USE ONLY)"],
        ["ADDRESS:", "", "", "", "PHONE:\nFAX:\nEMAIL:", "", "", "", "", "", "", "", "", ""],
        ["PROJECT MANAGER:", "", "", "", "SAMPLER:", "", "", "", "", "", "", "", "", ""],
        ["DATE", "TIME", "VOLUME", "SMPL\nTYPE", "SAMPLE IDENTIFICATION", "", "", "", "", "", "", "", "", ""]]

    header2 = [
        ["CENTERS FOR DISEASE CONTROL AND PREVENTION", "", "", "", "CHAIN OF CUSTODY RECORD", "", "", "", "", ""],
        [f"WATERBORNE DISEASE PREVENTION BRANCH\n{lab_name}", "", "", "", "", "", "", "", "", ""],
        [f"ATTN: {contact_name}", "", f"PHONE: {contact_num}", "", "ULTRAFILTRATION VOLUME MEASUREMENT", "", "", "", "",
         ""],
        ["SAMPLE IDENTIFICATION", "LATITUDE", "LONGITUDE", "OTHER WATER\nMEASUREMENT(S)", "START\nTIME", "END TIME",
         "START METER\nREADING", "END METER\nREADING", "FLOW RATE\nMEASUREMENTS (L/MIN)", ""]]

    footer1 = [["SIGNATURE:", "", "", "PRINT NAME:", "", "DATE:", "", "", "TIME:", "", "SAMPLE CONDITION:", "", "",
                "SAMPLE TYPE\nCODES:"],
               ["RELINQUISHED BY:", "", "", "", "", "", "", "", "", "", "(FOR LAB USE ONLY)", "", "", ""],
               ["", "", "", "", "", "", "", "", "", "", "Received On Ice", "", "Y    /    N", "W = Water"],
               ["RECEIVED BY:", "", "", "", "", "", "", "", "", "", "", "", "", "SW = Surface Water"],
               ["", "", "", "", "", "", "", "", "", "", "Container Intact", "", "Y    /    N", "GW = Ground Water"],
               ["PLEASE SHIP SAMPLES ON ICE TO KEEP COLD DURING OVERNIGHT SHIPMENT", "", "", "", "", "", "", "", "", "",
                "", "",
                "", "DW = Drinking Water"],
               ["(EXCEPT FOR NAEGLERIA FOWLERI TESTING-FOR WHICH SAMPLES SHOULD BE SHIPPED NON-CHILLED)", "", "", "",
                "",
                "", "", "", "", "", "Seals Present", "", "Y    /    N", "WW = Waste Water"],
               ["", "", "", "", "", "", "", "", "", "", "", "", "", "PW = Pool Water"],
               ["CDC Laboratory Notes Upon Receipt:", "", "", "", "", "", "", "", "", "", "Samples Missing", "",
                "Y    /    N",
                "SE = Sediment"],
               ["", "", "", "", "", "", "", "", "", "", "", "", "", "SL = Sludge"],
               ["", "", "", "", "", "", "", "", "", "", "Extra Samples", "", "Y    /    N", "OT = Other Matrix"],
               ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
               ["", "", "", "", "", "", "", "", "", "", "Hold time exceeded", "", "Y    /    N", ""],
               ["", "", "", "", "", "", "", "", "", "", "", "", "", ""]]

    footer2 = [["PLEASE SHIP SAMPLES ON ICE TO KEEP COLD DURING OVERNIGHT SHIPMENT\n(EXCEPT FOR NAEGLERIA FOWLERI "
                "TESTING-FOR WHICH SAMPLES SHOULD BE SHIPPED NON-CHILLED)", "", "", "", "", "", "", "", "", ""],
               ["COMMENTS/FIELD OBSERVATIONS:", "", "", "", "", "", "", "", "", ""]]

    doc.addPageTemplates([template1])
    # [["Date","Time","Volume","Sample Type","Sample Identification","G,C,or UF","Sodium Added","Free Chlorine","pH",
    #  "Temp","Dissolved Solids","Conductivity","Salinity"],
    #  ["Sample Identification","Latitude","Longitude","Other measurements","Start Time","End Time","Start Reading",
    #   "End Reading","Flow Rate",""]]
    # data2 = [
    #     ["Lab#", "Sample #", "Collection Method", "Sample\nType", "Collected", "Time\nCollected",
    #      "Numb\nCont", "Container", "Preservative"]
    # ]
    data1 = []
    data2 = []

    tables = []

    row_height1 = [inch * 0.25, inch * 0.25, inch * 0.15, inch * 0.15, inch * 0.4, inch * 0.75, inch * 0.3, inch * 0.3,
                   inch * 0.2, inch * 0.2, inch * 0.2, inch * 0.2, inch * 0.2, inch * 0.2, inch * 0.2, inch * 0.2,
                   inch * 0.2, inch * 0.2, inch * 0.2, inch * 0.2, inch * 0.2, inch * 0.15, inch * 0.15, inch * 0.15,
                   inch * 0.15, inch * 0.15, inch * 0.15, inch * 0.15, inch * 0.15, inch * 0.15, inch * 0.15,
                   inch * 0.15, inch * 0.15, inch * 0.15]
    row_height2 = [inch * 0.3, inch * 0.3, inch * 0.2, inch * 0.3, inch * 0.3, inch * 0.3, inch * 0.3, inch * 0.3,
                   inch * 0.3, inch * 0.3, inch * 0.3, inch * 0.3, inch * 0.3, inch * 0.3, inch * 0.3, inch * 0.3,
                   inch * 0.4, inch * 2]
    row_width1 = [inch * 0.7, inch * 0.7, inch * 0.5, inch * 0.4, inch * 2.3, inch * 0.4, inch * 0.49, inch * 0.49,
                  inch * 0.49, inch * 0.49, inch * 0.49, inch * 0.49, inch * 0.49, inch * 1.2]
    row_width2 = [inch * 1.7, inch * 1.4, inch * 1.4, inch * 1.2, inch * 0.5, inch * 0.5, inch * 0.8, inch * 0.8,
                  inch * 0.68, inch * 0.65]
    page1_style = TableStyle([('FONT', (0, 0), (-1, -1), 'Helvetica', 7),
                              ('FONT', (0, 0), (4, 0), 'Helvetica-Bold', 9),
                              ('FONT', (0, 1), (4, 1), 'Helvetica-Bold', 8),
                              ('FONT', (5, 0), (-1, 3), 'Helvetica-Bold', 10),
                              ('TOPPADDING', (0, 2), (4, 6), 1),
                              ('TOPPADDING', (10, 21), (12, 21), 1),
                              ('LEFTPADDING', (0, 2), (4, 6), 1),
                              ('LEFTPADDING', (0, 7), (4, 7), 4),
                              ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                              ('ALIGN', (0, 0), (-1, 1), 'CENTER'),
                              ('ALIGN', (5, 4), (-1, 4), 'CENTER'),
                              ('ALIGN', (0, 20), (-1, 20), 'CENTER'),
                              ('ALIGN', (10, 21), (12, 21), 'CENTER'),
                              ('ALIGN', (12, 22), (12, -1), 'CENTER'),
                              ('ALIGN', (0, 25), (9, 27), 'CENTER'),
                              ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                              ('VALIGN', (0, 0), (4, 0), 'BOTTOM'),
                              ('VALIGN', (5, 0), (-1, 0), 'MIDDLE'),
                              ('VALIGN', (5, 4), (-1, 4), 'BOTTOM'),
                              ('VALIGN', (0, 7), (4, 7), 'BOTTOM'),
                              ('BOX', (0, 0), (4, 1), 0.25, colors.black),
                              ('BOX', (0, 2), (4, 3), 0.25, colors.black),
                              ('BOX', (5, 0), (-1, 3), 0.25, colors.black),
                              ('BOX', (0, 25), (9, -1), 0.25, colors.black),
                              ('BOX', (10, 20), (12, 21), 0.25, colors.black),
                              ('BOX', (10, 22), (12, -1), 0.25, colors.black),
                              ('BOX', (13, 20), (13, 21), 0.25, colors.black),
                              ('BOX', (13, 22), (13, -1), 0.25, colors.black),
                              ('GRID', (0, 4), (-1, 19), 0.25, colors.black),
                              ('GRID', (0, 20), (9, 24), 0.25, colors.black),
                              ('SPAN', (0, 0), (4, 0)),
                              ('SPAN', (0, 1), (4, 1)),
                              ('SPAN', (0, 2), (4, 2)),
                              ('SPAN', (0, 3), (3, 3)),
                              ('SPAN', (0, 4), (3, 4)),
                              ('SPAN', (0, 5), (3, 5)),
                              ('SPAN', (0, 6), (3, 6)),
                              ('SPAN', (5, 0), (-1, 3)),
                              ('SPAN', (5, 4), (5, 7)),
                              ('SPAN', (6, 4), (6, 7)),
                              ('SPAN', (7, 4), (7, 7)),
                              ('SPAN', (8, 4), (8, 7)),
                              ('SPAN', (9, 4), (9, 7)),
                              ('SPAN', (10, 4), (10, 7)),
                              ('SPAN', (11, 4), (11, 7)),
                              ('SPAN', (12, 4), (12, 7)),
                              ('SPAN', (13, 4), (13, 7)),
                              ('SPAN', (0, 20), (2, 20)),
                              ('SPAN', (3, 20), (4, 20)),
                              ('SPAN', (5, 20), (7, 20)),
                              ('SPAN', (8, 20), (9, 20)),
                              ('SPAN', (10, 20), (12, 20)),
                              ('SPAN', (13, 20), (13, 21)),
                              ('SPAN', (0, 21), (2, 22)),
                              ('SPAN', (3, 21), (4, 22)),
                              ('SPAN', (5, 21), (7, 22)),
                              ('SPAN', (8, 21), (9, 22)),
                              ('SPAN', (10, 21), (12, 21)),
                              ('SPAN', (0, 23), (2, 24)),
                              ('SPAN', (3, 23), (4, 24)),
                              ('SPAN', (5, 23), (7, 24)),
                              ('SPAN', (8, 23), (9, 24)),
                              ('SPAN', (10, 22), (11, 23)),
                              ('SPAN', (12, 22), (12, 23)),
                              ('SPAN', (10, 24), (11, 25)),
                              ('SPAN', (12, 24), (12, 25)),
                              ('SPAN', (10, 26), (11, 27)),
                              ('SPAN', (12, 26), (12, 27)),
                              ('SPAN', (10, 28), (11, 29)),
                              ('SPAN', (12, 28), (12, 29)),
                              ('SPAN', (10, 30), (11, 31)),
                              ('SPAN', (12, 30), (12, 31)),
                              ('SPAN', (10, 32), (11, 33)),
                              ('SPAN', (12, 32), (12, 33)),
                              ('SPAN', (0, 25), (9, 25)),
                              ('SPAN', (0, 26), (9, 27)),
                              ('SPAN', (0, 28), (9, -1)),
                              ])
    page2_style = TableStyle([('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
                              ('FONT', (0, 0), (3, 0), 'Helvetica-Bold', 9),
                              ('FONT', (0, 1), (3, 1), 'Helvetica-Bold', 8),
                              ('FONT', (4, 0), (-1, 1), 'Helvetica-Bold', 10),
                              ('FONT', (4, 2), (-1, 2), 'Helvetica-Bold', 8),
                              ('FONT', (0, 3), (-1, 3), 'Helvetica-Bold', 7),
                              ('FONT', (0, 16), (-1, -1), 'Helvetica-Bold', 7),
                              ('FONT', (0, 2), (3, 2), 'Helvetica', 7),
                              ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                              ('ALIGN', (0, 0), (-1, 1), 'CENTER'),
                              ('ALIGN', (4, 2), (-1, 2), 'CENTER'),
                              ('ALIGN', (8, 3), (-1, 3), 'CENTER'),
                              ('ALIGN', (0, 16), (-1, 16), 'CENTER'),
                              ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                              ('VALIGN', (4, 0), (-1, 1), 'MIDDLE'),
                              ('VALIGN', (0, 16), (-1, 16), 'MIDDLE'),
                              ('VALIGN', (0, 3), (-1, 3), 'BOTTOM'),
                              ('TOPPADDING', (0, 1), (3, 1), 1),
                              ('TOPPADDING', (0, -1), (-1, -1), 1),
                              ('BOTTOMPADDING', (0, 3), (-1, 3), 2),
                              ('LEFTPADDING', (0, 2), (-1, 3), 1),
                              ('LEFTPADDING', (4, 4), (5, 15), 3),
                              ('LEFTPADDING', (0, -1), (-1, -1), 1),
                              ('RIGHTPADDING', (4, 4), (5, 15), 3),
                              ('GRID', (0, 3), (3, -1), 0.25, colors.black),
                              ('GRID', (4, 0), (-1, -1), 0.25, colors.black),
                              ('BOX', (0, 0), (3, 1), 0.25, colors.black),
                              ('BOX', (0, 2), (3, 2), 0.25, colors.black),
                              ('SPAN', (0, 0), (3, 0)),
                              ('SPAN', (0, 1), (3, 1)),
                              ('SPAN', (0, 2), (1, 2)),
                              ('SPAN', (2, 2), (3, 2)),
                              ('SPAN', (4, 0), (-1, 1)),
                              ('SPAN', (4, 2), (-1, 2)),
                              ('SPAN', (8, 3), (9, 3)),
                              ('SPAN', (0, 16), (-1, 16)),
                              ('SPAN', (0, 17), (-1, 17)),
                              ])
    # edd_data = []
    for i in range(len(data)):
        sample_part = data[i]
        if sample_part[3] == '':
            continue
        # sample_tuple = (sample_part[0].lower(), sample_part[1].lower())
        collect = Paragraph("%s" % sample_part[0], tableStyle)
        s_type = Paragraph("%s" % sample_part[1], tableStyle)
        sample_id = Paragraph("%s" % sample_part[3], tableStyle)
        sodium = Paragraph("%s" % sample_part[4], tableStyle)
        chlorine = Paragraph("%s" % sample_part[5], tableStyle)
        ph = Paragraph("%s" % sample_part[6], tableStyle)
        temperature = Paragraph("%s" % sample_part[7], tableStyle)
        solids = Paragraph("%s" % sample_part[8], tableStyle)
        conduct = Paragraph("%s" % sample_part[9], tableStyle)
        salinity = Paragraph("%s" % sample_part[10], tableStyle)
        volume = Paragraph("%s" % sample_part[11], tableStyle)
        other = Paragraph("%s" % sample_part[12], tableStyle)
        start_read = Paragraph("%s" % sample_part[13], tableStyle)
        end_read = Paragraph("%s" % sample_part[14], tableStyle)
        flow_rate = Paragraph("%s" % sample_part[15], tableStyle)
        longitude = Paragraph("%s" % sample_part[-2], tableStyle)
        latitude = Paragraph("%s" % sample_part[-1], tableStyle)

        # Move this block to when the date is pulled from the csv [

        time_value = sample_part[2]
        coll_date = time_value.date()
        coll_time = time_value.time()
        d_time = Paragraph("%s" % coll_date, tableStyle)
        c_time = Paragraph("%s" % coll_time, tableStyle)

        if sample_part[16] != '':
            start_time_value = sample_part[16].time()
            s_time = Paragraph("%s" % start_time_value, tableStyle)
        else:
            s_time = Paragraph("", tableStyle)

        if sample_part[17] != '':
            end_time_value = sample_part[17].time()
            e_time = Paragraph("%s" % end_time_value, tableStyle)
        else:
            e_time = Paragraph("", tableStyle)

        data1.append(
            [d_time, c_time, volume, s_type, sample_id, collect, sodium, chlorine, ph, temperature, solids, conduct,
             salinity, ""])
        data2.append(
            [sample_id, latitude, longitude, other, s_time, e_time, start_read, end_read, flow_rate, ""])

        # if samp_type == sample_types[0]:
        #     edd_data.append(["", sample_part[1], "%s (%s)" % (sample_part[4], sample_part[0])])
        # elif samp_type == sample_types[1]:
        #     # add condition check for column locations
        #     edd_data.append(["%s (%s)" % (sample_part[4], sample_part[0]), lab_name,
        #                      "",  # ? Matrix
        #                      "", "", "%s %s" % (coll_date, coll_time), "", "", "", lab_name])
        if (i + 1) % 12 == 0:
            data1 = header1 + data1 + footer1
            data2 = header2 + data2 + footer2
            t1 = Table(data1,
                       colWidths=row_width1,
                       rowHeights=row_height1)
            t2 = Table(data2,
                       colWidths=row_width2,
                       rowHeights=row_height2)
            t1.setStyle(page1_style)
            t2.setStyle(page2_style)
            tables.append([t1])
            tables.append([t2])
            data1 = []
            data2 = []
    if len(data1) != 0:
        while len(data1) < 12:
            data1.append(["", "", "", "", "", "", "", "", "", "", "", "", "", ""])
            data2.append(["", "", "", "", "", "", "", "", "", ""])

        data1 = header1 + data1 + footer1
        data2 = header2 + data2 + footer2

        t1 = Table(data1,
                   colWidths=row_width1,
                   rowHeights=row_height1)
        t2 = Table(data2,
                   colWidths=row_width2,
                   rowHeights=row_height2)
        t1.setStyle(page1_style)
        t2.setStyle(page2_style)
        tables.append([t1])
        tables.append([t2])

    # row heights should be determined automatically, except for the first row
    # row_heights = len(data2) * [None]
    # row_heights[0] = (inch / 2) + 10
    # set table to include previous data, establishing any important column widths
    final_table = Table(tables,
                        splitByRow=True)
    # t2.setStyle(TableStyle([('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8),
    #                         ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
    #                         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    #                         ('ALIGN', (6, 0), (6, -1), 'RIGHT'),
    #                         ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    #                         ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
    #                         ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
    #                         ]))

    # put the table in a format the document will read
    text = [final_table, PageBreak()]

    # with open("%s/Generated Forms/%s_EDD.csv" % (curDir, new_name), 'w', newline='') as eddForm:
    #     writer = csv.writer(eddForm)
    #
    #     for row in edd_data:
    #         writer.writerow(row)

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

    def __init__(self, **kwargs):  # start the program and bind the 'X' button the exit_call function
        super(MainScreenWidget, self).__init__(**kwargs)
        Window.bind(on_request_close=self.exit_call)
        self.btn = self.ids.startpdf

    def clear(self):
        screen_label = self.ids.screen_label
        screen_label.text = ""

    @staticmethod
    def can_start():
        global data_collected
        if not data_collected:
            return False
        # elif location == '':
        #     return False
        return True

    @staticmethod
    def exit_call(*args):
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
            # screen_label.text = f"{BaseColors.WARNING}CSV or Location not provided, " \
            #                     f"please correct{BaseColors.ENDC}"
            screen_label.text = f"{BaseColors.WARNING}CSV not provided, please correct{BaseColors.ENDC}"
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
            # screen_label.text = f"{BaseColors.WARNING}CSV or Location not provided, " \
            #                     f"please correct{BaseColors.ENDC}"
            screen_label.text = f"{BaseColors.WARNING}CSV not provided, please correct{BaseColors.ENDC}"
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
        self.num_rows += 1
        new_row = RowWidget()
        new_row.main_screen = self

        new_row.ids.rownumber.text = str(self.num_rows)
        new_row.ids.samplefield.text = name
        btn = new_row.ids.buttonsection.children[0]
        btn.bind(on_release=self.remove_row)

        rows_section = self.ids.middlesection
        rows_section.height += 61
        rows_section.add_widget(new_row)

    # def choose_type(self):
    #     samp_type = ContaminantWidget()
    #     samp_type.main_window = self
    #     samp_type.contam_widget_popup = Popup(title="select a Sample Type", content=samp_type,
    #                                           size_hint=(None, None),
    #                                           size=(500, 150), auto_dismiss=False)
    #     samp_type.main_screen = self
    #     samp_type.contam_widget_popup.open()

    def start_pdf(self):
        global pdf_details, usedData, dataList, curData, lab_counts, pop_counts
        error_text = "CoC PDF cannot be made with zero samples selected\nPlease select samples then try again"
        lab_short = pdf_details[0][0]
        if len(curData) == 0:
            self.start_error(error_text)
            return False

        # Add popup for selecting sample type

        num = str(form_number())
        build_pdf(num, curData)
        count = lab_counts[lab_short] + len(curData)
        lab_counts[lab_short] = count
        for sample in curData:
            usedData.append(sample)
        curData.clear()
        self.store_used()
        rows_section = self.ids.middlesection
        rows_section.clear_widgets()
        rows_section.height = 0
        pdf_details.clear()
        for key in pop_counts.keys():
            pop_counts[key] = 0
        self.btn.pos = (-300, 10)
        self.num_rows = 0
        self.ids.screen_label.text = "Samples used: %d/%d\n" % (len(usedData), len(dataList))
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
                    if [sample[2], sample[3]] not in found:
                        found.append([sample[2], sample[3]])
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
        if [sample[2], sample[3]] in found:
            found.remove([sample[2], sample[3]])
        root.remove_widget(row)
        root.height -= 61
        self.num_rows -= 1

    def select_storage(self):
        global contact_num, contact_name
        storage_location = StorageWidget()
        storage_location.storage_popup = Popup(title="Select a storage location", content=storage_location,
                                               size_hint=(None, None),
                                               size=(500, 240), auto_dismiss=False)
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

    @staticmethod
    def start_error(text):
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

    @staticmethod
    def store_used():
        global curMemory, usedData, lab_counts
        temp_list = usedData.copy()
        temp_list.append(list(lab_counts.items()))
        with open(curMemory, "wb+") as mem_file:
            pickle.dump(temp_list, mem_file)

    @staticmethod
    def grab_used():
        global curMemory, usedData, found, lab_counts
        with open(curMemory, "rb") as mem_file:
            temp_list = pickle.load(mem_file)
        usedData = temp_list[:len(temp_list) - 1]
        for sample in usedData:
            found.append([sample[2], sample[3]])
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
        online_layer.ids.owner.text = gis_owner
        online_layer.ids.layer.text = gis_title
        online_layer.online_popup.open()


class ScreenWidget(ScrollView):
    pass


class RowWidget(StackLayout):
    main_screen = None


class ScanWidget(BoxLayout):
    main_window = None
    scan_widget_popup = None

    def start_scan(self):
        global pdf_details, labInfo
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
        global pdf_details, method_drop_btn, labInfo
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
            if match[0].lower() == type_samples or type_samples == "any":
                if match[3] == "":
                    continue
                elif [match[2], match[3]] in found:  # add duplication error/check
                    continue
                if bag_counts[match[3]] > 1:
                    warning_text = warning_text + "Sample %s is in the dataset %s times\n" % \
                                   (match[3], bag_counts[match[3]])
                temp_data.append(match)
                found.append([match[2], match[3]])
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

        for sample in temp_data:
            self.main_window.add_row(sample[3], 0)
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
        global dataList, bag_counts, contact_name, contact_num, contact, lab_counts, usedData, pop_counts
        screen_label = self.main_screen.ids.screen_label
        dataList = []  # need to reset pointers for pop, getting "all x found restarting search warning"
        bag_counts = {}
        usedData = []
        for key in pop_counts.keys():
            pop_counts[key] = 0
        for lab in lab_counts.keys():
            lab_counts[lab] = 0
        # location = self.ids.location.text
        contact_name = self.ids.contact_name.text
        contact_num = self.ids.contact_num.text
        contact = "%s; %s" % (contact_name, contact_num)
        return screen_label

    def get_csv_file(self):
        global dataList, data_collected, col_indexes, csv_headers, headers, csvTitle, bag_counts
        screen_label = self.store_data()
        filename = store(self.main_screen)
        if data_collected:  # from a csv, restructure this
            with open(filename, "r", encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                all_samples = list(reader)
            headers = all_samples[0]
            for col in headers:
                for index in range(len(csv_headers)):
                    if col.lower() == csv_headers[index]:
                        col_indexes[index] = headers.index(col)
                        break
            all_samples = all_samples[1:]
            for sample in all_samples:
                if sample[col_indexes[3]] == '':
                    continue
                if sample[col_indexes[3]] not in bag_counts.keys():
                    bag_counts[sample[col_indexes[3]]] = 0
                if ',' in sample[col_indexes[2]]:
                    temp_time = sample[col_indexes[2]].replace(',', '')
                    time_value = datetime.strptime(temp_time, "%m/%d/%Y %I:%M:%S %p")
                else:
                    temp_time = datetime.strptime(sample[col_indexes[2]], "%m/%d/%Y %I:%M:%S %p")
                    timezone = get_localzone()
                    time_value = temp_time.replace(tzinfo=pytz.utc).astimezone(timezone)
                if ',' in sample[col_indexes[16]]:
                    temp_time = sample[col_indexes[16]].replace(',', '')
                    start_value = datetime.strptime(temp_time, "%m/%d/%Y %I:%M:%S %p")
                elif sample[col_indexes[16]] != '':
                    temp_time = datetime.strptime(sample[col_indexes[16]], "%m/%d/%Y %I:%M:%S %p")
                    timezone = get_localzone()
                    start_value = temp_time.replace(tzinfo=pytz.utc).astimezone(timezone)
                else:
                    start_value = ''
                if ',' in sample[col_indexes[17]]:
                    temp_time = sample[col_indexes[17]].replace(',', '')
                    end_value = datetime.strptime(temp_time, "%m/%d/%Y %I:%M:%S %p")
                elif sample[col_indexes[17]] != '':
                    temp_time = datetime.strptime(sample[col_indexes[17]], "%m/%d/%Y %I:%M:%S %p")
                    timezone = get_localzone()
                    end_value = temp_time.replace(tzinfo=pytz.utc).astimezone(timezone)
                else:
                    end_value = ''
                new_sample = []
                for index in range(len(col_indexes)):
                    if index == 2:
                        new_sample.append(time_value)
                    elif index == 16:
                        new_sample.append(start_value)
                    elif index == 17:
                        new_sample.append(end_value)
                    else:
                        new_sample.append(sample[col_indexes[index]])
                new_sample.append(sample[-2])
                new_sample.append(sample[-1])
                dataList.append(new_sample)
                bag_counts[sample[col_indexes[3]]] += 1
            temp = filename.split('/')
            csvTitle = temp[-1].split('.')[0]
            screen_label.text = f"{BaseColors.OKGREEN}CSV Selected: {temp[-1]}{BaseColors.ENDC}\n" \
                                f"{len(dataList)}"
            self.storage_popup.dismiss()
            self.main_screen.get_memory()

    def get_online_layer(self):
        screen_label = self.store_data()  # do something to set the label
        self.main_screen.find_online(self, self.storage_popup)


class OnlineWidget(BoxLayout):
    online_popup = None
    main_screen = None
    popup_widget = None
    source_class = None

    def access_layer(self):
        global accessed_server, gis_owner, gis_title, epa_client_id, epa_url, oneepa_url, oneepa_client_id, \
            data_collected, dataList, bag_counts, usedData, lab_counts, csvTitle, gis_headers
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

        match accessed_server:
            case 0:
                url = epa_url
                client_id = epa_client_id
            case 1:
                url = oneepa_url
                client_id = oneepa_client_id
            case _:
                url = ""
                client_id = ""
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
        layers = first.layers
        initial = layers[0]
        features = initial.query(
            out_fields=gis_headers,
            out_sr=4326
        ).to_dict()['features']
        for i in range(len(features)):
            temp = features[i]['attributes']
            geometry = features[i]['geometry']
            if temp[gis_headers[3]] is None:
                continue
            if temp[gis_headers[3]] not in bag_counts.keys():
                bag_counts[temp[gis_headers[3]]] = 0
            collect = temp[gis_headers[2]] / 1000.0
            fixed_time = datetime.fromtimestamp(collect)
            temp_time = datetime.strptime(datetime.strftime(fixed_time, "%m/%d/%Y %I:%M:%S %p"), "%m/%d/%Y %I:%M:%S %p")

            if temp[gis_headers[16]] is not None:
                start = temp[gis_headers[16]] / 1000.0
                fixed_start = datetime.fromtimestamp(start)
                temp_start = datetime.strptime(datetime.strftime(fixed_start, "%m/%d/%Y %I:%M:%S %p"),
                                               "%m/%d/%Y %I:%M:%S %p")
            else:
                temp_start = ''

            if temp[gis_headers[17]] is not None:
                end = temp[gis_headers[17]] / 1000.0
                fixed_end = datetime.fromtimestamp(end)
                temp_end = datetime.strptime(datetime.strftime(fixed_end, "%m/%d/%Y %I:%M:%S %p"),
                                             "%m/%d/%Y %I:%M:%S %p")
            else:
                temp_end = ''
            new_sample = []
            for index in range(len(gis_headers)):
                if index == 2:
                    new_sample.append(temp_time)
                elif index == 16:
                    new_sample.append(temp_start)
                elif index == 17:
                    new_sample.append(temp_end)
                else:
                    if temp[gis_headers[index]] is None:
                        new_sample.append('')
                    else:
                        new_sample.append(temp[gis_headers[index]])
            new_sample.append(geometry['x'])
            new_sample.append(geometry['y'])
            dataList.append(new_sample)
            bag_counts[temp[gis_headers[3]]] += 1
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
        global dataList, data_collected, bag_counts, col_indexes, csv_headers, headers

        filename = store(self.main_screen)
        screen_label = self.main_screen.ids.screen_label
        # all_samples = []
        if data_collected:
            with open(filename, "r", encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                all_samples = list(reader)
            headers = all_samples[0]
            for col in headers:
                for index in range(len(csv_headers)):
                    if col.lower() == csv_headers[index]:
                        col_indexes[index] = headers.index(col)
                        break
            all_samples = all_samples[1:]
            for sample in all_samples:
                if sample[col_indexes[3]] == '':
                    continue
                else:
                    finder = filter(lambda a: sample[col_indexes[2]] in a, dataList)
                    existing = list(finder)
                    copies = []
                    for finding in existing:
                        if finding[col_indexes[2]] == sample[col_indexes[2]]:
                            copies.append(finding)
                            break
                    if len(copies) == 0:
                        if sample[col_indexes[3]] not in bag_counts.keys():
                            bag_counts[sample[col_indexes[2]]] = 0
                        if ',' in sample[col_indexes[2]]:
                            temp_time = sample[col_indexes[2]].replace(',', '')
                            time_value = datetime.strptime(temp_time, "%m/%d/%Y %I:%M:%S %p")
                        else:
                            temp_time = datetime.strptime(sample[col_indexes[2]], "%m/%d/%Y %I:%M:%S %p")
                            timezone = get_localzone()
                            time_value = temp_time.replace(tzinfo=pytz.utc).astimezone(timezone)
                        if ',' in sample[col_indexes[16]]:
                            temp_time = sample[col_indexes[16]].replace(',', '')
                            start_value = datetime.strptime(temp_time, "%m/%d/%Y %I:%M:%S %p")
                        elif sample[col_indexes[16]] != '':
                            temp_time = datetime.strptime(sample[col_indexes[16]], "%m/%d/%Y %I:%M:%S %p")
                            timezone = get_localzone()
                            start_value = temp_time.replace(tzinfo=pytz.utc).astimezone(timezone)
                        else:
                            start_value = ''
                        if ',' in sample[col_indexes[17]]:
                            temp_time = sample[col_indexes[17]].replace(',', '')
                            end_value = datetime.strptime(temp_time, "%m/%d/%Y %I:%M:%S %p")
                        elif sample[col_indexes[17]] != '':
                            temp_time = datetime.strptime(sample[col_indexes[17]], "%m/%d/%Y %I:%M:%S %p")
                            timezone = get_localzone()
                            end_value = temp_time.replace(tzinfo=pytz.utc).astimezone(timezone)
                        else:
                            end_value = ''
                        new_sample = []
                        for index in range(len(col_indexes)):
                            if index == 2:
                                new_sample.append(time_value)
                            elif index == 16:
                                new_sample.append(start_value)
                            elif index == 17:
                                new_sample.append(end_value)
                            else:
                                new_sample.append(sample[col_indexes[index]])
                        new_sample.append(sample[-2])
                        new_sample.append(sample[-1])
                        dataList.append(new_sample)
                        bag_counts[sample[col_indexes[3]]] += 1
            temp = filename.split('/')

            screen_label.text = f"{BaseColors.OKGREEN}CSV added: {temp[-1]}{BaseColors.ENDC}\n" \
                                f"{len(dataList)}"
            self.append_popup.dismiss()

    def add_gis(self):
        self.main_screen.find_online(self, self.append_popup)


class SettingWidget(BoxLayout):
    main_screen = None
    setup_popup = None

    @staticmethod
    def show_count():
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
        global contact_num, contact_name
        storage_location = StorageWidget()
        storage_location.storage_popup = Popup(title="Select a storage location", content=storage_location,
                                               size_hint=(None, None),
                                               size=(500, 240), auto_dismiss=True)
        storage_location.main_screen = self.main_screen
        # storage_location.ids.location.text = location
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


class AlterHeaderWidget(BoxLayout):
    header_popup = None

    def setup(self):
        global csv_headers
        self.ids.method.text = csv_headers[0]
        self.ids.type.text = csv_headers[1]
        self.ids.date.text = csv_headers[2]
        self.ids.bag_id.text = csv_headers[3]

    def finish(self):
        global csv_headers, col_indexes, dataList, data_collected, headers

        csv_headers[0] = self.ids.method.text
        csv_headers[1] = self.ids.type.text
        csv_headers[2] = self.ids.date.text
        csv_headers[3] = self.ids.bag_id.text

        if data_collected:
            for col in headers:
                for index in range(len(csv_headers)):
                    if col.lower() == csv_headers[index]:
                        col_indexes[index] = headers.index(col)
                        break


class MemoryWidget(BoxLayout):
    memory_popup = None
    main_screen = None

    @staticmethod
    def no_memory():
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


class COCPDFToolApp(App):
    main_screen = None

    def build(self):
        self.main_screen = MainScreenWidget()
        Window.size = (900, 650)
        return self.main_screen

    @staticmethod
    def get_labs():
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

    @staticmethod
    def set_populate_options():
        global containers, preservative, pop_counts, method_drop_btn, drop_menu_2
        collection_methods = ['G', 'C', 'UF']
        # sample_types = ["W", "SW", "GW", "DW", "WW", "PW", "SE", "SL", "OT"]
        for method in collection_methods:
            btn = Button(text='%s' % method, size_hint_y=None, height=30)
            btn.bind(on_release=lambda button: drop_menu_2.select(button.text))
            drop_menu_2.add_widget(btn)
            pop_counts[method.lower()] = 0
        pop_counts["any"] = 0
        btn = Button(text='Any', size_hint_y=None, height=30)
        btn.bind(on_release=lambda button: drop_menu_2.select(button.text))
        drop_menu_2.add_widget(btn)
        method_drop_btn.bind(on_release=drop_menu_2.open)
        drop_menu_2.bind(on_select=lambda instance, x: setattr(method_drop_btn, 'text', x))

    def on_start(self):
        self.get_labs()
        self.set_populate_options()
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
