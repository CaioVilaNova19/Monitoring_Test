# **Transaction Anomaly Monitoring System**

This project implements a real-time transaction monitoring system designed to detect anomalous activities and provide immediate notifications to relevant teams. It offers a comprehensive solution for observing transaction health, identifying deviations from normal patterns, and ensuring proactive incident response.

## **Architecture Diagram**

The following diagram illustrates the key components and their interactions within the monitoring system:  
<div style="text-align: center;">
     \+-------------------+     \+-------------------------+     \+-------------------+  
     |    Data Generator |     |      API Endpoint       |     |     Database      |  
     | (generate\_test\_data.py) \+---\> (transactions\_endpoint.py) \+---\> (transactions.db) |  
     \+-------------------+     |     (Flask App)         |     \+-------------------+  
               |               |                         |              ^  
               |   POST        |   Anomaly Detection     |              |  
               |   Requests    |   (check\_anomaly)       |              | Historical Data  
               V               |                         |              |  
     \+-------------------+     |   Severity Calculation  |              |  
     |    Transaction    |     |   (calculate\_severity)  |              |  
     |     Received      |     \+-----------+-------------+              |  
     \+-------------------+                 |                            |  
               |                           | Trigger Alerts             |  
               |                           V                            |  
               |               \+-----------------------+                |  
               |               |    Alert Services     |                |  
               |               | (email\_alert.py,      |                |  
               |               |  telegram\_alert.py)   |                |  
               |               \+-----------+-----------+                |  
               |                           |                            |  
               |                           V                            |  
               |                   Active Notifications               |  
               |                                                        |  
               |                                                        |  
               |                   Provides Data for Dashboard          |  
               \+--------------------------------------------------------+  
                                            |  
                                            V  
                                     \+-----------------------+  
                                     |       Dashboard       |  
                                     |   (dashboard.html)    |  
                                     \+-----------------------+  
                                        (Real-time Visualization)
                                        
</div>

## **Features**

This monitoring system is designed to meet the following core requirements:

* **Real-time Transaction Data Reception:** An API endpoint receives incoming transaction data (timestamp, status, count) via HTTP POST requests.  
* **Persistent Data Storage:** All received transaction data is stored in an SQLite database (transactions.db) for historical analysis and anomaly detection baseline.  
* **Advanced Anomaly Detection Model:**  
  * Utilizes a **score-based** method to determine anomalies. For each transaction status ('failed', 'denied', 'reversed', 'approved'), it calculates the mean and standard deviation of historical transaction counts for the *same status, day, and hour*.  
  * An anomaly is flagged if the current transaction's count significantly deviates (e.g., exceeds 3 standard deviations) from this calculated baseline.  
* **Anomaly Severity Categorization:** Anomalies are categorized into 'low', 'medium', and 'high' severity levels based on their Z-score, providing a clear indication of risk.  
* **Automated Notification System:** For high-severity anomalies, the system automatically triggers alerts via configured Telegram and Email services, ensuring teams are promptly informed.  
* **Real-time Monitoring Dashboard:** A web-based dashboard provides a dynamic and interactive visualization of transaction metrics, trends, and detected anomalies in real-time. It includes:  
  * Key Performance Indicators (KPIs) for a quick overview.  
  * Line charts displaying average transaction counts and anomaly thresholds per hour for each status.  
  * A horizontal bar chart showing the overall transaction distribution by status.  
  * A list of recent transactions, visually highlighting detected high-severity anomalies.

## **Technology Stack**

The project is primarily built using Python, leveraging its robust libraries for web services, data handling, and statistical analysis. The frontend dashboard is implemented with standard web technologies for broad compatibility and real-time interactivity.

* **Backend:**  
  * Python 3.x  
  * **Flask:** Web framework for the API endpoint and serving static files (dashboard).  
  * **SQLite3:** Lightweight, file-based database for transaction persistence (built-in Python).  
  * **statistics:** Python's built-in module for statistical calculations (mean, standard deviation).  
  * **requests:** For making HTTP requests (used by the data generator).  
  * **pandas:** For efficient data handling (used by the data generator).  
* **Frontend:**  
  * **HTML5:** Structure of the dashboard.  
  * **CSS3:** Styling and visual presentation.  
  * **JavaScript:** Logic for fetching data, updating charts, and dynamic UI elements.  
  * **Chart.js:** A popular JavaScript library for creating interactive charts.  
  * **Chart.js Datalabels Plugin:** For displaying data values directly on charts.

## **Project Structure**

.  
├── data/  
│   ├── transactions.db               \# SQLite database file (generated)  
│   └── transactions.csv                \# Historical transaction data (initial DB source)  
│   └── transactions_auth_codes.csv       \# Historical transaction data (initial DB source)  
├── app/  
│   ├── transactions\_endpoint.py \# Flask API, anomaly detection, alert triggering, dashboard data provider  
│   ├── generate\_test\_data.py  \# Script to simulate transaction data and anomalies  
│   ├── email\_alert.py         \# Script for sending email alerts (demonstrative)  
│   ├── telegram\_alert.py      \# Script for sending Telegram alerts  
│   └── dashboard.html         \# Real-time web dashboard frontend  
└── README.md                  \# Project documentation  
└── requirements.txt           \# Python dependencies

## **How It Works**

The system operates by continuously receiving transaction data, performing real-time analysis, and visualizing the results.

* ### **transactions\_endpoint.py (The Core Monitoring Service)**   **This Flask application is the central component.**

  * It acts as a **REST API endpoint** (/receive\_transaction) that listens for incoming transaction data (timestamp, status, count) via HTTP POST requests.  
  * Upon receiving data, it **stores** the transaction in the transactions.db database.  
  * It then immediately performs **anomaly detection** using the check\_anomaly function. This function calculates a baseline (mean and standard deviation) from historical transactions for the *same status, day, and hour*. If the current transaction's count exceeds a predefined threshold (e.g., 3 standard deviations above the mean), it's flagged as an anomaly.  
  * The calculate\_severity function assigns a **danger level** ('low', 'medium', 'high') based on the Z-score of the anomaly, providing a quantifiable risk assessment.  
  * For high-severity anomalies, it automatically **triggers alerts** by executing email\_alert.py and telegram\_alert.py as subprocesses.  
  * It also exposes a /dashboard\_data endpoint, which provides aggregated metrics and recent transaction details to the frontend dashboard, enabling real-time visualization.  
  * Finally, it serves the dashboard.html file at the root URL (/).

* ### **generate\_test\_data.py (Transaction Data Simulator)**   **This script is designed to simulate a stream of incoming transaction data to test the monitoring system.**

  * It sends POST requests to the /receive\_transaction endpoint of transactions\_endpoint.py.  
  * It generates a mix of **normal transactions** (with low counts for 'failed', 'denied', 'reversed', and higher counts for 'approved') and **specific high-value anomalies** (e.g., a count of 5000 for a 'denied' transaction) at specific timestamps.  
  * **Crucially, this script does not directly modify or clean the historical database.** Its sole purpose is to simulate incoming data for the endpoint to process.

* ### **email\_alert.py & telegram\_alert.py (Notification Services)**   **These Python scripts are responsible for sending automated notifications when high-severity anomalies are detected.**

  * They are executed by transactions\_endpoint.py as subprocesses, receiving anomaly details (status, timestamp, count) as command-line arguments.  
  * **telegram\_alert.py:** Sends formatted messages to a specified Telegram chat. It uses a dedicated bot token (provided in the script) and requires a configured chat ID.  
  * **email\_alert.py:** This script is a **demonstrative example** and requires further configuration (SMTP server details, sender/receiver credentials) to send actual email alerts.

* ### **dashboard.html (Real-time Monitoring Dashboard)**   **This is the frontend interface for visualizing the transaction data and anomalies.**

  * It's a static HTML file that loads JavaScript (using Chart.js) to interact with the transactions\_endpoint.py.  
  * It periodically fetches data from the /dashboard\_data endpoint.  
  * It presents **real-time graphs** (line charts for trends, horizontal bar chart for distribution) and a **dynamic list of recent transactions**.  
  * High-severity anomalies in the recent transactions list are **visually highlighted** with distinct colors and an animation, providing immediate visual cues to operators.

## **Anomaly Detection Methodology**

The system employs a **score-based anomaly detection** method:

1. **Baseline Calculation:** For each incoming transaction, the system dynamically calculates a baseline by looking at the historical count values for transactions with the **same status** (e.g., 'denied'), occurring on the **same day**, and within the **same hour** (e.g., 21:00-21:59).  
2. **Statistical Metrics:** From this historical data, the mean (average) and standard deviation are computed.  
3. **Threshold Definition:** An anomaly threshold is set as mean \+ (STD\_MULTIPLIER \* standard\_deviation). By default, STD\_MULTIPLIER is 3, meaning a transaction is considered anomalous if its count is more than 3 standard deviations above the historical average for its specific context.  
4. **Severity Classification (Z-score):** The severity of a detected anomaly is determined using its Z-score:  
   * **High:** Z-score ge3  
   * **Medium:** Z-score ge2 and \\\<3  
   * **Low:** Z-score \\\<2 (but still above the mean)  
   * **Unknown:** Not enough historical data to calculate reliable statistics.

This approach ensures that "normal" is defined contextually for each transaction status and time window, making the detection more accurate.

## **Monitoring Alert Requirements**

The system is specifically designed to alert for abnormal increases in certain transaction statuses:

* **Alert transactions if failed transactions are above normal.**  
* **Alert transactions if reversed transactions are above normal.**  
* **Alert transactions if denied transactions are above normal.**

"Above normal" is quantified by the threshold calculated using the statistical model described above. Alerts are specifically triggered for anomalies classified with **"high" severity**.

## **Getting Started**

To set up and run the Transaction Anomaly Monitoring System, please refer to the detailed, step-by-step guide provided in the **Jupyter Notebook: monitoring\_implementation.ipynb**.  
This notebook will walk you through:
 
* **Environment Variables Setup** for alerts.  
* **Initializing the Database**.  
* **Starting the API Endpoint**.  
* **Generating Test Data** to simulate transactions and anomalies.  
* **Accessing the Real-time Monitoring Dashboard**.  
* **Configuring and Checking Alerts** for Telegram and Email.

Follow the instructions within the notebook to get your monitoring system up and running.
