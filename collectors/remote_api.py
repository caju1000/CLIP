import requests
from datetime import datetime, timezone
from core.base import CLIPCollector

class RemoteAPICollector(CLIPCollector):
    def __init__(self, config, debug=False):
        super().__init__(config, debug)
        self.api_config = self.config.get('api_endpoint', {})

    def fetch_data(self):
        """Consome o endpoint remoto configurado declarativamente."""
        self.logger.info(f"Iniciando requisição HTTP GET em: {self.api_config.get('url')}")
        try:
            response = requests.get(self.api_config.get('url'), timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            self.logger.error(f"Falha na comunicação com o endpoint remoto: {e}")
            return None

    def _parse_response_payload(self, text):
        """Mapeia e transforma linhas delimitadas por tokens em dicionários estruturados."""
        if not text:
            return []
        
        token_indicator = self.api_config.get('token_indicator', '')
        delimiter = self.api_config.get('delimiter', '*/')
        
        # Filtra linhas baseadas no indicador do arquivo de configuração
        lines = [line.strip() for line in text.splitlines() if line.strip() and line.startswith(token_indicator)]
        records = []
        
        for line in lines:
            parts = line.split(delimiter)
            if len(parts) < 5:
                continue
                
            try:
                # Mapeamento posicional genérico para descaracterização do negócio
                record = {
                    "type": self.config.get('id', 'generic_api'),
                    "source": "Remote_API_Gateway",
                    "uid": parts[1].strip() if len(parts) > 1 else None,
                    "label": parts[2].strip() if len(parts) > 2 else None,
                    "category": parts[3].strip() if len(parts) > 3 else None,
                    "meta_value_a": parts[4].strip() if len(parts) > 4 else None,
                    "captured_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                }
                records.append(record)
            except Exception as e:
                self.logger.warning(f"Erro de parsing no lote de dados posicional: {e}")
                continue
        
        return records

    def run(self):
        """Orquestra o ciclo de vida do pipeline para carga em lote via API."""
        self.logger.info("Iniciando rotina do coletor de API Remota.")
        raw_text = self.fetch_data()
        records = self._parse_response_payload(raw_text)
        
        if records:
            self.integrate(self.api_config.get('queue'), records)
            self.logger.info(f"Carga finalizada com sucesso. {len(records)} payloads integrados.")
        else:
            self.logger.warning("Nenhum registro gerado na janela de ingestão atual.")
