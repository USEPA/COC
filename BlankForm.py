from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import BaseDocTemplate, Table, TableStyle, Paragraph, Frame, PageTemplate, PageBreak


########################################################################
# custom Canvas class to create the "Page x of y" header


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


########################################################################

styles = getSampleStyleSheet()
style = styles['Normal']
# create custom styles for the table to use for the Paragraphs
tableStyle = ParagraphStyle('Table Body',
                            fontName="Helvetica",
                            fontSize=8,
                            parent=styles['Normal'],
                            alignment=0,  # Left
                            spaceAfter=10)
leftTable = ParagraphStyle('Left Table Body',
                           fontName="Helvetica",
                           fontSize=8,
                           parent=styles['Normal'],
                           alignment=2,  # Right
                           spaceAfter=10)

# set the header information to editable formats
location = ""
labContact = ""
labLocation = "                              "
labPhone = "                              "
cooler = "                              "
formNumber = "                        "
conPhone = ""

# start the document
doc = BaseDocTemplate("./Blank_CoC_Form.pdf",
                      pagesize=(11 * inch, 8.5 * inch),
                      rightMargin=50,
                      leftMargin=50,
                      topMargin=10,
                      bottomMargin=63)


# create the function for writing all of the header information on every page
def head(canvas, docum):
    canvas.saveState()
    # canvas.setFont('Times-Roman', 9)
    # canvas.drawString(doc.leftMargin, doc.height+30, "Page %d" % doc.page)
    canvas.setFont('Helvetica-Bold', 8)
    h = docum.height + 13
    canvas.drawString(docum.leftMargin + 4, h, "USEPA")
    canvas.drawCentredString((docum.width + 90) / 2, h, "CHAIN OF CUSTODY RECORD")
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawRightString(docum.width + 40, h, "No: %s" % formNumber)
    canvas.setFont('Helvetica', 8)
    h = h - 13
    canvas.drawString(docum.leftMargin + 4, h, "DateShipped: ")
    canvas.drawCentredString((docum.width + 90) / 2, h, location)
    canvas.drawRightString(docum.width + 40, h, "Cooler #: %s" % cooler)
    h = h - 13
    canvas.drawString(docum.leftMargin + 4, h, "CarrierName: ")
    canvas.drawCentredString((docum.width + 90) / 2, h, "Lab Contact: %s" % labContact)
    canvas.drawRightString(docum.width + 40, h, "Lab: %s" % labLocation)
    h = h - 13
    canvas.drawString(docum.leftMargin + 4, h, "AirbillNo: ")
    canvas.drawCentredString((docum.width + 90) / 2, h, "Contact Phone: %s" % conPhone)
    canvas.drawRightString(docum.width + 40, h, "Lab Phone: %s" % labPhone)
    canvas.restoreState()


# create the function for drawing the lower 2 tables that don't get automatically filled in
def mid(canvas, docum):
    canvas.saveState()
    midy = (inch * 3) + 17
    canvas.setFont('Helvetica-Bold', 8)
    canvas.drawString((inch * 8) + 37, midy, "HAZMAT #")
    canvas.setFont('Helvetica', 8)
    canvas.drawString(inch - 18, midy, "Special Instructions:")
    midy = midy - 37
    canvas.drawString(inch - 13, midy, "Items/Reason        Relinquished by (Signature and Organization)            "
                                       "Date/Time              Received by (Signature and Organization)               "
                                       "Date/Time         Sample Condition Upon Receipt")
    canvas.rect(inch - 22, midy + 20, docum.width, (inch / 2) + 3, fill=0)
    canvas.line(8.4 * inch, midy + 20, 8.4 * inch, midy + 23 + (inch / 2))
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


y = doc.bottomMargin + (doc.height / 4) + 65

# build the frame that the table will fit in
frame3 = Frame(doc.leftMargin,
               y,
               doc.width,
               (doc.height / 2) - 35,
               leftPadding=0,
               bottomPadding=0,
               rightPadding=0,
               topPadding=0,
               id='top')

# create the Page Template that will be used, adding the frame and functions to it
template = PageTemplate(id='main', frames=[frame3], onPage=all_write)
doc.addPageTemplates([template])

# sample information from example PDF
data2 = [
    ["Lab#", "Sample #", "Collection Method", "Sample\nType", "Collected", "Time\nCollected",
     "Numb\nCont", "Container", "Preservative"]]
pageCount = 20
for i in range(6 * pageCount):
    # text_hold = Paragraph("\n1\n1", tableStyle)
    data2.append(["", "", "", "", "", "", "", "", ""])

# row heights should be determined automatically, except for the first row
rowHeights = len(data2) * [inch / 2 - 6]
rowHeights[0] = (inch / 2) + 10
# set table to include previous data, establishing any important column widths
t2 = Table(data2,
           colWidths=[inch, inch, (3 * inch / 2) + 11, inch + 11, inch - 10, inch - 10, inch / 2, (3 * inch / 2) - 5, inch + 12],
           rowHeights=rowHeights,
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

# build the documant
doc.build(text, canvasmaker=PageNumCanvas)
