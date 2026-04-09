"""
فاکتور ساز حرفه‌ای - Consulenze immobiliari
طراحی طبق فرمت اصلی شرکت
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime

def number_to_italian_words(num):
    """تبدیل عدد به حروف ایتالیایی"""
    ones = ["", "uno", "due", "tre", "quattro", "cinque", "sei", "sette", "otto", "nove"]
    tens = ["", "dieci", "venti", "trenta", "quaranta", "cinquanta", "sessanta", "settanta", "ottanta", "novanta"]
    teens = ["dieci", "undici", "dodici", "tredici", "quattordici", "quindici", "sedici", "diciassette", "diciotto", "diciannove"]
    hundreds = ["", "cento", "duecento", "trecento", "quattrocento", "cinquecento", "seicento", "settecento", "ottocento", "novecento"]
    
    if num == 0:
        return "zero"
    
    num = int(num)
    
    if num < 10:
        return ones[num]
    elif num < 20:
        return teens[num - 10]
    elif num < 100:
        t = num // 10
        o = num % 10
        return tens[t] + ones[o]
    elif num < 1000:
        h = num // 100
        rest = num % 100
        if rest == 0:
            return hundreds[h]
        elif rest < 10:
            return hundreds[h] + ones[rest]
        elif rest < 20:
            return hundreds[h] + teens[rest - 10]
        else:
            t = rest // 10
            o = rest % 10
            return hundreds[h] + tens[t] + ones[o]
    else:
        thousands = num // 1000
        rest = num % 1000
        if thousands == 1:
            thou_word = "mille"
        else:
            thou_word = number_to_italian_words(thousands) + "mila"
        
        if rest == 0:
            return thou_word
        else:
            return thou_word + number_to_italian_words(rest)

def generate_luxury_invoice_pdf(invoice_data):
    """
    ساخت فاکتور لوکس
    
    invoice_data = {
        'invoice_number': '6031101',
        'date': '30/03/2026',
        'time': '16:44',
        'recipient_name': 'Ranjbarian Nastaran',
        'amount': 400.00,
        'description': 'Affitto di mese Marzo',
        'currency': '€'
    }
    """
    
    buffer = BytesIO()
    
    # ایجاد PDF با اندازه A4
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # پس‌زمینه کرم/بژ
    c.setFillColor(colors.HexColor('#FDF6E3'))
    c.rect(0, 0, width, height, fill=1, stroke=0)
    
    # === لوگو و هدر شرکت ===
    
    # لوگو خونه قرمز (ساده)
    logo_x = width / 2
    logo_y = height - 80
    
    # رسم خونه
    c.setFillColor(colors.HexColor('#9F1239'))
    c.setStrokeColor(colors.HexColor('#9F1239'))
    c.setLineWidth(2)
    
    # سقف مثلثی
    house_path = c.beginPath()
    house_path.moveTo(logo_x, logo_y + 20)  # بالای سقف
    house_path.lineTo(logo_x - 25, logo_y)  # گوشه چپ
    house_path.lineTo(logo_x + 25, logo_y)  # گوشه راست
    house_path.close()
    c.drawPath(house_path, fill=1, stroke=1)
    
    # بدنه خونه
    c.rect(logo_x - 20, logo_y - 30, 40, 30, fill=1, stroke=1)
    
    # در
    c.setFillColor(colors.white)
    c.rect(logo_x - 8, logo_y - 30, 16, 20, fill=1, stroke=0)
    
    # خط قرمز کنار
    c.setStrokeColor(colors.HexColor('#DC2626'))
    c.setLineWidth(3)
    c.line(logo_x + 30, logo_y + 10, logo_x + 45, logo_y + 10)
    
    # نام شرکت (فونت cursive شبیه‌ساز)
    c.setFillColor(colors.HexColor('#9F1239'))
    c.setFont('Helvetica-BoldOblique', 20)
    company_name = "Consulenze immobiliari"
    c.drawCentredString(width / 2, logo_y - 50, company_name)
    
    # خدمات
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#4B5563'))
    c.drawCentredString(width / 2, logo_y - 65, "AFFITTA  COMPRA  VENDE  RISTRUTTURA")
    
    # دسته‌بندی
    c.setFont('Helvetica-Bold', 9)
    c.drawCentredString(width / 2, logo_y - 78, "APPARTAMENTI")
    
    # آدرس
    c.setFont('Helvetica', 8)
    c.drawCentredString(width / 2, logo_y - 91, "VIA VIGONOVESE 114")
    
    # === محتوای فاکتور ===
    
    content_y = logo_y - 130
    
    # دریافت‌کننده
    c.setFont('Helvetica-Bold', 12)
    c.setFillColor(colors.black)
    c.drawString(100, content_y, f"Ricevuto da {invoice_data['recipient_name']}")
    
    # مبلغ به حروف
    content_y -= 30
    amount_words = number_to_italian_words(int(invoice_data['amount']))
    cents = int((invoice_data['amount'] - int(invoice_data['amount'])) * 100)
    
    c.setFont('Helvetica', 14)
    c.drawString(100, content_y, f"{invoice_data['currency']} {amount_words}/{cents:02d} euro")
    
    # توضیحات
    content_y -= 35
    c.setFont('Helvetica', 11)
    amount_in_parens = f"{int(invoice_data['amount'])} ({amount_words} euro)"
    c.drawString(100, content_y, f"Per {invoice_data['description']} ({amount_in_parens}{invoice_data['currency']})")
    
    # === جزئیات فاکتور در باکس ===
    
    box_y = content_y - 60
    
    # باکس پس‌زمینه
    c.setFillColor(colors.HexColor('#F5F5DC'))
    c.setStrokeColor(colors.HexColor('#9F1239'))
    c.setLineWidth(1.5)
    c.roundRect(80, box_y - 70, width - 160, 65, 8, fill=1, stroke=1)
    
    # محتوای باکس
    c.setFillColor(colors.black)
    c.setFont('Helvetica-Bold', 10)
    
    detail_y = box_y - 20
    c.drawString(100, detail_y, f"RICEVUTA n. {invoice_data['invoice_number']}")
    
    detail_y -= 20
    c.drawString(100, detail_y, f"data {invoice_data['date']} ore {invoice_data['time']}")
    
    detail_y -= 20
    c.drawString(100, detail_y, f"importo {invoice_data['amount']:.2f}")
    
    # === فوتر ===
    
    c.setFont('Helvetica', 7)
    c.setFillColor(colors.HexColor('#6B7280'))
    footer_text = "Consulenze immobiliari - Via Vigonovese 114"
    c.drawCentredString(width / 2, 50, footer_text)
    
    c.save()
    buffer.seek(0)
    return buffer
