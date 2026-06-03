import pika
import json
import logging
import os
from abc import ABC, abstractmethod
from logging.handlers import TimedRotatingFileHandler
from pythonjsonlogger import jsonlogger

class CLIPCollector(ABC):
    def __init__(self, config, debug=False):
        self.config = config
        self.debug = debug
        self.name = config.get('id', 'unnamed_source')
        self._setup_logging()

    def _setup_logging(self):
        """Padroniza a saída de logs em formato estruturado JSON."""
        log_dir = "/var/log/CLIP"
        os.makedirs(log_dir, exist_ok=True)
        log_file = f"{log_dir}/{self.name}.log"
        
        # Rotação diária mantendo retenção de segurança de 7 dias
        handler = TimedRotatingFileHandler(log_file, when="D", interval=1, backupCount=7)
        
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%SZ'
        )
        handler.setFormatter(formatter)
        
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
            
        self.logger.addHandler(handler)
        
        if self.debug:
            console = logging.StreamHandler()
            plain_formatter = logging.Formatter('[%(asctime)s] | %(message)s', datefmt='%H:%M:%S')
            console.setFormatter(plain_formatter)
            self.logger.addHandler(console)

    def integrate(self, queue_name, payload):
        """Dispacha dados de forma robusta fragmentando o buffer de sockets."""
        if not payload:
            return

        records = payload if isinstance(payload, list) else [payload]
        total = len(records)
        
        if self.debug:
            self.logger.info(f"MODO DEBUG: {total} registros seriam enviados para a fila: {queue_name}")
            return

        try:
            broker_cfg = self.config.get('rabbitmq', {})
            host = broker_cfg.get('host', 'localhost')
            
            if broker_cfg.get('user'):
                creds = pika.PlainCredentials(broker_cfg['user'], broker_cfg['pass'])
                params = pika.ConnectionParameters(
                    host=host, 
                    credentials=creds,
                    blocked_connection_timeout=30,
                    heartbeat=60
                )
            else:
                params = pika.ConnectionParameters(host=host)

            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            
            # Declaração dinâmica da fila sem persistência rígida no broker
            channel.queue_declare(queue=queue_name, durable=False)
            
            # Fatiamento em lotes (Chunking) para prevenção de overhead de rede
            batch_size = 500
            for i in range(0, total, batch_size):
                chunk = records[i:i + batch_size]
                for record in chunk:
                    channel.basic_publish(
                        exchange='', 
                        routing_key=queue_name, 
                        body=json.dumps(record, ensure_ascii=False)
                    )
            
            connection.close()
            self.logger.info(f"Sucesso: {total} registros integrados na fila {queue_name}")
            
        except Exception as e:
            self.logger.error(f"Erro no broker de mensageria na fila {queue_name}: {str(e)}")

    @abstractmethod
    def run(self):
        """Método abstrato obrigatório. Define a regra de negócio da extração."""
        pass
