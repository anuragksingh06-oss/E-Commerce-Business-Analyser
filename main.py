"""Main orchestration script for the E-Commerce Business Analyser project."""
from __future__ import annotations

import faulthandler
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src import config
from src.data_prep.data_generator import generate_all
from src.data_prep import preprocess
from src.modeling import regression, classification, clustering, anomaly
from src.visualization import dashboard

faulthandler.enable()


def ensure_data() -> None:
    existing_files = list(config.DATA_DIR.glob("*.csv"))
    if len(existing_files) < 5:
        print("Generating synthetic datasets...")
        generate_all(config.DATA_DIR)


def run_pipeline() -> dict:
    ensure_data()
    datasets = preprocess.load_datasets()

    products = preprocess.preprocess_products(datasets["products"])
    customers = preprocess.preprocess_customers(datasets["customers"])
    orders = datasets["orders"]
    inventory = datasets["inventory"]
    deliveries = datasets["deliveries"]

    # Product analytics
    product_splits = preprocess.get_product_regression_data(products)
    product_results = regression.run_product_regression(product_splits)

    # Delivery analytics
    delivery_splits = preprocess.preprocess_deliveries(deliveries)
    delivery_results = regression.run_delivery_regression(delivery_splits)

    # Customer behaviour
    churn_splits = preprocess.get_churn_data(customers)
    churn_results = classification.train_classifiers(churn_splits)

    value_splits = preprocess.get_value_segment_data(customers)
    value_results = classification.train_classifiers(value_splits)

    # Segmentation
    seg_features, seg_cols = preprocess.get_segmentation_features(customers)
    cluster_results = clustering.run_clustering(seg_features)

    # Anomaly detection
    anomaly_results = anomaly.detect_anomalies(orders)

    # Visualizations
    plot_paths = []
    plot_paths.append(
        dashboard.plot_regression_comparison(
            product_splits.y_test,
            {
                "linear": product_results["linear"]["model"].predict(product_splits.X_test),
                "polynomial": product_results["polynomial"]["model"].predict(product_splits.X_test),
            },
            title="Actual vs Predicted Product Sales",
            filename="product_regression.png",
        )
    )
    plot_paths.append(dashboard.plot_revenue_trend(orders))
    plot_paths.append(dashboard.plot_order_heatmap(orders))
    plot_paths.append(dashboard.plot_top_categories(orders, products))
    plot_paths.append(dashboard.plot_inventory_turnover(inventory))
    plot_paths.append(dashboard.plot_retention(customers))

    churn_labels = ["No", "Yes"]
    churn_cm = churn_results["logistic_regression"]["report"].confusion_matrix
    plot_paths.append(
        dashboard.plot_confusion_matrix(
            churn_cm,
            churn_labels,
            title="Churn - Logistic Regression",
            filename="churn_confusion.png",
        )
    )

    value_labels = sorted(customers["value_segment"].astype(str).unique())
    value_cm = value_results["random_forest"]["report"].confusion_matrix
    plot_paths.append(
        dashboard.plot_confusion_matrix(
            value_cm,
            value_labels,
            title="Value Segment - Random Forest",
            filename="value_confusion.png",
        )
    )

    kmeans_labels = cluster_results["kmeans"]["labels"]
    plot_paths.append(
        dashboard.plot_clusters(
            seg_features,
            kmeans_labels,
            title="Customer Segments (K-Means)",
            filename="customer_clusters.png",
        )
    )

    def serialize_report(report):
        data = vars(report).copy()
        if "confusion_matrix" in data:
            data["confusion_matrix"] = data["confusion_matrix"].tolist()
        return data

    summary = {
        "product_regression": {
            name: serialize_report(result["report"])
            for name, result in product_results.items()
        },
        "delivery_regression": {
            name: serialize_report(result["report"])
            for name, result in delivery_results.items()
        },
        "churn_models": {
            name: serialize_report(result["report"])
            for name, result in churn_results.items()
        },
        "value_models": {
            name: serialize_report(result["report"])
            for name, result in value_results.items()
        },
        "clustering": {
            name: result["summary"] for name, result in cluster_results.items()
        },
        "anomalies": len(anomaly_results["anomalies"]),
        "plots": [str(p) for p in plot_paths],
    }
    return summary, {
        "products": products,
        "customers": customers,
        "orders": orders,
        "inventory": inventory,
        "deliveries": deliveries,
        "seg_features": seg_features,
        "cluster_labels": kmeans_labels,
        "anomalies": anomaly_results["anomalies"],
    }


def save_report(summary: dict) -> Path:
    report_path = config.BASE_DIR / "reports" / "summary.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    def fmt_regression(name, metrics):
        return f"| {name} | {metrics['mse']:.2f} | {metrics['rmse']:.2f} | {metrics['r2']:.3f} |"

    def fmt_classification(name, metrics):
        return (
            f"| {name} | {metrics['accuracy']:.2f} | {metrics['precision']:.2f} | "
            f"{metrics['recall']:.2f} | {metrics['f1']:.2f} |"
        )

    lines = ["# E-Commerce Business Analyser Report", ""]

    lines += ["## Product Regression", "| Model | MSE | RMSE | R² |", "|---|---|---|---|"]
    for name, metrics in summary["product_regression"].items():
        lines.append(fmt_regression(name, metrics))

    lines += ["", "## Delivery Time Regression", "| Model | MSE | RMSE | R² |", "|---|---|---|---|"]
    for name, metrics in summary["delivery_regression"].items():
        lines.append(fmt_regression(name, metrics))

    lines += [
        "",
        "## Customer Churn Models",
        "| Model | Accuracy | Precision | Recall | F1 |",
        "|---|---|---|---|---|",
    ]
    for name, metrics in summary["churn_models"].items():
        lines.append(fmt_classification(name, metrics))

    lines += [
        "",
        "## Customer Value Models",
        "| Model | Accuracy | Precision | Recall | F1 |",
        "|---|---|---|---|---|",
    ]
    for name, metrics in summary["value_models"].items():
        lines.append(fmt_classification(name, metrics))

    lines += [
        "",
        "## Clustering Summary",
    ]
    for name, metrics in summary["clustering"].items():
        lines.append(f"- {name.title()}: {json.dumps(metrics, indent=0)}")

    lines += ["", f"## Anomalies Detected", f"- Total anomalous orders: {summary['anomalies']}\n"]

    lines += ["## Visuals", *[f"- {path}" for path in summary["plots"]]]

    report_path.write_text("\n".join(lines))
    return report_path


def main() -> None:
    summary, context = run_pipeline()
    report_path = save_report(summary)
    print("Pipeline complete. Key outputs saved:")
    print(json.dumps(summary, indent=2))
    print(f"Report written to: {report_path}")
    anomalies_preview = context["anomalies"].head(5)
    print("Sample anomalous orders:\n", anomalies_preview)


if __name__ == "__main__":
    main()
