import argparse
import yaml
import sys
import os
import glob
from core.factory import CLIPFactory
from core.scheduler import CLIPScheduler

BANNER = r"""
      __           
      o/  \o  ██████╗ ██╗      ██╗██████╗ 
     | [] |  ██╔════╝ ██║      ██║██╔══██╗
    o|    |o ██║      ██║      ██║██████╔╝
     \ __ /  ██║      ██║      ██║██╔═══╝ 
      o  o   ╚██████╗ ███████╗ ██║██║     
             ╚═════╝ ╚══════╝ ╚═╝╚═╝     
------------------------------------------------------
  Coleta, Limpeza, Integração e Padronização de dados
------------------------------------------------------
"""

def load_config():
    # Obtém dinamicamente a raiz do projeto (independente de onde for instalado)
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILE = os.path.join(BASE_PATH, "config.yml")
    SOURCES_DIR = os.path.join(BASE_PATH, "sources.d")
    
    full_config = {'sources': {}}
    
    # 1. Carrega configurações globais (Broker, Paths, etc)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                global_cfg = yaml.safe_load(f) or {}
                full_config.update(global_cfg)
        except Exception as e:
            print(f"⚠️ Erro ao ler config.yml global: {e}")

    # 2. Carrega dinamicamente cada arquivo de especificação na sources.d/
    if os.path.exists(SOURCES_DIR):
        yaml_files = glob.glob(os.path.join(SOURCES_DIR, "*.yaml")) + \
                     glob.glob(os.path.join(SOURCES_DIR, "*.yml"))
        
        for file_path in yaml_files:
            try:
                with open(file_path, 'r') as f:
                    source_data = yaml.safe_load(f)
                    if source_data:
                        source_id = source_data.get('id') or os.path.splitext(os.path.basename(file_path))[0]
                        full_config['sources'][source_id] = source_data
            except Exception as e:
                print(f"⚠️ Erro ao carregar especificação de fonte em {file_path}: {e}")
    
    return full_config

def main():
    config = load_config()

    parser = argparse.ArgumentParser(
        description=f"{BANNER}\nFramework extensível de ingestão e padronização de dados.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--source", type=str, metavar="ID", help="Executa o pipeline para uma fonte específica.")
    parser.add_argument("--list", action="store_true", help="Lista todos os coletores mapeados no sistema.")
    parser.add_argument("--show-jobs", action="store_true", help="Mostra os agendamentos ativos em lote.")
    parser.add_argument("--debug", action="store_true", help="Modo inspeção: Executa sem enviar dados ao broker.")
    parser.add_argument("--scheduler", action="store_true", help="Inicia o orquestrador em background (Maestro Scheduler).")
    
    args = parser.parse_args()

    if args.list:
        sources = CLIPFactory.get_available_sources()
        print(BANNER)
        print("💡 Coletores disponíveis mapeados no core (plugins):")
        BASE_PATH = os.path.dirname(os.path.abspath(__file__))
        SOURCES_DIR = os.path.join(BASE_PATH, "sources.d")
        
        for s in sorted(sources):
            print(f"  - {s}")
            
            # Varre de forma abstrata as subchaves declarativas do arquivo YAML da fonte (Ex: endpoints, sub-fontes)
            yaml_path = os.path.join(SOURCES_DIR, f"{s}.yaml")
            if not os.path.exists(yaml_path):
                yaml_path = os.path.join(SOURCES_DIR, f"{s}.yml")
                
            try:
                if os.path.exists(yaml_path):
                    with open(yaml_path, 'r') as f:
                        yaml_data = yaml.safe_load(f) or {}
                        # Procura chaves de agrupamentos genéricos de alvos de coleta para listagem estruturada
                        for group_key in ['endpoints', 'subkeys', 'webforms', 'targets']:
                            if group_key in yaml_data and isinstance(yaml_data[group_key], dict):
                                for item_name in sorted(yaml_data[group_key].keys()):
                                    print(f"     └── 🌐 [{group_key}] {item_name}")
            except Exception:
                pass
        return

    if args.show_jobs:
        sources = config.get('sources', {})
        print(BANNER)
        print("📅 Tarefas Cron Detectadas (sources.d/):")
        if not sources:
            print("  (Nenhuma especificação declarativa encontrada em sources.d/)")
        for sid, info in sources.items():
            cron = info.get('scheduler', {}).get('cron', 'Execução Manual / Contínua')
            print(f"  - {sid.ljust(25)} | Cron: {cron}")
        return

    if args.scheduler:
        print(BANNER)
        print("⚙️  [CLIP 2.0] Inicializando Maestro Engine...")
        scheduler = CLIPScheduler(config)
        scheduler.start()

    elif args.source:
        mode = "(DEBUG)" if args.debug else "(PRODUÇÃO)"
        print(f"🚀 [CLIP 2.0] Executando pipeline para a origem: {args.source} {mode}")
        try:
            collector = CLIPFactory.create(args.source, debug=bool(args.debug))
            
            if collector:
                collector.run()
                print(f"✅ Pipeline para '{args.source}' finalizado.")
            else:
                print(f"❌ Falha de instanciação no componente: {args.source}")

        except Exception as e:
            import traceback
            print(f"❌ Erro crítico no pipeline: {str(e)}")
            if args.debug:
                print("\n--- TRACEBACK COMPLETO ---")
                traceback.print_exc()
    else:
        print(BANNER)
        parser.print_help()

if __name__ == "__main__":
    main()
