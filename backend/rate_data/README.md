# EBL Interest Rate Excel Updates

Use `EBL_rates_update_template.xlsx` to update deposit and lending rates.

The workbook has two sheets:

- `Deposit Rates`
- `Lending Rates`

Keep the column names unchanged. After editing the Excel file, save and close it. The backend scheduler checks the file every minute and updates the SQLite database automatically.

Manual import from the project root:

```powershell
python backend\import_rates_excel.py
```
