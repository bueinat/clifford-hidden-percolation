# app.py
import streamlit as st
# מייבאים את הפונקציה המעודכנת מקובץ my_script
from my_script import perform_calculation_and_generate_plots
import streamlit.components.v1 as components # נחוץ להצגת SVG מתוך מחרוזת

import numpy as np
import wcore as core

# הגדרות כלליות לדף
st.set_page_config(
    page_title="אפליקציה עם גרפים ותהליך",
    layout="centered", # אפשרויות: "centered" או "wide"
    initial_sidebar_state="auto"
)

st.title("📊 אפליקציה קטנה: חישוב עם דוחות וגרפים")
st.markdown("""
ברוכים הבאים לאפליקציה!
בחרו את הפרמטרים `p` ו-`r` באמצעות המחוונים, לחצו על כפתור "הרץ/י חישוב"
וצפו ביומן התהליך ובגרפים שנוצרו.
""")

# 1. מחוונים (Sliders) וכפתור הרצה
st.header("⚙️ הגדרת פרמטרים")

# הגדרת ערכי ברירת מחדל למחוונים
default_p = 0.5
default_r = 0.2
default_N = 12

p_value = st.slider(
    "בחר/י ערך עבור p (פרמטר ראשון)",
    min_value=0.0,
    max_value=1.0,
    value=default_p,
    step=0.05,
    help="ערך זה ישפיע על קנה המידה של הגרפים."
)

r_value = st.slider(
    "בחר/י ערך עבור r (פרמטר שני)",
    min_value=0.0,
    max_value=1.0,
    value=default_r,
    step=0.05,
    help="ערך זה ישפיע גם הוא על צורת הגרפים, ומשמש לחלוקה."
)

N_value = st.slider(
    "בחר/י ערך עבור N (פרמטר שלישי)",
    min_value=8,
    max_value=80,
    value=default_N,
    step=4,
    help="ערך זה ישפיע גם הוא על צורת הגרפים, ומשמש לחלוקה."
)

# שימוש ב-st.cache_data כדי למנוע הרצה מחדש של החישוב והגרפים בכל פעם שנעשה שינוי לא רלוונטי
# הפונקציה תרוץ מחדש רק כאשר p_value או r_value משתנים
@st.cache_data
def run_and_cache_calculation(N, p, r):
    """
    עוטף את פונקציית החישוב כדי לאפשר Streamlit caching.
    """
    return perform_calculation_and_generate_plots(N, p, r)

# כפתור הרצה
# נשתמש ב-session_state כדי לאתחל את המצב של סלייד-שואו הגרפים
if 'current_plot_index' not in st.session_state:
    st.session_state.current_plot_index = 0
if 'all_svg_plots' not in st.session_state:
    st.session_state.all_svg_plots = []
if 'calculation_done' not in st.session_state:
    st.session_state.calculation_done = False
if 'calculation_logs' not in st.session_state:
    st.session_state.calculation_logs = ""
if 'final_calculated_result' not in st.session_state:
    st.session_state.final_calculated_result = None

if st.button("🚀 הרץ/י חישוב", type="primary"):
    # ויזואליזציה של תהליך
    with st.spinner('מבצע חישוב, מייצר יומן תהליך ויוצר גרפים...'):
        try:
            # בדיקה למניעת חלוקה באפס ב-r
            if abs(r_value) < 0.001: # אם r קרוב מאוד לאפס
                st.error("🚫 שגיאה: הפרמטר 'r' קרוב לאפס. אנא בחר/י ערך שונה מ-0 כדי למנוע חלוקה באפס.")
                st.session_state.calculation_done = False
            else:
                # הרצת החישוב דרך הפונקציה המכוסה ב-cache
                logs, svg_plots, final_result = run_and_cache_calculation(N_value, p_value, r_value)

                st.session_state.calculation_logs = logs
                st.session_state.all_svg_plots = svg_plots
                st.session_state.final_calculated_result = final_result
                st.session_state.current_plot_index = 0 # איפוס האינדקס לגרף הראשון לאחר חישוב חדש
                st.session_state.calculation_done = True

        except Exception as e:
            st.error(f"❌ אירעה שגיאה בלתי צפויה במהלך ההרצה: {e}")
            st.session_state.calculation_done = False

# הצגת תוצאות לאחר סיום החישוב
if st.session_state.calculation_done:
    # 2. חלון המציג את פלט תהליך החישוב (print statements)
    st.subheader("📝 יומן תהליך החישוב:")
    st.code(st.session_state.calculation_logs, language='text') # הצגת הפלטים כקוד טקסט רגיל

    if st.session_state.final_calculated_result is not None and not np.isnan(st.session_state.final_calculated_result):
        st.success(f"✅ החישוב הסתיים בהצלחה! התוצאה הסופית שחושבה היא: **{st.session_state.final_calculated_result:.2f}**")
    else:
        st.error("⚠️ החישוב הסתיים עם תוצאה לא חוקית (ייתכן בגלל שגיאה פנימית).")
    
    # 3. סלייד-שואו של תמונות SVG כתוצאה מהחישוב
    if st.session_state.all_svg_plots:
        st.subheader("📈 גרפים כתוצאה מהחישוב:")
        num_svgs = len(st.session_state.all_svg_plots)
        
        # פונקציות לניווט בין הגרפים
        def next_plot():
            if st.session_state.current_plot_index < num_svgs - 1:
                st.session_state.current_plot_index += 1

        def prev_plot():
            if st.session_state.current_plot_index > 0:
                st.session_state.current_plot_index -= 1
        
        # יצירת כפתורי הניווט
        col1, col2, col3 = st.columns([1, 2, 1]) # כדי למרכז את הכפתורים
        with col1:
            if st.button("⬅️ קודם", on_click=prev_plot, disabled=(st.session_state.current_plot_index == 0)):
                pass # הפעולה מתרחשת ב-on_click
        with col3:
            if st.button("הבא ➡️", on_click=next_plot, disabled=(st.session_state.current_plot_index == num_svgs - 1)):
                pass # הפעולה מתרחשת ב-on_click
        
        # הצגת אינדקס הגרף הנוכחי
        st.info(f"מציג גרף {st.session_state.current_plot_index + 1} מתוך {num_svgs}")
        
        html_content = f"""
        <div style="background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: flex; justify-content: center; align-items: center;">
            {st.session_state.all_svg_plots[st.session_state.current_plot_index]}
        </div>
        """

        # הצגת ה-SVG הנבחר באמצעות st.components.v1.html
        # זה מאפשר להציג מחרוזות HTML/SVG גולמיות
        components.html(
            html_content,
            height=500, # גובה קבוע לאזור הגרף
            scrolling=False # מונע גלילה בתוך אזור ה-HTML
        )
    else:
        st.info("ℹ️ לא נוצרו גרפים בחישוב זה.")

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.9em;">
  אפליקציה זו פותחה באמצעות Streamlit Python.
  <br>
  ניתן למצוא את קוד המקור ב-GitHub (קישור יתווסף לאחר פריסה).
</div>
""", unsafe_allow_html=True)


# # הגדרות כלליות לדף
# st.set_page_config(
#     page_title="אפליקציה עם גרפים ותהליך",
#     layout="centered", # אפשרויות: "centered" או "wide"
#     initial_sidebar_state="auto"
# )

# st.title("📊 אפליקציה קטנה: חישוב עם דוחות וגרפים")
# st.markdown("""
# ברוכים הבאים לאפליקציה!
# בחרו את הפרמטרים `p` ו-`r` באמצעות המחוונים, לחצו על כפתור "הרץ/י חישוב"
# וצפו ביומן התהליך ובגרפים שנוצרו.
# """)

# # 1. מחוונים (Sliders) וכפתור הרצה
# st.header("⚙️ הגדרת פרמטרים")

# # הגדרת ערכי ברירת מחדל למחוונים
# default_p = 5.0
# default_r = 2.0

# p_value = st.slider(
#     "בחר/י ערך עבור p (פרמטר ראשון)",
#     min_value=0.1,
#     max_value=10.0,
#     value=default_p,
#     step=0.1,
#     help="ערך זה ישפיע על קנה המידה של הגרפים."
# )

# r_value = st.slider(
#     "בחר/י ערך עבור r (פרמטר שני)",
#     min_value=0.1,
#     max_value=10.0,
#     value=default_r,
#     step=0.1,
#     help="ערך זה ישפיע גם הוא על צורת הגרפים, ומשמש לחלוקה."
# )

# # שימוש ב-st.cache_data כדי למנוע הרצה מחדש של החישוב והגרפים בכל פעם שנעשה שינוי לא רלוונטי
# # הפונקציה תרוץ מחדש רק כאשר p_value או r_value משתנים
# @st.cache_data
# def run_and_cache_calculation(p, r):
#     """
#     עוטף את פונקציית החישוב כדי לאפשר Streamlit caching.
#     """
#     return perform_calculation_and_generate_plots(p, r)

# # כפתור הרצה
# if st.button("🚀 הרץ/י חישוב", type="primary"):
#     # ויזואליזציה של תהליך
#     with st.spinner('מבצע חישוב, מייצר יומן תהליך ויוצר גרפים...'):
#         try:
#             # בדיקה למניעת חלוקה באפס ב-r
#             if abs(r_value) < 0.001: # אם r קרוב מאוד לאפס
#                 st.error("🚫 שגיאה: הפרמטר 'r' קרוב לאפס. אנא בחר/י ערך שונה מ-0 כדי למנוע חלוקה באפס.")
#             else:
#                 # הרצת החישוב דרך הפונקציה המכוסה ב-cache
#                 logs, svg_plots, final_result = run_and_cache_calculation(p_value, r_value)

#                 # 2. חלון המציג את פלט תהליך החישוב (print statements)
#                 st.subheader("📝 יומן תהליך החישוב:")
#                 st.code(logs, language='text') # הצגת הפלטים כקוד טקסט רגיל

#                 st.success(f"✅ החישוב הסתיים בהצלחה! התוצאה הסופית שחושבה היא: **{final_result:.2f}**")
                
#                 # 3. סלייד-שואו של תמונות SVG כתוצאה מהחישוב
#                 if svg_plots:
#                     st.subheader("📈 גרפים כתוצאה מהחישוב:")
#                     num_svgs = len(svg_plots)
                    
#                     # סליידר לבחירת הגרף המוצג
#                     plot_index = st.slider(
#                         "בחר/י גרף לצפייה",
#                         min_value=0,
#                         max_value=num_svgs - 1,
#                         value=0, # גרף ראשון כברירת מחדל
#                         step=1,
#                         # format_func=lambda x: f"גרף {x+1} מתוך {num_svgs}" # תצוגה ידידותית
#                     )
                    
#                     # הצגת ה-SVG הנבחר באמצעות st.components.v1.html
#                     # זה מאפשר להציג מחרוזות HTML/SVG גולמיות
#                     components.html(
#                         svg_plots[plot_index],
#                         height=500, # גובה קבוע לאזור הגרף
#                         scrolling=False # מונע גלילה בתוך אזור ה-HTML
#                     )
#                     st.info(f"הגרף המוצג כרגע הוא גרף מספר {plot_index + 1}.")
#                 else:
#                     st.info("ℹ️ לא נוצרו גרפים בחישוב זה.")

#         except Exception as e:
#             st.error(f"❌ אירעה שגיאה בלתי צפויה במהלך ההרצה: {e}")

# st.markdown("---")
# st.markdown("""
# <div style="text-align: center; color: #888; font-size: 0.9em;">
#   אפליקציה זו פותחה באמצעות Streamlit Python.
#   <br>
#   ניתן למצוא את קוד המקור ב-GitHub (קישור יתווסף לאחר פריסה).
# </div>
# """, unsafe_allow_html=True)


# # def calculate_result(p, r):
# #     print(f"p + r = {float(p) + float(r)}")
# #     return p + r

# st.title("אפליקציה קטנה עם בחירת פרמטרים")
# st.write("בחר/י את הפרמטרים p ו-r כדי להריץ את החישוב.")

# # יצירת מחוונים (sliders) לבחירת פרמטרים
# p_value = st.slider("בחר/י ערך עבור p", min_value=0.0, max_value=1.0, value=0.5, step=0.05)
# r_value = st.slider("בחר/י ערך עבור r", min_value=0.0, max_value=1.0, value=0.1, step=0.05)
# N_value = st.slider("בחר/י ערך עבור N", min_value=8, max_value=80, value=12, step=4)

# # כפתור להרצת הקוד
# if st.button("הרץ/י חישוב"):
#     # הרצת פונקציית הפייתון עם הפרמטרים שנבחרו
#     try:
#         result = calculate_result(N_value, p_value, r_value)
#         st.success(f"החישוב הסתיים בהצלחה! התוצאה היא: {result:.2f}")
#     except ZeroDivisionError:
#         st.error("שגיאה: לא ניתן לחלק באפס! ודא/י ש-r אינו 0.")
#     except Exception as e:
#         st.error(f"אירעה שגיאה: {e}")

# # ניתן להוסיף כאן גם גרפים, טבלאות ועוד תוצאות.
# st.subheader("אודות האפליקציה")
# st.info("אפליקציה זו מדגימה כיצד ניתן ליצור ממשק פשוט להרצת קוד פייתון עם פרמטרים מוגדרים מראש.")

