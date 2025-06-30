import base64
import io
import pandas as pd
import matplotlib.pyplot as plt
import PyPDF2
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_daq as daq
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np
import plotly.graph_objs as go

# Create a Dash app instance
app = dash.Dash(__name__)

# Function to calculate dynamic metrics based on the provided DataFrame
def calculate_metrics(df):
    total_records = len(df)
    if total_records == 0:
        return {"completeness": 0, "consistency": 0, "overall_integrity": 0, "valid_records": 0, "invalid_records": 0}

    # Completeness: Percentage of non-null values
    completeness = (df.notnull().mean().mean()) * 100

    # Consistency: Placeholder (e.g., no duplicates)
    consistency = 100 - (df.duplicated().sum() / total_records * 100)

    # Overall Integrity: Weighted average of metrics
    overall_integrity = (0.6 * completeness + 0.4 * consistency)

    # Valid/Invalid Records (example: assume a column 'valid' exists)
    valid_records = df["valid"].sum() if "valid" in df.columns else int(0.9 * total_records)
    invalid_records = total_records - valid_records

    return {
        "completeness": round(completeness, 2),
        "consistency": round(consistency, 2),
        "overall_integrity": round(overall_integrity, 2),
        "valid_records": valid_records,
        "invalid_records": invalid_records,
    }

# Layout of the Dash App
app.layout = html.Div(
    style={
        "font-family": "Arial, sans-serif",
        "padding": "30px",
        "backgroundColor": "#eaf2f8",
        "color": "#2c3e50",
    },
    children=[
        html.H1("Data Integrity Dashboard", style={"text-align": "center", "color": "#34495e"}),

        # File Upload Section
        html.Div(
            children=[
                html.Label(
                    "Upload your CSV, Excel, or PDF files:",
                    style={"font-size": "18px", "font-weight": "bold", "color": "#2c3e50"},
                ),
                dcc.Upload(
                    id="file-upload",
                    children=html.Div(
                        [
                            "Drag and Drop or ",
                            html.A("Click to Upload", style={"color": "#3498db", "cursor": "pointer"}),
                        ]
                    ),
                    style={
                        "width": "100%",
                        "height": "60px",
                        "lineHeight": "60px",
                        "borderWidth": "2px",
                        "borderStyle": "dashed",
                        "borderRadius": "10px",
                        "textAlign": "center",
                        "margin": "10px 0",
                        "backgroundColor": "#f9f9f9",
                    },
                    multiple=True,
                ),
            ],
        ),

        # Loading Spinner
        dcc.Loading(
            id="loading",
            type="circle",
            children=[html.Div(id="loading-output", style={"text-align": "center", "font-size": "20px", "color": "#3498db"})],
        ),

        # Display Metrics and Graphs
        html.Div(
            children=[
                html.Div(id="overall-integrity-gauge", style={"width": "100%", "margin": "20px 0"}),
                html.Div(id="validity-pie-chart", style={"width": "45%", "display": "inline-block", "padding": "20px"}),
                html.Div(id="metrics-bar-chart", style={"width": "45%", "display": "inline-block", "padding": "20px"}),
            ],
            style={"display": "flex", "justify-content": "space-between"},
        ),

        # Footer
        html.Div(
            children=[
                html.Hr(),
                html.P(
                    "Developed by Your Name | Data Integrity Dashboard",
                    style={"text-align": "center", "font-size": "14px", "color": "#7f8c8d"},
                ),
            ]
        ),
    ],
)

# Callback to update the visualizations based on file upload
@app.callback(
    [
        Output("overall-integrity-gauge", "children"),
        Output("validity-pie-chart", "children"),
        Output("metrics-bar-chart", "children"),
        Output("loading-output", "children"),
    ],
    Input("file-upload", "contents"),
    State("file-upload", "filename"),
)
def update_visualizations(contents, filenames):
    if contents is not None:
        all_data = []
        for content, filename in zip(contents, filenames):
            _, content_string = content.split(",")
            decoded = base64.b64decode(content_string)

            if filename.endswith(".csv"):
                df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            elif filename.endswith(".xlsx"):
                df = pd.read_excel(io.BytesIO(decoded), engine="openpyxl")
            elif filename.endswith(".pdf"):
                # Extract text from PDF and create a DataFrame
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(decoded))
                text_data = [page.extract_text() for page in pdf_reader.pages]
                df = pd.DataFrame({"content": text_data})
            else:
                continue

            all_data.append(df)

        # Combine all uploaded data
        combined_df = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

        # Calculate metrics
        metrics = calculate_metrics(combined_df)

        # Create a pie chart for Valid/Invalid Records
        pie_chart = dcc.Graph(
            figure={
                "data": [
                    go.Pie(
                        labels=["Valid", "Invalid"],
                        values=[metrics["valid_records"], metrics["invalid_records"]],
                        marker=dict(colors=["#2ecc71", "#e74c3c"]),
                    )
                ],
                "layout": {
                    "title": "Valid vs Invalid Records",
                    "showlegend": True,
                    "annotations": [
                        {
                            "text": f"Valid: {metrics['valid_records']}, Invalid: {metrics['invalid_records']}",
                            "x": 0.5,
                            "y": 0.5,
                            "showarrow": False,
                            "font": {"size": 18, "color": "#2c3e50"},
                        }
                    ],
                },
            }
        )

        # Create a simple bar plot using matplotlib for Completeness and Consistency
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(
            ["Completeness", "Consistency"],
            [metrics["completeness"], metrics["consistency"]],
            color=["#3498db", "#f39c12"],
        )
        ax.set_title("Integrity Metrics")
        ax.set_ylabel("Percentage")

        # Convert matplotlib figure to PNG image to display in Dash
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode("utf-8")
        img_uri = f"data:image/png;base64,{img_str}"

        # Display percentages
        overall_integrity = f"Overall Integrity: {metrics['overall_integrity']}% (Completeness: {metrics['completeness']}%, Consistency: {metrics['consistency']}%)"
        
        return (
            html.Div([html.H4(overall_integrity)]),
            pie_chart,
            html.Img(src=img_uri, style={"width": "100%", "height": "auto"}),
            "Metrics successfully calculated.",
        )

    return {}, {}, {}, "Upload your files to see results."


if __name__ == "__main__":
    app.run_server(debug=True)
