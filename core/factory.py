import os
import importlib

class CLIPFactory:
    @staticmethod
    def get_available_sources():
        """Varre dinamicamente a pasta de plugins de coleta."""
        base_dir = "/usr/local/bin/CLIP2"
        collectors_path = os.path.join(base_dir, "collectors")
        
        if not os.path.exists(collectors_path):
            return []
        
        try:
            files = os.listdir(collectors_path)
            return [f.replace(".py", "") for f in files if f.endswith(".py") and not f.startswith("__")]
        except Exception:
            return []

    @staticmethod
    def create(source_id, debug=False):
        """Instancia o coletor injetando dicionários de parametrização global."""
        from main import load_config
        full_config = load_config()

        sources_dict = full_config.get('sources', {})
        source_data = sources_dict.get(source_id)
        
        if not source_data:
            source_data = full_config.get(source_id)

        if not source_data:
            raise Exception(f"Configuração declarativa para '{source_id}' não localizada no escopo do projeto.")

        # Isolamento do escopo de memória do objeto configurador
        source_config = source_data.copy()

        # Injeção de componentes genéricos compartilhados
        source_config['rabbitmq'] = full_config.get('rabbitmq')
        source_config['databases'] = full_config.get('databases')
        source_config['paths'] = full_config.get('paths')

        try:
            module_name = f"collectors.{source_id}"
            module = importlib.import_module(module_name)
            importlib.reload(module)
        except ImportError as e:
            raise Exception(f"Falha na carga dinâmica do componente 'collectors.{source_id}': {e}")

        # Mecanismo de Auto-Descoberta (Auto-Discovery) da classe filha
        collector_class = None
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            if isinstance(attribute, type) and attribute_name.endswith("Collector") and attribute_name != "CLIPCollector":
                collector_class = attribute
                break

        if not collector_class:
            raise Exception(f"Assinatura padrão '...Collector' não identificada no arquivo: collectors/{source_id}.py")

        try:
            return collector_class(config=source_config, debug=debug)
        except TypeError:
            return collector_class(source_config, debug)
