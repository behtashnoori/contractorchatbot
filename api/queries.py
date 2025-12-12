from typing import Optional, List, Dict, Any


def fetch_kpi_yearly(
	conn,
	supplier_uid: Optional[str],
	supplier_name: Optional[str],
	source: str,
	year: Optional[str],
	limit: int,
	offset: int,
) -> List[Dict[str, Any]]:
	where = []
	params = []

	if supplier_uid:
		where.append("customer_uid = %s")
		params.append(supplier_uid)
	if supplier_name:
		where.append("public.normalize_persian(supplier_name) = public.normalize_persian(%s)")
		params.append(supplier_name)
	if source and source != "all":
		where.append("source = %s")
		params.append(source)
	if year:
		where.append("year_j = %s")
		params.append(year)

	sql = """
		SELECT source, customer_uid, supplier_name, year_j, status, count, amount_a, amount_b
		FROM public.v_kpi_yearly_compact
		{where}
		ORDER BY source, supplier_name, year_j, status
		LIMIT %s OFFSET %s
	""".format(where=("WHERE " + " AND ".join(where)) if where else "")

	params.extend([limit, offset])

	with conn.cursor() as cur:
		cur.execute(sql, params)
		cols = [d[0] for d in cur.description]
		return [dict(zip(cols, r)) for r in cur.fetchall()]






