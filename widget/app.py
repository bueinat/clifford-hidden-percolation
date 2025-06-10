# app.py
import streamlit as st
from my_script import calculate_result # מייבאים את הפונקציה מהקובץ הקודם
import wcore as core

# def calculate_result(p, r):
#     print(f"p + r = {float(p) + float(r)}")
#     return p + r

st.title("אפליקציה קטנה עם בחירת פרמטרים")
st.write("בחר/י את הפרמטרים p ו-r כדי להריץ את החישוב.")

# יצירת מחוונים (sliders) לבחירת פרמטרים
p_value = st.slider("בחר/י ערך עבור p", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
r_value = st.slider("בחר/י ערך עבור r", min_value=0.0, max_value=1.0, value=0.1, step=0.05)
N_value = st.slider("בחר/י ערך עבור N", min_value=8, max_value=80, value=12, step=4)

# כפתור להרצת הקוד
if st.button("הרץ/י חישוב"):
    # הרצת פונקציית הפייתון עם הפרמטרים שנבחרו
    try:
        result = calculate_result(N_value, p_value, r_value)
        st.success(f"החישוב הסתיים בהצלחה! התוצאה היא: {result:.2f}")
    except ZeroDivisionError:
        st.error("שגיאה: לא ניתן לחלק באפס! ודא/י ש-r אינו 0.")
    except Exception as e:
        st.error(f"אירעה שגיאה: {e}")

# ניתן להוסיף כאן גם גרפים, טבלאות ועוד תוצאות.
st.subheader("אודות האפליקציה")
st.info("אפליקציה זו מדגימה כיצד ניתן ליצור ממשק פשוט להרצת קוד פייתון עם פרמטרים מוגדרים מראש.")