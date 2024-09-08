from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework import status
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search, A
import json
from datetime import datetime
from authentication.permissions import IsOrganization,IsSupplier, IsSystemAdmin

es = Elasticsearch(['http://43.204.122.107:9200'])

def build_search_query(params):
    must_clauses = []
    filter_clauses = []

    query_word = params.get('query')
    if query_word:
        must_clauses.append(Q("nested", path="items", query=Q("match", items__description=query_word)))

    organization_id = params.get('organization_id')
    if organization_id:
        must_clauses.append(Q("term", recipient=organization_id))

    supplier_name = params.get('supplier_name')
    if supplier_name:
        must_clauses.append(Q("nested", path="seller", query=Q("match", seller__company_name=supplier_name)))

    start_date = params.get('start_date')
    end_date = params.get('end_date')
    if start_date or end_date:
        date_range = {}
        if start_date:
            date_range["gte"] = start_date
        if end_date:
            date_range["lte"] = end_date
        filter_clauses.append(Q("range", invoice_date=date_range))

   
    invoice_number = params.get('invoice_number')
    if invoice_number:
        must_clauses.append(Q("term", invoice_number=invoice_number))

    currency = params.get('currency')
    if currency:
        must_clauses.append(Q("term", currency=currency))

    issuer = params.get('issuer')
    if issuer:
        must_clauses.append(Q("term", issuer=issuer))

    buyer_name = params.get('buyer_name')
    if buyer_name:
        must_clauses.append(Q("nested", path="buyer", query=Q("match", buyer__company_name=buyer_name)))

    total_amount_min = params.get('total_amount_min')
    total_amount_max = params.get('total_amount_max')
    if total_amount_min or total_amount_max:
        amount_range = {}
        if total_amount_min:
            amount_range["gte"] = float(total_amount_min)
        if total_amount_max:
            amount_range["lte"] = float(total_amount_max)
        filter_clauses.append(Q("range", summary__total_amount=amount_range))

    query = Q("bool", must=must_clauses, filter=filter_clauses)
    return query


@api_view(['GET'])
@permission_classes([IsOrganization])
def search_invoices(request):
    query_params = request.query_params
    size = query_params.get('size', 1000)  

    search_body = {
        "query": build_search_query(query_params).to_dict(),
        "size": size  
    }

    try:
        res = es.search(index="invoices", body=search_body)

        if res['hits']['total']['value'] == 0:
            return Response({"error": "No invoices found matching the search criteria"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(res['hits']['hits'], status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsOrganization])
def organization_products(request):
    organization_id = request.query_params.get('organization_id')

    if not organization_id:
        return Response({"error": "organization_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        search = Search(using=es, index="invoices")
        search = search.filter('term', recipient=organization_id)
        
        search_body = {
            "query": build_search_query(request.query_params).to_dict(),
            "size": 1000
        }
        search.update_from_dict(search_body)

        response = search.execute()
        products = {}
        
        for hit in response.hits:
            try:
                invoice_year = datetime.strptime(hit.invoice_date, "%Y-%m-%dT%H:%M:%S").year
                for item in hit.items:
                    description = item['description']
                    currency = getattr(hit, 'currency', None)
                    if description not in products:
                        products[description] = {"currency": currency, "years": set()}
                    products[description]["years"].add(invoice_year)
            except AttributeError as e:
                return Response({"error": f"Missing attribute in hit: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        product_list = [
            {"description": desc, "currency": details["currency"], "years": sorted(details["years"])}
            for desc, details in products.items()
        ]
        
        return Response(product_list, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    
def build_advanced_search_query(params):
    query = Q('bool', must=[])

    if 'supplier_name' in params:
        query &= Q('nested', path='seller', query=Q('match', seller__company_name=params['supplier_name']))

    if 'start_date' in params and 'end_date' in params:
        query &= Q('range', invoice_date={'gte': params['start_date'], 'lte': params['end_date']})

    if 'invoice_number' in params:
        query &= Q('term', invoice_number=params['invoice_number'])

    if 'currency' in params:
        query &= Q('term', currency=params['currency'])

    if 'total_amount_min' in params and 'total_amount_max' in params:
        query &= Q('range', summary__total_amount={'gte': params['total_amount_min'], 'lte': params['total_amount_max']})

    if 'item_description' in params:
        query &= Q('nested', path='items', query=Q('match', items__description=params['item_description']))

    return Search(using=es, index='invoices').query(query)

@api_view(['POST'])
@permission_classes([IsSystemAdmin])
def build_query(request):
    try:
        params = request.data.get('params', {})
        search = build_advanced_search_query(params)
        query = search.to_dict()
        return Response({"query": query}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsSystemAdmin])
def execute_search(request):
    try:
        query_params = request.data.get('query', {})
        size = query_params.get('size', 1000)

        search = Search.from_dict(query_params)
        search = search.extra(size=size)
        
        response = search.execute()
        
        results = []
        for hit in response:
            document = hit.to_dict()
            document['_id'] = hit.meta.id
            results.append(document)

        return Response({
            "total": response.hits.total.value if hasattr(response.hits.total, 'value') else response.hits.total,
            "results": results
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)