import requests
import re
from datetime import datetime, timezone
from core.base import CLIPCollector

class WebScraperCollector(CLIPCollector):
    def __init__(self, config, debug=False):
        super().__init__(config, debug)
        self.scraper_config = self.config.get('web_target', {})

    def _extract_html_content(self):
        """Captura o DOM de texto bruto da URL alvo configurada."""
        target_url = self.scraper_config.get('url')
        self.logger.info(f"Executando raspagem web no endereço: {target_url}")
        try:
            response = requests.get(target_url, timeout=15)
            response.encoding = self.scraper_config.get('encoding', 'utf-8')
            
            # Limpa quebras de linha para linearização do alvo da regex
            return response.text.replace("\n", " ").replace("\r", "")
        except Exception as e:
            self.logger.error(f"Erro na requisição de raspagem do alvo HTML: {e}")
            return None

    def run(self):
        """Executa a varredura baseada no padrão regex e injeta no broker."""
        html_content = self._extract_html_content()
        if not html_content:
            return

        try:
            regex_pattern = self.scraper_config.get('regex_pattern')
            match = re.search(regex_pattern, html_content)

            if match:
                # Extração baseada em grupos de captura nomeados ou posicionais genéricos
                payload = {
                    "captured_metric_alpha": float(match.group(1)) if match.group(1) else 0.0,
                    "captured_metric_beta": float(match.group(2)) if match.group(2) else 0.0,
                    "captured_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "type": self.config.get('id', 'generic_scraper'),
                    "source": self.scraper_config.get('source_identifier', 'Web_Target_Node')
                }
                
                # Despacha o dicionário encapsulado em lista para o buffer do RabbitMQ
                self.integrate(self.scraper_config.get('queue'), [payload])
                self.logger.info(f"Sucesso: Ingestão de scraping concluída para as métricas extraídas.")
            else:
                self.logger.warning("O padrão de expressão regular não localizou correspondências no HTML.")
        except Exception as e:
            self.logger.error(f"Falha crítica no processamento de expressão regular do Scraper: {e}")
