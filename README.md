# CLIP - Coleta, Limpeza, Integração e Padronização de dados

<div align="center">
  <img src="https://github.com/caju1000/CLIP/blob/main/CLIP.png" alt="Logo do CLIP" width="500px">
</div>

O CLIP é um framework de ingestão de dados modular e de alta performance, projetado para atuar como uma camada inteligente entre fontes de dados heterogêneas e ecossistemas de análise (como o Stack ELK).
Diferente de ferramentas de ETL convencionais, o CLIP foca na resiliência e na padronização, utilizando coletores modulares para buscar dados de diversas fontes por meio de métodos distintos como:
- APIs REST (JSON/XML)
- Protocolos de Rede (TCP/UDP/NMEA)
- Consultas em Bancos de Dados (PostgreSQL, SQL Server, MySQL)
- Monitoramento de Infraestrutura (ICMP Ping, Web Health Checks)

## Atualização e dependências de sistema
```Terminal
sudo apt update
sudo apt install -y python3-pip python3-dev libpq-dev xvfb rabbitmq-server
```

## Instalação do Framework
```Terminal
git clone https://github.com/caju1000/CLIP.git
cd CLIP
pip3 install -e . --break-system-packages
```

## Dependências do Python
```Terminal
pip install -r requirements.txt
```

## Interface de Linha de Comando (CLI)
```Terminal
clip -h
usage: clip [-h] [--source ID] [--list] [--show-jobs] [--debug] [--scheduler]

      __          
    o/  \o   ██████╗██╗     ██╗██████╗ 
    | [] |  ██╔════╝██║     ██║██╔══██╗
   o|    |o ██║     ██║     ██║██████╔╝
    \ __ /  ██║     ██║     ██║██╔═══╝ 
     o  o   ╚██████╗███████╗██║██║     
             ╚═════╝╚══════╝╚═╝╚═╝     
---------------------------------------
  Coleta, Limpeza, Integração e Padronização 
---------------------------------------

Gerenciamento da coleta de Dados.

options:
  -h, --help   show this help message and exit
  --source ID  Executa o pipeline para uma fonte específica.
  --list       Lista todos os coletores instalados no sistema.
  --show-jobs  Mostra o que está agendado no config.yml.
  --debug      Modo inspeção: não envia dados ao RabbitMQ.
  --scheduler  Inicia o agendamento automático (Maestro).
  
```




## Arquitetura do "Maestro"
O framework utiliza uma arquitetura baseada em Factory Design Pattern, permitindo que novos conectores sejam "plugados" ao sistema sem a necessidade de alterar o núcleo do software.

Fluxo de Dados:
- Collectors: Classes especializadas que executam a lógica de extração.
- Maestro (Scheduler): Orquestrador que gerencia frequências de execução e concorrência.
- Broker (RabbitMQ): Garante a persistência e o desacoplamento entre a coleta e a indexação.
- Standardization: Todos os dados são convertidos para o formato CLIP Standard JSON antes da integração.



```mermaid
classDiagram
    class MainMaestro {
        +String source_id
        +Boolean debug_mode
        +Boolean scheduler_mode
        +run_pipeline()
    }

    class CLIPFactory {
        -dict _collectors_registry
        +get_collector(source_id, debug_mode) CLIPCollector
    }

    class CLIPCollector {
        <<abstract>>
        +String name
        +Boolean debug
        +Logger logger
        +Config_YAML config
        #_setup_logging()
        +run()*
        +integrate(queue_name, payload)
    }

    class StreamingDataCollector {
        +int listen_port
        +run()
        #_handle_socket_connection()
    }

    class DatabaseBatchCollector {
        +String db_credentials
        +String checkpoint_timestamp
        +run()
        #_execute_incremental_query()
    }

    class RemoteAPICollector {
        +String api_endpoint
        +String auth_token
        +run()
        #_parse_response_payload()
    }

    class WebScraperCollector {
        +String target_url
        +String regex_pattern
        +run()
        #_extract_html_content()
    }

    class Config_YAML {
        +dict pipeline_settings
        +dict job_scheduler
        +load_config(file_path)
    }

    MainMaestro --> CLIPFactory : solicita objeto por ID
    CLIPFactory ..> CLIPCollector : instancia via factory
    StreamingDataCollector --|> CLIPCollector : herda/implementa
    DatabaseBatchCollector --|> CLIPCollector : herda/implementa
    RemoteAPICollector --|> CLIPCollector : herda/implementa
    WebScraperCollector --|> CLIPCollector : herda/implementa
    CLIPCollector o-- Config_YAML : injeta parâmetros declarativos


```


## Extensibilidade & Plugins (Auto-Discovery)
O CLIP foi projetado sob o princípio de Open-Closed (Aberto para extensão, fechado para modificação). Adicionar uma nova fonte de dados ao ecossistema não requer alterações no núcleo do framework.
Como adicionar uma nova fonte (3 Passos)
### 1. Criar o Coletor:
Crie um arquivo Python em collectors/ herdando da classe base. O CLIP detectará automaticamente sua nova classe via Reflection/Auto-Discovery.

```python
from core.base import CLIPCollector

class MyNewSourceCollector(CLIPCollector):
    def run(self):
        data = self.my_custom_logic()
        self.integrate("my_queue", data)
        
```

### 2. Configurar a Fonte:
Adicione um arquivo YAML na pasta sources.d/. O Maestro lerá as configurações de agendamento e credenciais isoladamente.
```yaml
# sources.d/my_source.yml
monitor_config:
  id: my_new_source
  scheduler: "*/5 * * * *" # Exemplo Cron
  retention_days: 7

```

### 3. Deploy:
Reinicie o serviço ou execute diretamente via CLI:
```Terminal
clip --source my_new_source

```

## Estrutura de Diretório 
```markdown
CLIP/
├── collectors/
│   ├── __init__.py
│   ├── remote_api.py       # Template de API HTTP (Baseado no preps)
│   ├── web_scraper.py      # Template de Scraping HTML (Baseado no termômetro)
│   └── database_batch.py   # 🌟 Template de Banco Relacional Incremental
├── core/
│   ├── __init__.py
│   ├── base.py             # Classe Abstrata CLIPCollector (Template Method)
│   ├── factory.py          # CLIPFactory (Auto-Discovery de plugins)
│   └── scheduler.py        # CLIPScheduler (Maestro Engine multi-thread)
├── sources.d/
│   ├── remote_api.yaml
│   ├── web_scraper.yaml
│   └── database_batch.yaml # 🌟 Template Configuração declarativa da query e cron
├── templates/
│   ├── database_batch.py   # Cópia limpa para referência de usuários do framework
│   └── database_batch.yaml
├── config.yml              # Parametrização global de infra (Sem senhas expostas)
├── main.py                 # Ponto de entrada CLI (clip --scheduler)
└── setup.py                # Empacotamento de dependências via setuptools



```

## 📄 Licença
Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.
