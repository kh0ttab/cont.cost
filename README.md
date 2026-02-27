# Container Economics Calculator

A Streamlit app for calculating container space utilization and unit economics when importing goods from China to USA. Supports Amazon FBA and Walmart WFS fee calculations.

## Features

- **Container Space Calculator**: 20ft, 40ft, 40ft HC containers
- **Import Costs**: Ocean freight, China warehousing, customs fees, insurance, tariffs
- **Amazon FBA**: Referral, fulfillment, storage fees
- **Walmart WFS**: Referral, fulfillment, pick & pack, weight handling, storage
- **Unit Economics**: Landed cost, suggested retail, gross margin

## Deploy to Streamlit Cloud

### Step 1: Push to GitHub

1. Create a new GitHub repository
2. Push this folder to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/container-economics.git
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set:
   - **Branch**: `main`
   - **Main file path**: `container_economics_app/app.py`
6. Click "Deploy"

That's it! Your app will be live at a URL like `https://your-app-name.streamlit.app`

## Local Development

```bash
cd container_economics_app
pip install -r requirements.txt
streamlit run app.py
```

## Product Categories & Tariffs

| Category | Tariff |
|----------|--------|
| Electronics | 7.5% |
| Machinery | 7.5% |
| Furniture | 10% |
| Textiles | 16.5% |
| Footwear | 16.5% |
| Toys | 11% |
| Plastics | 6.5% |
| Default | 21% |

## Import Fees

- Customs Bond: $250
- Customs Entry: $150
- ISI Fee: $150
- MPF: 0.34% of CIF
- HMF: 0.125% of CIF
- ISF: 0.25% of CIF

## Project Structure

```
container_economics_app/
├── app.py                 # Streamlit app (self-contained)
├── requirements.txt       # Dependencies
└── data/
    └── fees_data.json    # Tariffs, fees, container specs
```

## Usage

1. Select container type (20ft/40ft/40hc)
2. Set utilization target %
3. Configure China warehouse days & shipping costs
4. Add items (dimensions, weight, quantity, cost, category)
5. Toggle Amazon FBA / Walmart WFS fees
6. Click "Calculate"
