# app.py
import streamlit as st
from back_code import perform_calculation_and_generate_plots
import streamlit.components.v1 as components # נחוץ להצגת SVG מתוך מחרוזת

# הגדרות כלליות לדף
st.set_page_config(
    page_title="ZX Simplification Demonstration",
    layout="centered", # אפשרויות: "centered" או "wide"
    initial_sidebar_state="auto"
)

st.title("ZX Simplification Demonstration App")
st.markdown("""
This is a small application where you can see the simplification process of random circuits generated according to the model defined in [this paper](https://arxiv.org/abs/2502.13211), according to the chosen parameters. 
""")

# 1. מחוונים (Sliders) וכפתור הרצה
st.header("⚙️ Set Parameters")

# הגדרת ערכי ברירת מחדל למחוונים
default_p = 0.5
default_r = 0.2
default_N = 12

p_value = st.slider(
    "p",
    min_value=0.0,
    max_value=1.0,
    value=default_p,
    step=0.05,
    help="measurement probability"
)

r_value = st.slider(
    "r",
    min_value=0.0,
    max_value=1.0,
    value=default_r,
    step=0.05,
    help="cnot probability"
)

N_value = st.slider(
    "N",
    min_value=8,
    max_value=80,
    value=default_N,
    step=4,
    help="number of qubits. note this highly affects run time"
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
if 'zoom_level' not in st.session_state:
    st.session_state.zoom_level = 1.0 # רמת זום התחלתית (1.0 = 100%)
if 'x_offset' not in st.session_state:
    st.session_state.x_offset = 0 # מיקום אופקי התחלתי (0 = מרכז)
if 'y_offset' not in st.session_state:
    st.session_state.y_offset = 0 # מיקום אנכי התחלתי (0 = מרכז)
    
# פונקציות לטיפול בזום
def zoom_in():
    st.session_state.zoom_level = min(st.session_state.zoom_level + 0.1, 2.0) # מקסימום זום 200%

def zoom_out():
    st.session_state.zoom_level = max(st.session_state.zoom_level - 0.1, 0.5) # מינימום זום 50%

if st.button("🚀 Run", type="primary"):
    # ויזואליזציה של תהליך
    with st.spinner('Generating circuit, simplifying, and creating plots'):
        try:
            logs, svg_plots, svg_names, final_result = run_and_cache_calculation(N_value, p_value, r_value)

            st.session_state.calculation_logs = logs
            st.session_state.all_svg_plots = svg_plots
            st.session_state.all_svg_names = svg_names
            st.session_state.final_calculated_result = final_result
            st.session_state.current_plot_index = 0 # איפוס האינדקס לגרף הראשון לאחר חישוב חדש
            st.session_state.calculation_done = True

        except Exception as e:
            st.error(f"❌ During the run, unexpected error occured {e}")
            st.session_state.calculation_done = False

# הצגת תוצאות לאחר סיום החישוב
if st.session_state.calculation_done:
    st.success(f"✅ The simplification was successful! now presenting the simplification steps below")

    # 3. סלייד-שואו של תמונות SVG כתוצאה מהחישוב
    if st.session_state.all_svg_plots:
        st.subheader("📈 Simplification Steps Plots")
        num_svgs = len(st.session_state.all_svg_plots)
        
    # פונקציות לניווט בין הגרפים
        def next_plot():
            if st.session_state.current_plot_index < num_svgs - 1:
                st.session_state.current_plot_index += 1

        def prev_plot():
            if st.session_state.current_plot_index > 0:
                st.session_state.current_plot_index -= 1
    
        # יצירת כפתורי הניווט
        # יצירת כפתורי הניווט והזום בשורה אחת
        col_prev, col_zoom_in, col_zoom_out, col_next = st.columns([1, 1, 1, 1])
        
        with col_prev:
            st.button("⬅️ Previous", on_click=prev_plot, disabled=(st.session_state.current_plot_index == 0))
        with col_zoom_in:
            st.button("➕ Zoom In", on_click=zoom_in, disabled=(st.session_state.zoom_level >= 2.0))
        with col_zoom_out:
            st.button("➖ Zoom Out", on_click=zoom_out, disabled=(st.session_state.zoom_level <= 0.5))
        with col_next:
            st.button("Next ➡️", on_click=next_plot, disabled=(st.session_state.current_plot_index == num_svgs - 1))
        

        # מחווני היסט (Panning)
        st.write("---") # קו מפריד
        st.markdown("**Graph Panning Controls**")
        col_offset_x, col_offset_y = st.columns(2)
        with col_offset_x:
            st.session_state.x_offset = st.slider(
                "Horzontal Offset (X)",
                min_value=-200, # טווח היסט במרחק פיקסלים
                max_value=200,
                value=st.session_state.x_offset,
                step=10,
                key="x_offset_slider", # מזהה ייחודי למחוון
                help="drag the plot display left / right"
            )
        with col_offset_y:
            st.session_state.y_offset = st.slider(
                "Vertical Offset (Y)",
                min_value=-200,
                max_value=200,
                value=st.session_state.y_offset,
                step=10,
                key="y_offset_slider", # מזהה ייחודי למחוון
                help="drag the plot display upt / down"
            )
                

                
        # --- עטיפת ה-SVG עם רקע לבן, פונקציונליות זום והיסט ---
        current_svg_content = st.session_state.all_svg_plots[st.session_state.current_plot_index]
        current_svg_name = st.session_state.all_svg_names[st.session_state.current_plot_index]
        current_zoom_level = st.session_state.zoom_level
        current_x_offset = st.session_state.x_offset
        current_y_offset = st.session_state.y_offset
        
        # הצגת אינדקס הגרף הנוכחי
        st.info(f"{current_svg_name.split('_')[-1]} rule {st.session_state.current_plot_index + 1} out of {num_svgs} total rules")
        # הסגנון 'transform' מאפשר לשלב 'scale' ו-'translate'
        # חשוב שה-translate יבוא אחרי ה-scale כדי להזיז את התוכן *לאחר* שהוגדל.
        # כדי להבטיח ביצועים טובים יותר, ניתן להוסיף גם translateZ(0) או translate3d(0,0,0)
        # שמפעילים האצת חומרה.
        html_content = f"""
        <div id="svg-wrapper" style="
            background-color: #ffffff; /* רקע לבן לאזור התצוגה */
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden; /* מונע גלילה בתוך ה-div בזמן זום */
            width: 100%;
            height: 500px; /* גובה קבוע לעטיפה החיצונית */
            position: relative;
        ">
            <div id="zoomable-svg-container" style="
                transform: scale({current_zoom_level}) translate({current_x_offset}px, {current_y_offset}px) translateZ(0);
                transform-origin: center center; /* הזום יתבצע ממרכז הגרף */
                transition: transform 0.2s ease-out; /* אנימציית זום/היסט חלקה */
                display: flex;
                justify-content: center;
                align-items: center;
                width: 100%;
                height: 100%;
            ">
                {current_svg_content}
            </div>
        </div>
        """
        # --- סוף עטיפת ה-SVG ---

        # הצגת ה-SVG הנבחר באמצעות st.components.v1.html
        # זה מאפשר להציג מחרוזות HTML/SVG גולמיות
        components.html(
            html_content,
            height=500, # גובה קבוע לאזור הגרף
            scrolling=False # מונע גלילה בתוך אזור ה-HTML
        )
    else:
        st.info("ℹ️ No plots were made")

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.9em;">
  This app was developed using Streamlit Python.
  <br>
   Source code accessible in <a href="https://github.com/bueinat/clifford-hidden-percolation/tree/main/widget" target="_blank" rel="noopener noreferrer" style="color: #F63366; text-decoration: none;">GitHub</a>
</div>
""", unsafe_allow_html=True)

