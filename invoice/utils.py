from invoice_template.models import Template
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def clean_number_string(number_str: str) -> str:
    return number_str.replace('$', '').replace(',', '').strip()

def map_field(data, mapping, data_type=None):
    if isinstance(mapping, float) or isinstance(mapping, int):
        return mapping
    keys = mapping.split('.')
    current_value = data
    for key in keys:
        current_value = current_value.get(key, '')
    
  
    if isinstance(current_value, str):
        current_value = clean_number_string(current_value)
    
    if data_type == 'int':
        return int(current_value) if current_value else 0
    elif data_type == 'float':
        return float(current_value) if current_value else 0.0
    return current_value

def format_invoice(invoice, supplier_id):
    template_mapping = Template.objects.get(supplier=supplier_id)
   
    mapping = json.loads(template_mapping.mapping)
   
   
    formatted_invoice = {
        "invoice": {
            "header": {
                "invoice_number": map_field(invoice, mapping.get("invoice_number", "")),
                "invoice_date": map_field(invoice, mapping.get("invoice_date", "")),
                "due_date": map_field(invoice, mapping.get("due_date", "")),
                "currency": map_field(invoice, mapping.get("currency", ""))
            },
            "seller": {
                "company_name": map_field(invoice, mapping.get("seller.company_name", "")),
                "address": {
                    "street": map_field(invoice, mapping.get("seller.address.street", "")),
                    "city": map_field(invoice, mapping.get("seller.address.city", "")),
                    "state": map_field(invoice, mapping.get("seller.address.state", "")),
                    "zip_code": map_field(invoice, mapping.get("seller.address.zip_code", "")),
                    "country": map_field(invoice, mapping.get("seller.address.country", ""))
                },
                "contact": {
                    "name": map_field(invoice, mapping.get("seller.contact.name", "")),
                    "phone": map_field(invoice, mapping.get("seller.contact.phone", "")),
                    "email": map_field(invoice, mapping.get("seller.contact.email", ""))
                }
            },
            "buyer": {
                "company_name": map_field(invoice, mapping.get("buyer.company_name", "")),
                "address": {
                    "street": map_field(invoice, mapping.get("buyer.address.street", "")),
                    "city": map_field(invoice, mapping.get("buyer.address.city", "")),
                    "state": map_field(invoice, mapping.get("buyer.address.state", "")),
                    "zip_code": map_field(invoice, mapping.get("buyer.address.zip_code", "")),
                    "country": map_field(invoice, mapping.get("buyer.address.country", ""))
                },
                "contact": {
                    "name": map_field(invoice, mapping.get("buyer.contact.name", "")),
                    "phone": map_field(invoice, mapping.get("buyer.contact.phone", "")),
                    "email": map_field(invoice, mapping.get("buyer.contact.email", ""))
                }
            },
            "items": [
                {
                    "description": map_field(item, mapping["items.list"][1]["description"]),
                    "quantity": map_field(item, mapping["items.list"][1]["quantity"], 'int'),
                    "unit_price": map_field(item, mapping["items.list"][1]["unit_price"], 'float'),
                    "total_price": map_field(item, mapping["items.list"][1]["total_price"], 'float')
                } for item in map_field(invoice, mapping["items.list"][0])
            ],
            "summary": {
                "subtotal": map_field(invoice, mapping.get("summary.subtotal", 0.0), 'float'),
                "tax_rate": map_field(invoice, mapping.get("summary.tax_rate", 0.0), 'float'),
                "tax_amount": map_field(invoice, mapping.get("summary.tax_amount", 0.0), 'float'),
                "total_amount": map_field(invoice, mapping.get("summary.total_amount", 0.0), 'float'),
                "discount": map_field(invoice, mapping.get("summary.discount", 0.0), 'float')
            },
            "payment_instructions": {
                "bank_name": map_field(invoice, mapping.get("payment_instructions.bank_name", "")),
                "account_number": map_field(invoice, mapping.get("payment_instructions.account_number", "")),
                "routing_number": map_field(invoice, mapping.get("payment_instructions.routing_number", "")),
                "swift": map_field(invoice, mapping.get("payment_instructions.swift", ""))
            },
            "notes": {
                "note": map_field(invoice, mapping.get("notes.note", ""))
            }
        }
    }
    

    return formatted_invoice

def map_csv_row_to_invoice(row, organization_id, supplier_id):
    converted_invoice = {
        "invoice": {
            "header": {
                "invoice_number": row.get('InvoiceNumber') or 'N/A',
                "invoice_date": convert_date_format(row.get('InvoiceDate')) if row.get('InvoiceDate') else 'N/A',
                "due_date": convert_date_format(row.get('DueDate')) if row.get('DueDate') else 'N/A',
                "currency": row.get('Currency') or 'N/A'
            },
            "seller": {
                "company_name": row.get('SellerCompanyName') or 'N/A',
                "address": {
                    "street": row.get('SellerStreet') or 'N/A',
                    "city": row.get('SellerCity') or 'N/A',
                    "state": row.get('SellerState') or 'N/A',
                    "zip_code": row.get('SellerZipCode') or 'N/A',
                    "country": row.get('SellerCountry') or 'N/A'
                },
                "contact": {
                    "name": row.get('SellerContactName') or 'N/A',
                    "phone": row.get('SellerContactPhone') or 'N/A',
                    "email": row.get('SellerContactEmail') or 'N/A'
                }
            },
            "buyer": {
                "company_name": row.get('BuyerCompanyName') or 'N/A',
                "address": {
                    "street": row.get('BuyerStreet') or 'N/A',
                    "city": row.get('BuyerCity') or 'N/A',
                    "state": row.get('BuyerState') or 'N/A',
                    "zip_code": row.get('BuyerZipCode') or 'N/A',
                    "country": row.get('BuyerCountry') or 'N/A'
                },
                "contact": {
                    "name": row.get('BuyerContactName') or 'N/A',
                    "phone": row.get('BuyerContactPhone') or 'N/A',
                    "email": row.get('BuyerContactEmail') or 'N/A'
                }
            },
            "items": [
                {
                    "description": row.get('ItemDescription') or 'N/A',
                    "quantity": int(row.get('ItemQuantity', '0') or '0'),
                    "unit_price": float(row.get('ItemUnitPrice', '0.0') or '0.0'),
                    "total_price": float(row.get('ItemTotalPrice', '0.0') or '0.0')
                }
            ],
            "summary": {
                "subtotal": float(row.get('InvoiceSubtotal', '0.0') or '0.0'),
                "tax_rate": float(row.get('InvoiceTaxRate', '0.0') or '0.0'),
                "tax_amount": float(row.get('InvoiceTaxAmount', '0.0') or '0.0'),
                "total_amount": float(row.get('InvoiceTotalAmount', '0.0') or '0.0'),
                "discount": float(row.get('InvoiceDiscount', '0.0') or '0.0')
            },
            "payment_instructions": {
                "bank_name": row.get('BankName') or 'N/A',
                "account_number": row.get('AccountNumber') or 'N/A',
                "routing_number": row.get('RoutingNumber') or 'N/A',
                "swift": row.get('SWIFT') or 'N/A'
            },
            "notes": {
                "note": row.get('InvoiceNote') or 'N/A'
            }
        }
    }

    invoice_data = {
        'issuer': supplier_id,
        'recipient': organization_id,
        'source_format': json.dumps(row),
        'internal_format': json.dumps(converted_invoice),
    }
    print(converted_invoice)
    return invoice_data

def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return 'N/A'
