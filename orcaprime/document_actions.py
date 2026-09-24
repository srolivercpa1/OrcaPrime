"""Document operations use persisted orders and never mutate business state."""
from pathlib import Path
from . import service_documents


class DocumentActions:
    def __init__(self, workshop, company):
        self.workshop = workshop
        self.company = company

    def generate(self, order_id, destination, kind, paper):
        if not destination: return None
        order = self.workshop.get_order(order_id)
        return service_documents.export_service_document(
            order, order.get('company') or self.company, Path(destination), kind, paper)

    def send(self, path, printer):
        if not printer or not str(printer).strip():
            raise ValueError('Selecione uma impressora instalada no Windows.')
        self.workshop._allow('ATENDIMENTO','TECNICO','FINANCEIRO')
        service_documents.print_document(path, printer)
