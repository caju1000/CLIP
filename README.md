
<div align="center">
  <img src="https://github.com/caju1000/CLIP/blob/main/CLIP.png" alt="Logo do CLIP" width="500px">
</div>

```
python3 main.py -h
usage: main.py [-h] [--source ID] [--list] [--show-jobs] [--debug] [--scheduler]

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




## Arquitetura do CLIP
Abaixo está o diagrama de classes que descreve a estrutura do CLIP utilizando o padrão Factory:

```mermaid
classDiagram
    class Main_Maestro {
        +String source_id
        +Boolean debug_mode
        +Boolean scheduler_mode
        +run_pipeline()
    }

    class CLIPFactory {
        +dict _collectors_registry
        +get_collector(source_id, debug) CLIPCollector
    }

    class CLIPCollector {
        <<abstract>>
        +String name
        +Boolean debug
        +Logger logger
        +Config config
        #_setup_logging()
        +run()* +integrate(queue, data)
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
        <<file>>
        +Settings settings
        +Jobs agendamento
    }

    Main_Maestro --> CLIPFactory : solicita objeto por ID
    CLIPFactory ..> CLIPCollector : instancia via factory
    CLIPCollector <|-- StreamingDataCollector : padrão contínuo
    CLIPCollector <|-- DatabaseBatchCollector : padrão incremental
    CLIPCollector <|-- RemoteAPICollector : padrão REST/JSON
    CLIPCollector <|-- WebScraperCollector : padrão Scraping
    CLIPCollector o-- Config_YAML : injeta configurações

