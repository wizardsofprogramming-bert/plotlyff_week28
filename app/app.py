import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date

from plotly.subplots import make_subplots

# df_superstore = pd.read_excel('../sources/Sample - Superstore.xls')
df_stateabbrevs = pd.read_csv('../sources/State abbreviations.csv')
df_superstore_geos = pd.read_csv('../sources/Superstore_with_LAT_LNG.csv')
df_combined = df_superstore_geos.merge(df_stateabbrevs, how='left', left_on='State/Province', right_on='Full Name')
df_combined['Order Date'] = pd.to_datetime(df_combined['Order Date'], origin='1899-12-30', unit='D')
df_combined['Order Year'] = df_combined['Order Date'].dt.year
df_combined['Order Month'] = df_combined['Order Date'].dt.strftime("%b")
df_combined['Order Month Year'] = df_combined['Order Month'] + ' ' + df_combined['Order Year'].astype(str)
df_combined['Ship Date'] = pd.to_datetime(df_combined['Ship Date'], origin='1899-12-30', unit='D')
df_combined['Ship Year'] = df_combined['Ship Date'].dt.year
df_combined['Ship Month'] = df_combined['Ship Date'].dt.strftime("%b")
df_combined['Ship Month Year'] = df_combined['Ship Month'] + ' ' + df_combined['Ship Year'].astype(str)
df_combined = df_combined.sort_values(by='Order Date', ascending=True)

datetime_default_start = date(2024, 1, 1)
datetime_default_end = date(2024, 12, 31)

def filter_df_by_datetimes(df, date_column, start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    filtered_df = df[(df[date_column] >= start_date) & (df[date_column] <= end_date)]
    return filtered_df

df_default = filter_df_by_datetimes(df_combined, date_column='Order Date', start_date=datetime_default_start, end_date=datetime_default_end)


# Initialize the app
app = dash.Dash(__name__)


# Figure functions
def generage_fig1(df_to_chart):
    sales_over_time_bycategory = df_to_chart.groupby(['Order Month Year', 'Order Month', 'Order Year', 'Category'])['Sales'].sum().reset_index()
    cats = ['Jan', 'Feb', 'Mar', 'Apr','May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    sales_over_time_bycategory['Order Month'] = pd.Categorical(sales_over_time_bycategory['Order Month'], categories=cats, ordered=True)
    sales_over_time_bycategory = sales_over_time_bycategory.sort_values(by=['Order Year', 'Order Month'])
    sales_over_time = df_to_chart.groupby(['Order Month Year', 'Order Month', 'Order Year'])['Sales'].sum().reset_index()
    sales_over_time['Order Month'] = pd.Categorical(sales_over_time['Order Month'], categories=cats, ordered=True)
    sales_over_time = sales_over_time.sort_values(by=['Order Year', 'Order Month'])

    fig = px.bar(sales_over_time_bycategory, x='Order Month Year', y='Sales', color='Category', barmode='group')
    fig.add_scatter(
        x=sales_over_time['Order Month Year'],
        y=sales_over_time['Sales'],
        mode='lines+markers',
        name='Total Sales',
        line=dict(color='green', width=2)
    )
    fig.update_layout(
        title='Sales Over Time',
        xaxis_title=None,
        yaxis_title=None
    )
    return fig

def generage_fig2(df_to_chart):
    # Group by 'Order Month Year', 'Order Month', 'Order Year', 'Segment' and sum sales
    sales_over_time_bysegment = df_to_chart.groupby(
        ['Order Month Year', 'Order Month', 'Order Year', 'Segment']
    )['Sales'].sum().reset_index()

    # Define the order of months
    cats = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    sales_over_time_bysegment['Order Month'] = pd.Categorical(
        sales_over_time_bysegment['Order Month'],
        categories=cats,
        ordered=True
    )

    # Sort the dataframe by 'Order Year' and 'Order Month'
    sales_over_time_bysegment = sales_over_time_bysegment.sort_values(by=['Order Year', 'Order Month'])

    # Calculate total sales by 'Order Month Year'
    total_sales_by_month = sales_over_time_bysegment.groupby('Order Month Year')['Sales'].sum().reset_index()
    total_sales_by_month.rename(columns={'Sales': 'Total Sales'}, inplace=True)

    # Merge total sales back into the main dataframe
    sales_over_time_bysegment = sales_over_time_bysegment.merge(total_sales_by_month, on='Order Month Year')
    sales_over_time_bysegment['Percentage'] = (sales_over_time_bysegment['Sales'] / sales_over_time_bysegment['Total Sales']) * 100
    # Create the subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Create separate bar traces for each segment
    segments = sales_over_time_bysegment['Segment'].unique()
    colors = ['blue', 'orange', 'green', 'red']  # Define colors for each segment

    for i, segment in enumerate(segments):
        segment_data = sales_over_time_bysegment[sales_over_time_bysegment['Segment'] == segment]
        fig.add_trace(
            go.Bar(
                x=segment_data['Order Month Year'],
                y=segment_data['Percentage'],
                name=f'{segment}',
                marker=dict(color=colors[i % len(colors)])
            ),
            secondary_y=False  # Assign to primary y-axis
        )

    # Add a line for total sales (for reference)
    fig.add_trace(
        go.Scatter(
            x=sales_over_time_bysegment['Order Month Year'].unique(),
            y=total_sales_by_month['Total Sales'],
            mode='lines+markers',
            name='Total Sales',
            line=dict(color='black', width=2)
        ),
        secondary_y=True  # Assign to secondary y-axis
    )

    # Update layout
    fig.update_layout(
        title='Sales Over Time by Segment (%)',
        yaxis_title='Percentage (%)',
        yaxis2_title='Total Sales',
        barmode='relative'
    )
    return fig

def generage_fig3(df_to_chart):
    fig = px.scatter_mapbox(df_to_chart,
                            lat='LAT',
                            lon='LNG',
                            size='Sales',
                            color='Region',
                            hover_data=['City', 'State/Province'],
                            title='Sales by Region',
                            mapbox_style='open-street-map',  # Free and does not require a token
                            zoom=3,
                            center={'lat': 45, 'lon': -95}  # Center the map roughly between US and Canada
                            )
    return fig

# App layout
app.layout = html.Div([
    html.H1("Superstore Sales Dashboard", style={"textAlign": "center"}),

    # Date picker and submit button
    html.Div([
        dcc.DatePickerRange(
            id='date-picker',
            start_date=datetime_default_start,
            end_date=datetime_default_end,
            display_format='YYYY-MM-DD'
        ),
        html.Button("Submit", id='submit-button', n_clicks=0, style={"marginLeft": "20px"})
    ], style={"textAlign": "center", "marginBottom": "20px"}),

    # Quadrant figures
    html.Div([
        html.Div(dcc.Graph(id='fig1', figure=generage_fig1(df_default), style={"width": "48%", "display": "inline-block"})),
        html.Div(dcc.Graph(id='fig2', figure=generage_fig2(df_default)), style={"width": "48%", "display": "inline-block"}),
    ], style={"marginBottom": "20px"}),

    html.Div([
        html.Div(dcc.Graph(id='fig3', figure=generage_fig3(df_default)), style={"width": "100%", "display": "inline-block"}),
    ]),
])

# Callback to update figures based on date range
@app.callback(
    [
        Output('fig1', 'figure'),
        Output('fig2', 'figure'),
        Output('fig3', 'figure'),
    ],
    Input('submit-button', 'n_clicks'),
    State('date-picker', 'start_date'),
    State('date-picker', 'end_date')
)
def update_figures(n_clicks, start_date, end_date):
    df_to_chart = filter_df_by_datetimes(df_combined, date_column='Order Date', start_date=start_date, end_date=end_date)
    return (
        generage_fig1(df_to_chart),
        generage_fig2(df_to_chart),
        generage_fig3(df_to_chart),
    )

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
