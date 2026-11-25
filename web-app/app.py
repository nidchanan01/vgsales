import os
import time

from flask import Flask, render_template, request
import psycopg2

app = Flask(__name__)

# Query 1: Window Function (RANK) - Top N เกมขายดีในแต่ละแนว
SQL_Q1 = """
SELECT genre, name, platform, global_sales, rnk
FROM (
    SELECT genre, name, platform, global_sales,
           RANK() OVER (PARTITION BY genre ORDER BY global_sales DESC) AS rnk
    FROM vgsales
) AS ranked
WHERE rnk <= %s
ORDER BY genre, rnk
"""

# Query 2: CTE + LAG - ยอดขายรายปีและ % การเติบโตเทียบปีก่อน
SQL_Q2 = """
WITH yearly AS (
    SELECT release_year, SUM(global_sales) AS total_sales
    FROM vgsales
    WHERE release_year IS NOT NULL
    GROUP BY release_year
)
SELECT release_year,
       total_sales,
       LAG(total_sales) OVER (ORDER BY release_year) AS prev_year_sales,
       ROUND(
           (total_sales - LAG(total_sales) OVER (ORDER BY release_year))
           * 100.0
           / LAG(total_sales) OVER (ORDER BY release_year),
       2) AS growth_pct
FROM yearly
ORDER BY release_year
"""

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "labdb"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password123"),
    )


def wait_for_db(retries=30, delay=2):
    for _ in range(retries):
        try:
            get_connection().close()
            return
        except psycopg2.OperationalError:
            time.sleep(delay)
    raise RuntimeError("Cannot connect to PostgreSQL")


def run(sql, params):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return cols, cur.fetchall()
    finally:
        conn.close()


@app.route("/", methods=["GET", "POST"])
def index():
    result = {"q1": None, "q2": None}
    error = None
    top_n = 3

    if request.method == "POST":
        which = request.form.get("which")
        try:
            if which == "q1":
                top_n = max(1, min(int(request.form.get("top_n", 3)), 10))
                result["q1"] = run(SQL_Q1, (top_n,))
            elif which == "q2":
                result["q2"] = run(SQL_Q2, None)
        except (psycopg2.Error, ValueError) as exc:
            error = str(exc)

    return render_template(
        "index.html", result=result, error=error, top_n=top_n,
        sql_q1=SQL_Q1, sql_q2=SQL_Q2,
    )

if __name__ == "__main__":
    wait_for_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
