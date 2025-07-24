from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

c = canvas.Canvas("teste.pdf", pagesize=A4)
c.drawString(100, 750, "Teste de ReportLab funcionando")
c.save()
