```sql
GRAPH FamilyGraph
  MATCH tree_path = (r3:Individuals)<-{1,3}-[:Begets]-(start_node:Individuals {ID: 21121}) -[:Begets]->{1, 3} (relative:Individuals)
RETURN SAFE_TO_JSON(tree_path) AS JSON
```
