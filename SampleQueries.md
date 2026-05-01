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
