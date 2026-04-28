
![Logo do CLIP](https://github.com/caju1000/CLIP/blob/main/CLIP.png)



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
