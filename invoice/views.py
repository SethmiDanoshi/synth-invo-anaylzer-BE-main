from uuid import UUID
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
import json
import xmltodict
from .models import Invoice
from .utils import format_invoice, map_csv_row_to_invoice
from .serializers import InvoiceSerializer
from rest_framework import status
from search.elasticsearch_utils import async_index_invoices, delete_invoice_index
import threading
import csv
import io
from authentication.permissions import IsOrganization, IsSystemAdmin, IsSupplier
from datetime import datetime, timedelta
from django.db.models import Q




@api_view(['POST'])
@permission_classes([IsSupplier])
def create_invoice(request):
    try:
        source_invoice = request.data.get('source_invoice')
        
        if isinstance(source_invoice, str):
            if source_invoice.strip().startswith('<'):
                source_invoice = xmltodict.parse(source_invoice)
            else:
                source_invoice = json.loads(source_invoice)
        
        elif 'source_invoice' in request.FILES:
            source_invoice_file = request.FILES['source_invoice']
            if source_invoice_file.name.endswith('.xml'):
                source_invoice = xmltodict.parse(source_invoice_file.read())
            else:
                source_invoice = json.load(source_invoice_file)

        supplier_id = request.data.get("supplier_id")
        organization_id = request.data.get("organization_id")

        converted_invoice = format_invoice(source_invoice, supplier_id)
        
        
        invoice_data = {
            'issuer': supplier_id,
            'recipient': organization_id,
            'source_format': json.dumps(source_invoice),  
            'internal_format': json.dumps(converted_invoice),
        }

        serializer = InvoiceSerializer(data=invoice_data)
        
        if serializer.is_valid():
            
            invoice = serializer.save()
         
            threading.Thread(target=async_index_invoices, args=([json.dumps(converted_invoice)], supplier_id, organization_id, invoice.id)).start()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        print(e)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsSupplier])
def bulk_upload_invoices(request):
    try:
        supplier_id = request.data.get("supplier_id")
        organization_id = request.data.get("organization_id")
        csv_file = request.FILES.get('source_invoice')
        
        if not csv_file.name.endswith('.csv'):
            return Response({'error': 'Invalid file format. Please upload a CSV file.'}, status=status.HTTP_400_BAD_REQUEST)

        csv_data = csv_file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_data))
        
        invoices = []
        for row in reader:
            invoice_data = map_csv_row_to_invoice(row, organization_id, supplier_id)
            serializer = InvoiceSerializer(data=invoice_data)
            if serializer.is_valid():
                invoice = serializer.save()
                invoices.append(invoice)
                threading.Thread(target=async_index_invoices, args=([(invoice_data['internal_format'])], invoice.issuer, invoice.recipient, invoice.id)).start()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'success': f'{len(invoices)} invoices uploaded successfully.'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    

@api_view(['GET'])
@permission_classes([IsSupplier])
def supplier_invoice_view(request):
    try:
        supplier_id = request.query_params.get('supplier_id')
        
        invoices = Invoice.objects.filter(issuer=supplier_id)
        serializer = InvoiceSerializer(invoices, many=True)
        
        return Response({'invoices': serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsOrganization])
def organization_invoice_view(request):
    try:
        organization_id = request.query_params.get('orgId')
        
        invoices = Invoice.objects.filter(recipient=organization_id)
        serializer = InvoiceSerializer(invoices, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['PUT'])
@permission_classes([IsOrganization | IsSupplier])
def archive_invoice(request, invoice_id, user_id):
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        
        
        if user_id not in [invoice.recipient, invoice.issuer]:
            return Response({'error': 'You do not have permission to archive this invoice.'}, status=status.HTTP_403_FORBIDDEN)
        
        invoice.archived = True
        invoice.archived_at = datetime.now()
        invoice.archived_by = str(user_id)
        invoice.save()

        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsOrganization | IsSupplier])
def restore_invoice(request, invoice_id, user_id):
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        

        if user_id not in [invoice.recipient,invoice.issuer]:
            return Response({'error': 'You do not have permission to restore this invoice.'}, status=status.HTTP_403_FORBIDDEN)

        invoice.archived = False
        invoice.archived_at = None
        invoice.archived_by = None
        invoice.save()

        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsSystemAdmin])
def delete_invoice(request, invoice_id):
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        invoice.delete()
        delete_invoice_index(invoice_id)
        return Response({'success': 'Invoice deleted successfully.'}, status=status.HTTP_200_OK)
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsOrganization | IsSupplier])
def view_archived_invoices(request, user_id):
    try:
        recipient_invoices = Invoice.objects.filter(archived=True, recipient=user_id)
        
        serializer = InvoiceSerializer(recipient_invoices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)