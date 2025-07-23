# **Anomaly Analysis Challenge**

This project focuses on identifying anomalous behaviors in hypothetical hourly sales data from Point of Sale (POS) checkouts. The analysis is conducted through a combination of data visualization and SQL queries, with all steps and conclusions thoroughly documented in a Jupyter Notebook.

## **Project Structure**

desafio-analise  
├── data/  
│   ├── checkout\_1.csv         \# Hypothetical sales data for Checkout 1  
│   ├── checkout\_2.csv         \# Hypothetical sales data for Checkout 2  
│   ├── transactions\_1.csv     \# (Additional data, not directly used in this analysis)  
│   └── transactions\_2.csv     \# (Additional data, not directly used in this analysis)  
└── notebooks/  
    ├── Exploratory\_Analysis.ipynb    \# Jupyter Notebook with detailed analysis and conclusions  
    ├── Exploratory\_Analysis.pdf      \# PDF version of the analysis notebook  
    └── exploratory\_with\_wrong\_data.ipynb \# Initial exploration notebook with alternative data (for reference)

## **Challenge Objective**

The main objective of this challenge was to analyze the provided sales data to:

* **Identify anomalous behaviors:** Observe sales patterns that deviate from the norm compared to historical data (previous day, same hour last week, weekly and monthly averages).  
* **Utilize SQL and Graphics:** Employ SQL queries to organize and extract insights from the data, and create graphical visualizations to clearly illustrate sales behaviors and anomalies.  
* **Explain Anomalies:** Provide a concise and data-driven explanation for each anomaly found, contextualizing it with historical references.

## **Analysis Methodology**

The analysis was performed following a structured process, fully documented in the Jupyter Notebook Exploratory\_Analysis.ipynb:

1. **Data Import and Loading:** Data from checkout\_1.csv and checkout\_2.csv files were loaded into suitable data structures for manipulation.  
2. **Graphical Visualization:** Line charts were generated for each checkout, comparing "today's" sales with "yesterday's," "same day last week's," "last week's average," and "last month's average." This step was crucial for the initial visual identification of patterns and anomalies.  
3. **SQL Analysis and Validation:** SQL queries were developed and executed to:  
   * Unify checkout data.  
   * Filter specific data for hours where anomalies were visually identified.  
   * Quantitatively confirm the deviations observed in the graphs by comparing absolute sales values with historical references.  
4. **Anomaly Identification and Explanation:** Based on visual analysis and SQL validation, anomalies were clearly identified and detailed, providing specific observations and contextual comparisons.

## **Analysis Conclusions**

The analysis revealed two main anomalies in the hourly sales data:

* **🔻 Anomaly 1: Sales Drop at Checkout 2 from 3 PM Onwards**  
  * An abrupt drop in checkout\_2 sales to 0 from 3 PM onwards, strongly contrasting with normal historical volumes for that time. The absence of a similar drop in checkout\_1 during the same period suggests a specific checkout\_2 system failure.  
* **🔺 Anomaly 2: Sales Spike at 10 AM Across Both Checkouts**  
  * A significant increase in sales across both checkout systems at 10 AM, exceeding historical averages. While not necessarily a problem, this spike suggests an external event (such as a promotional event or an unexpected customer influx) that affected both systems simultaneously.

These conclusions are detailed with specific data and comparisons in the notebook.

## **How to Access the Full Analysis**

All analysis steps, including Python code, SQL queries, generated graphs, and detailed explanations of anomalies, are formatted and presented in the following Jupyter Notebook:  
**notebooks/Exploratory\_Analysis.ipynb**  
To view the analysis:

1. Ensure you have a Python environment with Jupyter Notebook installed.  
2. Navigate to the notebooks directory of the project.  
3. Open the Exploratory\_Analysis.ipynb file in your browser via Jupyter.  
4. Execute the cells sequentially to replicate the analysis and understand the anomaly identification process.