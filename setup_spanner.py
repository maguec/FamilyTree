import os
import pandas as pd
from dotenv import load_dotenv
from google.cloud import spanner

# Load environment variables
load_dotenv(override=True)
GOOGLE_PROJECT = os.getenv("GOOGLE_PROJECT")
GOOGLE_SPANNER_INSTANCE = os.getenv("GOOGLE_SPANNER_INSTANCE")
GOOGLE_SPANNER_DATABASE = os.getenv("GOOGLE_SPANNER_DATABASE")

# Explicit check to catch the error early
for var_name, value in {
    "GOOGLE_PROJECT": GOOGLE_PROJECT,
    "SPANNER_INSTANCE": GOOGLE_SPANNER_INSTANCE,
    "SPANNER_DATABASE": GOOGLE_SPANNER_DATABASE,
}.items():
    if value is None:
        raise ValueError(
            f"Environment variable {var_name} is missing! Check your .env file."
        )


def setup_spanner_graph():
    client = spanner.Client(project=GOOGLE_PROJECT, disable_builtin_metrics=True)
    instance = client.instance(GOOGLE_SPANNER_INSTANCE)
    database = instance.database(GOOGLE_SPANNER_DATABASE)

    print(f"Recreating Graph and Tables in {GOOGLE_SPANNER_DATABASE}...")

    # 1. Clean up existing Graph and Tables
    ddl_statements = [
        "DROP PROPERTY GRAPH IF EXISTS FamilyGraph",
        "DROP TABLE IF EXISTS Begets",
        "DROP TABLE IF EXISTS Marriages",
        "DROP TABLE IF EXISTS Individuals",
    ]

    # 2. Define Parent Node Table
    ddl_statements.extend(["""CREATE TABLE Individuals (
            ID INT64 NOT NULL,
            First_Name STRING(MAX),
            Last_Name STRING(MAX),
            Gender STRING(1),
            Generation INT64
        ) PRIMARY KEY (ID)"""])

    # 3. Define Interleaved Child Edge Tables
    ddl_statements.extend(
        [
            """CREATE TABLE Marriages (
            ID INT64 NOT NULL,
            Spouse2_ID INT64 NOT NULL,
            FOREIGN KEY (Spouse2_ID) REFERENCES Individuals (ID)
        ) PRIMARY KEY (ID, Spouse2_ID),
          INTERLEAVE IN PARENT Individuals ON DELETE CASCADE""",
            """CREATE TABLE Begets (
            ID INT64 NOT NULL,
            Child_ID INT64 NOT NULL,
            FOREIGN KEY (Child_ID) REFERENCES Individuals (ID)
        ) PRIMARY KEY (ID, Child_ID),
          INTERLEAVE IN PARENT Individuals ON DELETE CASCADE""",
        ]
    )

    # 4. Define Property Graph
    ddl_statements.append("""
        CREATE PROPERTY GRAPH FamilyGraph
        NODE TABLES (Individuals)
        EDGE TABLES (
            Marriages SOURCE KEY (ID) REFERENCES Individuals DESTINATION KEY (Spouse2_ID) REFERENCES Individuals,
            Begets SOURCE KEY (ID) REFERENCES Individuals DESTINATION KEY (Child_ID) REFERENCES Individuals
        )
    """)

    print("Executing DDL statements... (this may take a moment)")
    operation = database.update_ddl(ddl_statements)
    operation.result()
    print("Schema created successfully.")

    # 5. Load Data in Chunks
    def insert_csv_to_spanner(table_name, csv_file, chunk_size=2000):
        print(f"Loading {table_name} from {csv_file}...")
        df = pd.read_csv(csv_file)

        # Rename columns dynamically so we don't have to regenerate the CSVs
        if table_name == "Marriages":
            df.rename(columns={"Spouse1_ID": "ID"}, inplace=True)
        elif table_name == "Begets":
            df.rename(columns={"Parent_ID": "ID"}, inplace=True)

        columns = df.columns.tolist()
        total_rows = len(df)

        # Iterate over the dataframe in chunks to prevent Spanner mutation limit errors
        for start_idx in range(0, total_rows, chunk_size):
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk_df = df.iloc[start_idx:end_idx]

            # --- NEW: Convert numpy.int64 to native python int ---
            data = []
            for row in chunk_df.values:
                # hasattr(x, 'item') safely catches numpy data types and extracts the base python type
                native_row = [x.item() if hasattr(x, "item") else x for x in row]
                data.append(tuple(native_row))

            with database.batch() as batch:
                batch.insert(table_name, columns=columns, values=data)

            # Progress print
            if end_idx % (chunk_size * 50) == 0 or end_idx == total_rows:
                print(
                    f"  -> Inserted {end_idx:,} / {total_rows:,} rows into {table_name}"
                )

        print(f"Completed loading {total_rows:,} rows into {table_name}.\n")

    # Load the generated files from the data subdirectory
    insert_csv_to_spanner("Individuals", "data/individuals.csv")
    insert_csv_to_spanner("Marriages", "data/marriages.csv")
    insert_csv_to_spanner("Begets", "data/begets.csv")


if __name__ == "__main__":
    confirm = input("This will DROP and recreate your tables. Proceed? (y/n): ")
    if confirm.lower() == "y":
        setup_spanner_graph()
    else:
        print("Aborted.")
