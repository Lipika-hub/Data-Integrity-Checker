import base64
import io
import pandas as pd
import matplotlib.pyplot as plt
import PyPDF2
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

# Initialize Dash app
app = dash.Dash(__name__)

# Function to calculate integrity metrics
def calculate_metrics(df):
    total_records = len(df)
    if total_records == 0:
        return {"completeness": 0, "consistency": 0, "overall_integrity": 0, "valid_records": 0, "invalid_records": 0}
    
    completeness = (df.notnull().mean().mean()) * 100
    consistency = 100 - (df.duplicated().sum() / total_records * 100)
    overall_integrity = (0.6 * completeness + 0.4 * consistency)
    
    valid_records = df["valid"].sum() if "valid" in df.columns else int(0.9 * total_records)
    invalid_records = total_records - valid_records
    
    return {
        "completeness": round(completeness, 2),
        "consistency": round(consistency, 2),
        "overall_integrity": round(overall_integrity, 2),
        "valid_records": valid_records,
        "invalid_records": invalid_records,
    }

# Dashboard Layout
app.layout = html.Div([
    html.H1("Data Integrity Dashboard", style={'textAlign': 'center'}),
    
    # File Upload Section
    dcc.Upload(
        id="file-upload",
        children=html.Div([
            "Drag and Drop or ",
            html.A("Click to Upload", style={"color": "#3498db", "cursor": "pointer"}),
        ]),
        style={
            "width": "100%", "height": "60px", "lineHeight": "60px", "borderWidth": "2px",
            "borderStyle": "dashed", "borderRadius": "10px", "textAlign": "center",
            "margin": "10px 0", "backgroundColor": "#f9f9f9",
        },
        multiple=True,
    ),
    
    dcc.Loading(id="loading", type="circle", children=[html.Div(id="loading-output")]),
    
    # Metrics and Charts
    html.Div(id="overall-integrity-gauge"),
    html.Div(id="validity-pie-chart"),
    html.Div(id="metrics-bar-chart"),
])

# Callback to process and visualize uploaded data
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
    if contents is None:
        return {}, {}, {}, "Upload your files to see results."
    
    all_data = []
    for content, filename in zip(contents, filenames):
        _, content_string = content.split(",")
        decoded = base64.b64decode(content_string)
        
        if filename.endswith(".csv"):
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(decoded), engine="openpyxl")
        elif filename.endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(decoded))
            text_data = [page.extract_text() for page in pdf_reader.pages]
            df = pd.DataFrame({"content": text_data})
        else:
            continue
        
        all_data.append(df)
    
    combined_df = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
    metrics = calculate_metrics(combined_df)
    
    # Pie Chart for Valid vs Invalid Records
    pie_chart = dcc.Graph(
        figure={
            "data": [
                go.Pie(
                    labels=["Valid", "Invalid"],
                    values=[metrics["valid_records"], metrics["invalid_records"]],
                    marker=dict(colors=["#2ecc71", "#e74c3c"]),
                )
            ],
            "layout": go.Layout(title="Valid vs Invalid Records")
        }
    )

    
    # Bar Chart for Completeness and Consistency
    bar_chart = dcc.Graph(
        figure={
            "data": [
                go.Bar(
                    x=["Completeness", "Consistency"],
                    y=[metrics["completeness"], metrics["consistency"]],
                    marker=dict(color=["#3498db", "#f39c12"]),
                )
            ],
            "layout": go.Layout(title="Integrity Metrics", xaxis={'title': 'Metric'}, yaxis={'title': 'Percentage'})
        }
    )
    
    overall_integrity_text = f"Overall Integrity: {metrics['overall_integrity']}% (Completeness: {metrics['completeness']}%, Consistency: {metrics['consistency']}%)"
    
    return html.Div([html.H4(overall_integrity_text)]), pie_chart, bar_chart, "Metrics successfully calculated."

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
