import logging
import threading
import time
import socket
import sys
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from core.factory import CLIPFactory

class CLIPScheduler:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("CLIP_Scheduler")
        self.scheduler = BackgroundScheduler()

    def _is_port_in_use(self, host, port):
        """Varre o soquete de rede local para evitar colisão de alocação de portas."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex((host, port)) == 0

    def _run_job(self, source_id):
        """Executa coletores em lotes orientados a jobs agendados."""
        self.logger.info(f"Iniciando tarefa agendada: {source_id}")
        try:
            collector = CLIPFactory.create(source_id)
            collector.run()
            self.logger.info(f"Tarefa {source_id} finalizada com sucesso.")
        except Exception as e:
            self.logger.error(f"Exceção capturada na execução da tarefa {source_id}: {str(e)}")

    def _start_streaming(self):
        """Valida e orquestra fluxos persistentes em threads isoladas daemon."""
        
        # 1. Configuração Genérica para Serviços de Redes e Escuta Contínua (Exemplo: Socket Stream)
        try:
            streaming_source = self.config.get('sources', {}).get('stream_gateway', {})
            stream_cfg = streaming_source.get('network', {})
            stream_host = stream_cfg.get('host', '0.0.0.0')
            stream_port = int(stream_cfg.get('port', 9095))

            if self._is_port_in_use(stream_host, stream_port):
                print(f"  🔄 [stream_gateway] Serviço contínuo já ativo no sistema (Porta {stream_port})")
            else:
                stream_instance = CLIPFactory.create("stream_gateway")
                stream_thread = threading.Thread(target=stream_instance.run, name="Stream_Receiver_Thread", daemon=True)
                stream_thread.start()
                print(f"  🚀 [stream_gateway] Iniciado em background (Porta {stream_port})")
        except Exception as e:
            self.logger.error(f"Falha ao processar thread de streaming de rede: {str(e)}")

        # 2. Configuração Genérica para Receptores Baseados em Webhooks/API Rest Event-Driven
        try:
            receiver_source = self.config.get('sources', {}).get('api_receiver', {})
            receiver_host = receiver_source.get('host', '0.0.0.0')
            receiver_port = int(receiver_source.get('port', 7000))

            if self._is_port_in_use(receiver_host, receiver_port):
                print(f"  🔄 [api_receiver] Receptor dinâmico já ativo no sistema (Porta {receiver_port})")
            else:
                receiver_instance = CLIPFactory.create("api_receiver")
                receiver_thread = threading.Thread(target=receiver_instance.run, name="API_Receiver_Thread", daemon=True)
                receiver_thread.start()
                print(f"  🚀 [api_receiver] Receptor assíncrono iniciado (Porta {receiver_port})")
        except Exception as e:
            self.logger.error(f"Falha ao processar thread do receptor orientado a eventos: {str(e)}")

    def start(self):
        """Inicializa e vincula as triggers do Crontab definidas nos arquivos YAML."""
        print("\n==========================================================")
        print("⚙️  [CLIP 2.0] Inicializando e Verificando Serviços...")
        print("==========================================================")
        
        self._start_streaming()

        sources_cfg = self.config.get('sources', {})
        continuous_services = ["stream_gateway", "api_receiver"]
        successful_jobs = {}

        for source_id, info in sources_cfg.items():
            if source_id in continuous_services:
                continue

            cron_expr = info.get('scheduler', {}).get('cron') if isinstance(info.get('scheduler'), dict) else None
            
            if cron_expr:
                try:
                    trigger = CronTrigger.from_crontab(cron_expr)
                    
                    self.scheduler.add_job(
                        self._run_job,
                        trigger=trigger,
                        args=[source_id],
                        id=source_id,
                        name=f"Job_{source_id}",
                        replace_existing=True
                    )
                    successful_jobs[source_id] = cron_expr
                except Exception as e:
                    self.logger.error(f"❌ Falha ao mapear agendamento {source_id} com expressão '{cron_expr}': {e}")

        self.scheduler.start()

        print("\n==========================================================")
        print("📋 PAINEL DE CONTROLE - AGENDAMENTOS ATIVOS NO MAESTRO")
        print("==========================================================")
        if successful_jobs:
            for source_id, cron_expr in successful_jobs.items():
                print(f"  📅 Agendado: {source_id} via Cron [{cron_expr}]")
        else:
            print("  Nenhuma tarefa agendada via Cron encontrada.")
        print("==========================================================\n")

        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            print("\n👋 Finalizando inspeção do Maestro de forma limpa...")
            sys.exit(0)
