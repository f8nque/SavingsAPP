def weekly_saving_data_query(today,week_start,week_end,user):
    sql =f"""
    WITH track AS (
    SELECT id,start_date,end_date
    FROM spent_track
    WHERE user_id_id = {user.id}
      AND start_date <= '{today}'
      AND end_date >= '{today}'
    ORDER BY id DESC
    LIMIT 1
),
budget AS (
    SELECT id, name
    FROM spent_budget
    WHERE track_id_id = (SELECT id FROM track)
      AND voided = 0
),
budget_items AS (
    SELECT
        c.id AS budget_category_id,
        bt.budget_id,
        c.name,
        bt.amount AS budget_amount
    FROM spent_budgetitem bt
    INNER JOIN spent_budgetclassitem c
      ON bt.budget_class_item_id = c.id
    WHERE bt.budget_id = (SELECT id FROM budget)
    and c.id in (select category_id_id from spent_weeklysavingstracker where track_id_id = (select id from track) and voided =0)
      AND bt.voided = 0
      AND c.voided = 0
),
spending_summary AS (
    SELECT
        c.budget_category_id,
        SUM(CASE WHEN s.date BETWEEN (SELECT start_date FROM track)  AND (SELECT end_date FROM track)  THEN s.amount ELSE 0 END) AS total_sofar,
        SUM(CASE WHEN s.date BETWEEN '{week_start}' AND '{week_end}' THEN s.amount ELSE 0 END) AS total_thisweek
    FROM spent_spent s
    INNER JOIN spent_category c
      ON s.category_id_id = c.id
    WHERE s.voided = 0
    and s.date between (SELECT start_date FROM track) and '{week_end}'
    GROUP BY c.budget_category_id
)

SELECT
    a.id AS budget_id,
    a.name AS budget_name,
    b.name AS budget_category,
    b.budget_category_id,
    '{week_start}' as week_start,
    '{week_end}' as week_end,
    b.budget_amount,
    IFNULL(s.total_sofar, 0) AS spent_at_start_this_week,
    IFNULL(((b.budget_amount - s.total_sofar) / 20) * 7, 0) AS week_budget,
    IFNULL(s.total_thisweek, 0) AS spent_this_week,
    IFNULL(((b.budget_amount - s.total_sofar) / 20) * 7 - s.total_thisweek, 0) AS week_remaining
FROM budget a
INNER JOIN budget_items b
  ON a.id = b.budget_id
LEFT JOIN spending_summary s
  ON b.budget_category_id = s.budget_category_id
    """
    return sql