from elasticsearch import Elasticsearch
from elasticsearch_dsl import Document, Date, Integer, Keyword, Text, Float, Nested, InnerDoc
from datetime import datetime
import json
import threading

# Elasticsearch client
es = Elasticsearch(['http://43.204.122.107:9200'])

class AddressDocument(InnerDoc):
    street = Text()
    city = Text()
    state = Text()
    zip_code = Keyword()
    country = Text()

class ContactDocument(InnerDoc):
    name = Text()
    phone = Keyword()
    email = Keyword()

class CompanyDocument(InnerDoc):
    company_name = Text()
    address = Nested(AddressDocument)
    contact = Nested(ContactDocument)

class ItemDocument(InnerDoc):
    description = Text()
    quantity = Integer()
    unit_price = Float()
    total_price = Float()

class SummaryDocument(InnerDoc):
    subtotal = Float()
    tax_rate = Float()
    tax_amount = Float()
    total_amount = Float()
    discount = Float()

class PaymentInstructionsDocument(InnerDoc):
    bank_name = Text()
    account_number = Keyword()
    routing_number = Keyword()
    swift = Keyword()

class NotesDocument(InnerDoc):
    note = Text()

class InvoiceDocument(Document):
    invoice_number = Keyword()
    invoice_date = Date()
    due_date = Date()
    currency = Keyword()
    issuer = Keyword()
    recipient = Keyword()
    seller = Nested(CompanyDocument)
    buyer = Nested(CompanyDocument)
    items = Nested(ItemDocument)
    summary = Nested(SummaryDocument)
    payment_instructions = Nested(PaymentInstructionsDocument)
    notes = Nested(NotesDocument)
    original_invoice_id = Keyword()  # Add this field

    class Index:
        name = 'invoices'

# Ensure the index is created
InvoiceDocument.init()

def index_invoice(invoice_json, supplier_id, organization_id, original_invoice_id):
    try:
        # Parse the JSON invoice to extract relevant fields
        invoice = json.loads(invoice_json)

        # Extract and convert dates
        invoice_date = datetime.strptime(invoice["invoice"]["header"]["invoice_date"], "%Y-%m-%d")
        due_date = datetime.strptime(invoice["invoice"]["header"]["due_date"], "%Y-%m-%d")

        # Prepare the document
        doc = InvoiceDocument(
            invoice_number=invoice["invoice"]["header"]["invoice_number"],
            invoice_date=invoice_date,
            due_date=due_date,
            currency=invoice["invoice"]["header"]["currency"],
            issuer=supplier_id,
            recipient=organization_id,
            seller=CompanyDocument(
                company_name=invoice["invoice"]["seller"]["company_name"],
                address=AddressDocument(
                    street=invoice["invoice"]["seller"]["address"]["street"],
                    city=invoice["invoice"]["seller"]["address"]["city"],
                    state=invoice["invoice"]["seller"]["address"]["state"],
                    zip_code=invoice["invoice"]["seller"]["address"]["zip_code"],
                    country=invoice["invoice"]["seller"]["address"]["country"]
                ),
                contact=ContactDocument(
                    name=invoice["invoice"]["seller"]["contact"]["name"],
                    phone=invoice["invoice"]["seller"]["contact"]["phone"],
                    email=invoice["invoice"]["seller"]["contact"]["email"]
                )
            ),
            buyer=CompanyDocument(
                company_name=invoice["invoice"]["buyer"]["company_name"],
                address=AddressDocument(
                    street=invoice["invoice"]["buyer"]["address"]["street"],
                    city=invoice["invoice"]["buyer"]["address"]["city"],
                    state=invoice["invoice"]["buyer"]["address"]["state"],
                    zip_code=invoice["invoice"]["buyer"]["address"]["zip_code"],
                    country=invoice["invoice"]["buyer"]["address"]["country"]
                ),
                contact=ContactDocument(
                    name=invoice["invoice"]["buyer"]["contact"]["name"],
                    phone=invoice["invoice"]["buyer"]["contact"]["phone"],
                    email=invoice["invoice"]["buyer"]["contact"]["email"]
                )
            ),
            items=[
                ItemDocument(
                    description=item["description"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total_price=item["total_price"]
                )
                for item in invoice["invoice"]["items"]
            ],
            summary=SummaryDocument(
                subtotal=invoice["invoice"]["summary"]["subtotal"],
                tax_rate=invoice["invoice"]["summary"]["tax_rate"],
                tax_amount=invoice["invoice"]["summary"]["tax_amount"],
                total_amount=invoice["invoice"]["summary"]["total_amount"],
                discount=invoice["invoice"]["summary"]["discount"]
            ),
            payment_instructions=PaymentInstructionsDocument(
                bank_name=invoice["invoice"]["payment_instructions"]["bank_name"],
                account_number=invoice["invoice"]["payment_instructions"]["account_number"],
                routing_number=invoice["invoice"]["payment_instructions"]["routing_number"],
                swift=invoice["invoice"]["payment_instructions"]["swift"]
            ),
            notes=NotesDocument(
                note=invoice["invoice"]["notes"]["note"]
            ),
            original_invoice_id=str(original_invoice_id)  
        )
        doc.save()
        print(f"Invoice {invoice['invoice']['header']['invoice_number']} indexed successfully.")
    except Exception as e:
        print(f"Error indexing invoice: {str(e)}")

def async_index_invoices(invoice_jsons, supplier_id, organization_id, original_invoice_id):
    threads = []
    for invoice_json in invoice_jsons:
        thread = threading.Thread(target=index_invoice, args=(invoice_json, supplier_id, organization_id, original_invoice_id))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()



def delete_invoice_index(invoice_id):
    es.delete(index='invoices', id=invoice_id)
