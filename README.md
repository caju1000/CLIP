
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
    class CLIPService {
        +Config config
        +Scheduler scheduler
        +iniciar()
    }
    class ConnectorFactory {
        +get_connector(type, params) BaseConnector
    }
    class BaseConnector {
        <<abstract>>
        +fetch_data()*
        +transform_to_json()*
        +send_to_rabbit()
    }
    ConnectorFactory ..> BaseConnector : cria
    BaseConnector <|-- CSVConnector : implementa
    BaseConnector <|-- APIConnector : implementa
    CLIPService --> ConnectorFactory : solicita
