# my_script.py
import wcore as core

# def calculate_result(p, r):
#     """
#     פונקציה לדוגמה שמבצעת חישוב כלשהו על בסיס הפרמטרים p ו-r.
#     במציאות, זה יהיה הקוד הפייתון שלך.
#     """
#     result = p * r + (p / r)
#     return result

def calculate_result(N, p, r):
    try:
        t_factor, periodic, quiet = 4, False, True
        q, u = 0.5, 0
        string_circuit = core.sample_string_circuit(
            N, t_factor, periodic=periodic, p=p, q=q, r=r, u=u)
        g, qubits = core.sample_circuit(
                N, t_factor, string_circuit=string_circuit, apply_state=False, periodic=periodic)
        stats = core.simplified_modified.Stats()
        core.simplify_circuit(g, quiet, core.full_reduce, stats=stats)
        return 0
    except:
        return 1

def main():
    # כאן ירוץ הקוד שלך כשהוא נקרא ישירות
    # במקרה של streamlit, הוא לא ירוץ ישירות מכאן, אלא מתוך הפונקציה באפליקציה.
    pass

if __name__ == "__main__":
    main()