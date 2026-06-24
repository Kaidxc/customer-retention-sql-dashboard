# GitHub Upload Guide

The project is ready to publish. The current Codex environment could not upload it automatically because:

- GitHub App access returned no installed accounts or repositories.
- GitHub CLI `gh` is not available in this shell.

## Option 1: GitHub Desktop

1. Open GitHub Desktop.
2. Select `File > Add Local Repository`.
3. Choose this folder:

```text
C:\Users\Kaidi\Documents\Job_applications\Customer_Retention_SQL_Dashboard_Project
```

4. If GitHub Desktop asks to create a repository, choose:

```text
customer-retention-sql-dashboard
```

5. Commit all files with:

```text
Create customer retention SQL dashboard project
```

6. Publish the repository to GitHub.

## Option 2: GitHub CLI

Install and authenticate GitHub CLI, then run from the project folder:

```bash
git init
git add .
git commit -m "Create customer retention SQL dashboard project"
gh repo create customer-retention-sql-dashboard --public --source=. --remote=origin --push
```

## Recommended repository description

```text
SQL-driven customer retention analytics project with RFM segmentation, cohort retention, campaign targeting outputs and an HTML dashboard.
```

