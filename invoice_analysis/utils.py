from datetime import datetime
import os
import matplotlib.pyplot as plt
import json
from invoice.models import Invoice
from rest_framework.response import Response
from elasticsearch_dsl import Q, Search, A
import pandas as pd
from elasticsearch_dsl import Search
from elasticsearch import Elasticsearch


es = Elasticsearch(['http://43.204.122.107:9200'])




def get_invoice_data(year, product_name, organization_id, es, index="invoices"):
    try:
        year = int(year)
        if year < 1000 or year > 9999:
            raise ValueError("Invalid year")
    except ValueError:
        raise ValueError("Year parameter must be a valid 4-digit number")

    search = Search(using=es, index=index)
    search = search.filter('range', invoice_date={'gte': f'{year}-01-01', 'lte': f'{year}-12-31'})
    search = search.filter('term', recipient=organization_id)
    search = search.query('nested', path='items', query=Q('match', items__description=product_name))

    response = search.execute()

    data = []
    for hit in response.hits:
        invoice_date = hit.invoice_date
        for item in hit.items:
            if item['description'] == product_name:
                supplier_name = hit.seller.company_name
                data.append({
                    'product': item['description'],
                    'price': item['unit_price'],
                    'date': invoice_date,
                    'supplier': supplier_name
                })

    return data


def calculate_price_deviations(data, year):
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month

    monthly_avg = df.groupby(['product', 'year', 'month'])['price'].mean().reset_index()
    overall_avg = monthly_avg.groupby('product')['price'].mean().reset_index()
    overall_avg.rename(columns={'price': 'overall_avg_price'}, inplace=True)

    deviations = pd.merge(monthly_avg, overall_avg, on='product')
    deviations = deviations[deviations['year'] == int(year)]
    deviations['deviation'] = deviations['price'] - deviations['overall_avg_price']

    return deviations

def calculate_supplier_expenditures(organization_id, year):
    start_date = datetime(int(year), 1, 1).isoformat()
    end_date = datetime(int(year), 12, 31).isoformat()

    search_body = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"recipient": organization_id}},
                    {"range": {"invoice_date": {"gte": start_date, "lte": end_date}}}
                ]
            }
        }
    }

    try:
        res = es.search(index="invoices", body=search_body)

        data = []
        for hit in res['hits']['hits']:
            supplier_name = hit['_source']['seller']['company_name']
            total_amount = hit['_source']['summary']['total_amount']
            data.append({
                "supplier_name": supplier_name,
                "total_amount": total_amount
            })

        df = pd.DataFrame(data)
        expenditures_per_supplier = df.groupby('supplier_name')['total_amount'].sum().reset_index()

        suppliers_expenditures = expenditures_per_supplier.to_dict(orient='records')

        return suppliers_expenditures

    except Exception as e:
        raise ValueError(f"Error fetching data from Elasticsearch: {str(e)}")




def calculate_monthly_expenditures(hits):
    data = []
    for hit in hits:
        invoice_date = datetime.strptime(hit.invoice_date, '%Y-%m-%dT%H:%M:%S')
        total_amount = hit.summary.total_amount
        data.append((invoice_date, total_amount))

    if not data:
        return []

    df = pd.DataFrame(data, columns=['invoice_date', 'total_amount'])
    df.set_index('invoice_date', inplace=True)
    monthly_expenditures = df.resample('M').sum()

    expenditures = []
    for date, row in monthly_expenditures.iterrows():
        expenditures.append({
            "month": date.strftime('%Y-%m'),
            "total_expenditure": row['total_amount']
        })

    return expenditures





















