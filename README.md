## E-Commerce Business Analyser

Comprehensive end-to-end ML project that performs product analytics, customer behavior modeling, segmentation, inventory & delivery analytics, revenue KPIs, and anomaly detection for an e-commerce business.

### Project Highlights
- Modular Python package in `src/` with preprocessing, feature engineering, modeling, evaluation, and visualization utilities.
- Synthetic-yet-realistic datasets under `data/` and generated processed data under `artifacts/`.
- Rich model zoo covering regression, classification, clustering, and anomaly detection.
- Visualization dashboard and final report with actionable insights.

### Quickstart
1. Create a virtual environment and install requirements.
2. Run the main pipeline script to regenerate datasets, train models, and export figures.
3. Explore notebooks in `notebooks/` for additional experimentation.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# headless environments
export MPLCONFIGDIR=$(pwd)/.matplotlib
export LOKY_MAX_CPU_COUNT=4

# Run the ML pipeline (optional)
python main.py

# Launch the analytics web app (Streamlit - original)
streamlit run app.py

# OR Launch the new Next.js web application
# Terminal 1: Start Flask API backend
python flask_api.py

# Terminal 2: Start Next.js frontend
cd frontend
npm install
npm run dev
# Then open http://localhost:3000 in your browser
```

### Web Application Overview

- **Part A – Marketing Site**: Hero CTA, pain points, features, USP, use-cases, how-it-works, testimonials, footer.
- **Part B – Analytics Studio**: Secure workspace where business owners upload CSV/XLSX (orders, customers, products, returns, traffic, inventory) or use demo data.
- **Modules**:
  - Cohort analysis with retention curves, first-purchase cohorts, geography, and comparison presets.
  - Product intelligence: hero vs zero dashboard, dead stock prediction, price elasticity, sentiment proxy, seasonality, funnel conversion, cross-sell matrix, discount dependency, complaints.
  - Customer segmentation via automated RFM labeling (Champions, Loyal, Big Spenders, At Risk, Lost) with LTV + city splits.
  - Demand forecasting (monthly demand, seasonal patterns, festival spikes) using seasonal linear regression signals.
  - Anomaly detection for returns, conversions, suspicious orders, supplier delays.
  - Inventory insights: days of stock left, over/under-stock alerts, refill recommendations, auto replenishment hints.
  - Store heatmaps: hourly visitor peaks, conversion funnel, engagement over time.
  - Export center: downloadable Excel, PDF, and dashboard image bundle.

### Upload Schema Expectations

Upload a single XLSX workbook with sheets named:

- `orders`: order_id, customer_id, product_id, order_date, quantity, revenue, discount_rate, acquisition_channel, city, region, festival, cart_adds, page_views, supplier_delay_hours…
- `customers`: demographics, tenure, spend, engagement, geography, acquisition channel…
- `products`: product_id, sku, category, price, cost_price, rating, demand, seasonality…
- `inventory`: product_id, stock_on_hand, safety_stock, weekly_orders, incoming_stock…
- `returns`: order_id, product_id, customer_id, return_date, reason, severity, refund_amount…
- `traffic`: timestamp/date, hour, visitors, add_to_cart, purchases, bounce_rate…

CSV uploads are treated as `orders`-only datasets; use the demo data switch for a full showcase.

### Outputs

- `reports/summary.md`: Markdown summary after running `main.py`.
- `artifacts/plots/`: Auto-generated PNG visuals (regression comparison, revenue trends, heatmaps, confusion matrices, etc.).
- Streamlit exports: Excel workbook, PDF narrative, downloadable dashboard image ZIP.

### Repository Layout
- `data/`: Raw CSV inputs, including generated sales, customers, products, inventory logs.
- `src/data_prep/`: Data ingestion, cleaning, feature engineering, and splitting utilities.
- `src/modeling/`: Regression, classification, clustering, anomaly detection modules.
- `src/visualization/`: Plotting utilities and dashboard generator.
- `artifacts/`: Persisted models, scalers, processed datasets, and plots.
- `notebooks/`: Exploratory notebooks for deeper analysis and validation.
- `reports/`: Generated dashboard assets and final PDF report.

### Workflows
1. **Product Analytics**  
   - Predict sales from price, rating, demand features using linear and polynomial regression.  
   - Evaluate with MSE, RMSE, and R².  
2. **Customer Behaviour Analysis**  
   - Predict churn and customer value segments using Logistic Regression, SVM, KNN, Naive Bayes, Decision Tree, and Random Forest.  
   - Provide confusion matrices, accuracy, precision, recall, and F1 for each model.  
3. **Customer Segmentation**  
   - Cluster customers via K-Means and DBSCAN; visualize clusters and interpret segments.  
4. **Inventory & Delivery Analytics**  
   - Predict delivery time, identify fast/slow-moving products, and plot order-time heatmaps.  
5. **Revenue & KPI Analysis**  
   - Visualize revenue trends, average order value, top categories, retention metrics, and weekly/daily heatmaps.  
6. **Anomaly Detection (Optional)**  
   - Flag anomalous orders using clustering or distance-based methods.

### Status
Scaffolding ready. Implement pipelines, populate datasets, and extend modules per needs.

