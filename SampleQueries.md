## Optimized 10 up / 10 down query

```sql
WITH DistinctEdges AS (
  SELECT parent_id, child_id
  FROM GRAPH_TABLE(
    FamilyGraph
    MATCH (start_node:Individuals {ID: 223199}) <-[e_arr:Begets]-{1,11} (relative:Individuals)
    FOR edge IN e_arr
      RETURN DISTINCT edge.ID AS parent_id, edge.Child_ID AS child_id
    UNION ALL
    MATCH (start_node:Individuals {ID: 223199}) -[e_arr:Begets]->{1,11} (relative:Individuals)
    FOR edge IN e_arr
      RETURN DISTINCT edge.ID AS parent_id, edge.Child_ID AS child_id
  )
)
SELECT
  S.First_Name AS Src_First_Name,
  S.Last_name AS Src_Last_Name,
  S.ID AS Src_ID,
  D.First_Name AS Dst_First_Name,
  D.Last_name AS Dst_Last_Name,
  D.ID AS Dst_ID
FROM DistinctEdges UDE
JOIN Individuals S ON UDE.parent_id = S.ID
JOIN Individuals D ON UDE.child_id = D.ID;
```


## Sample JSON query

```sql
GRAPH FamilyGraph
  MATCH tree_path = (start_node:Individuals {ID: 223199}) <-[:Begets]-{1,10} (relative:Individuals)
  RETURN tree_path
  UNION ALL
  MATCH tree_path = (start_node:Individuals {ID: 223199}) -[:Begets]->{1,10} (relative:Individuals)
  RETURN tree_path
NEXT
RETURN SAFE_TO_JSON(tree_path) AS JSON
```
