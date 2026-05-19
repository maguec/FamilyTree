# Family Tree

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Python 3 or greater 
- [Working Google Cloud CLI](https://cloud.google.com/sdk/docs/install-sdk)
- A Google Cloud project
- make

## Ensure your cloud project is setup correctly
```bash
gcloud auth application-default login
```

## Setup ENV Vars

```bash
cp env.sample .env
vi .env             #configure the variables
```

## Setup Spanner Instance

### Create Spanner instance if necessary

```bash
make instancecreate
```

### Add a database
```bash
make dbcreate
```

## Load the data

```bash
uv run setup_spanner.py
```

## Sample queries

Some sample [Queries](./SampleQueries.md)
