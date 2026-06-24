from flask import Flask, render_template, request, redirect, session, send_file
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape
import tempfile

app = Flask(__name__)
app.secret_key = "CHANGE_ME"

EXCEL_FILE = "data.xlsx"

ACCESS_CODES = {
    "LAB2026": True
}

def clean_sections(df):
    df["Section"] = pd.to_numeric(df["Section"], errors="coerce")
    df = df.dropna(subset=["Section"])
    df["Section"] = df["Section"].astype(int).astype(str)
    return df

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        code = request.form["code"]
        if code in ACCESS_CODES:
            session["logged_in"] = True
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect("/")

    df = pd.read_excel(EXCEL_FILE)
    df = clean_sections(df)

    sections = sorted(df["Section"].unique())
    return render_template("dashboard.html", sections=sections)

@app.route("/dates/<section>")
def dates(section):
    df = pd.read_excel(EXCEL_FILE)
    df = clean_sections(df)

    dates = sorted(
        df[df["Section"] == str(section)]["Date"]
        .astype(str)
        .unique()
        .tolist()
    )

    return {"dates": dates}

def build_pdf(records, filename):
    records = sorted(records, key=lambda x: str(x["Lab"]))

    if len(records) == 1:
        cards = records * 12
    elif len(records) == 2:
        cards = [records[0]] * 6 + [records[1]] * 6
    else:
        cards = records[:12]

    style = ParagraphStyle("Card", alignment=1, leading=22)
    cells = []

    for r in cards:
        section = int(float(r["Section"]))

        txt = f"""
        <para align="center">
        <font size="16"><b>SECTION {section}</b></font>
        <br/><br/>
        <font size="16">{r['Date']}</font>
        <br/><br/>
        <font size="20"><b> {r['Lab']} &nbsp;&nbsp; {r['Exam Code']}</b></font>
        </para>
        """

        cells.append(Paragraph(txt, style))

    grid = [cells[i:i+3] for i in range(0, 12, 3)]

    doc = SimpleDocTemplate(
        filename,
        pagesize=landscape(A4),
        leftMargin=10,
        rightMargin=10,
        topMargin=10,
        bottomMargin=10
    )

    table = Table(grid, colWidths=260, rowHeights=130)

    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))

    doc.build([table])

@app.route("/generate", methods=["POST"])
def generate():
    section = request.form["section"]
    date = request.form["date"]

    df = pd.read_excel(EXCEL_FILE)
    df = clean_sections(df)

    rows = df[
        (df["Section"] == str(section))
        &
        (df["Date"].astype(str) == str(date))
    ]

    records = rows[["Date", "Section", "Lab", "Exam Code"]].to_dict("records")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()

    build_pdf(records, tmp.name)

    return send_file(
        tmp.name,
        as_attachment=True,
        download_name=f"Section_{section}.pdf"
    )

if __name__ == "__main__":
    app.run(debug=True)
