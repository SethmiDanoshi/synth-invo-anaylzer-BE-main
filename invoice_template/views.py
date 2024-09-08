# views.py
from .models import Template
from .serializers import TemplateSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.core.files.uploadedfile import InMemoryUploadedFile
import json
from authentication.permissions import IsSystemAdmin, IsOrganization, IsSupplier


@api_view(['POST'])
@permission_classes([IsSupplier])
def save_invoice_template(request):

    template_file = request.FILES.get('template')
    supplier = request.data.get('supplier_id')
    
    if not template_file:
        return Response({"error": "Template file is required."}, status=status.HTTP_400_BAD_REQUEST)

    
    template  = Template.objects.filter(supplier = supplier)
    if template.exists():
        return Response({"error": "Template is already have to this user"}, status=status.HTTP_409_CONFLICT)

    template_content = template_file.read().decode('utf-8')

    serializer_data = {
        'supplier': supplier,
        'template_name': template_file.name,  
        'template_content': template_content,
    }

    serializer = TemplateSerializer(data=serializer_data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['PUT'])
@permission_classes([IsSystemAdmin])
def update_mapping(request):
    template_id = request.data.get('template_id')
    mapping_file = request.FILES.get('mapping')
    admin_id = request.data.get('admin_id')  

    try:
        template = Template.objects.get(id=template_id)
    except Template.DoesNotExist:
        return Response({"error": "Template not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if not isinstance(mapping_file, InMemoryUploadedFile):
        return Response({"error": "Mapping file not provided or invalid format"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        mapping_content = mapping_file.read().decode('utf-8')
        mapping_json = json.loads(mapping_content)
    except json.JSONDecodeError as e:
        return Response({"error": f"Invalid JSON format: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    

    template.mapping = json.dumps(mapping_json)
    template.mapped_status = True
    template.mapped_by = admin_id
    template.save()
    
    serializer = TemplateSerializer(template)
    return Response(serializer.data, status= status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsSystemAdmin])
def get_unmapped_templates(request):
    unmapped_templates = Template.objects.filter(mapped_status = False)
    
    templates = TemplateSerializer(unmapped_templates, many=True)
    
    return Response({"unmapped_templates": templates.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsSupplier])
def get_supplier_template(request):
   try:
        supplier_id = request.query_params.get('supplier_id')
        if not supplier_id:
            return Response({'error': 'supplier_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        template = Template.objects.filter(supplier=supplier_id)
        
        if not template.exists():
            return Response({'error': 'Template not found for the given supplier_id'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TemplateSerializer(template, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
   except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
