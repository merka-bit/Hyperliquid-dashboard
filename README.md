# Hyperliquid Dashboard

Streamlit dashboard for viewing Hyperliquid trade statistics from a CSV file.

## Project Structure

- `app.py` - main Streamlit app
- `csv/trade_history.csv` - default data source used on startup
- `requirements.txt` - Python dependencies

## Run Locally

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Publish on Streamlit Community Cloud

1. Upload this project to a GitHub repository.
2. Open Streamlit Community Cloud.
3. Create a new app from that repository.
4. Set the main file path to `app.py`.
5. Deploy the app.

## Notes

- The app will automatically load `csv/trade_history.csv` if it exists.
- The current dashboard calculations use a starting capital of `$2,000`.
- If you publish this repository with the CSV included, viewers will be able to see the statistics based on that data.
