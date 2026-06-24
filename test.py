import pandas as pd

df = pd.read_excel("data.xlsx")

print(
    df[df["Section"]==11][
        ["Date","Section","Lab","Exam Code"]
    ].tail(20)
)
