import psycopg2  # Ou o driver correspondente (pyodbc, pymysql, etc.)
from datetime import datetime, timezone
from core.base import CLIPCollector

class DatabaseBatchCollector(CLIPCollector):
    def __init__(self, config, debug=False):
        super().__init__(config, debug)
        # Extrai o bloco de parametrização da fonte e a credencial injetada da infra global
        self.query_config = self.config.get('query_settings', {})
        self.db_credentials = self.config.get('databases', {}).get(self.query_config.get('db_alias'), {})

    def _execute_incremental_query(self, cursor, checkpoint_timestamp):
        """Executa a query injetando o marcador temporal para extração incremental."""
        raw_query = self.query_config.get('sql_query')
        incremental_field = self.query_config.get('incremental_field')
        
        # Reconstrói a query dinamicamente aplicando o filtro de checkpoint se ele existir
        if incremental_field and checkpoint_timestamp:
            self.logger.info(f"Executando varredura incremental a partir de: {checkpoint_timestamp}")
            # Estrutura uma query limpa aplicando o filtro de corte na cláusula WHERE ou HAVING
            query = f"SELECT * FROM ({raw_query}) AS base_table WHERE {incremental_field} > %s"
            cursor.execute(query, (checkpoint_timestamp,))
        else:
            self.logger.info("Executando carga total (marcador de checkpoint não localizado).")
            cursor.execute(raw_query)
            
        # Obtém os metadados das colunas para converter a tupla nativa em dicionário (chave/valor)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def run(self):
        """Orquestra a conexão com o banco e despacha o lote extraído para a fila."""
        self.logger.info("Iniciando ciclo de extração de Banco de Dados Relacional.")
        
        if not self.db_credentials:
            self.logger.error("Falha crítica: Credenciais de banco de dados não injetadas pela Factory.")
            return

        records = []
        connection = None
        
        # Simula a leitura de um timestamp de controle (checkpoint persistido)
        # Em produção, pode ser lido de um arquivo local indicado em config.yml['paths']['checkpoints_dir']
        checkpoint_timestamp = self.query_config.get('fallback_checkpoint')

        try:
            # Estabece a conexão de rede com o banco de dados de forma isolada
            connection = psycopg2.connect(
                host=self.db_credentials.get('host', 'localhost'),
                port=self.db_credentials.get('port', 5432),
                database=self.db_credentials.get('database'),
                user=self.db_credentials.get('user'),
                password=self.db_credentials.get('password'),
                connect_timeout=10
            )
            
            with connection.cursor() as cursor:
                raw_records = self._execute_incremental_query(cursor, checkpoint_timestamp)
                
                # Normaliza e enriquece os dicionários para o padrão de indexação do ecossistema
                for row in raw_records:
                    # Converte campos datetime nativos para string ISO se necessário
                    for key, val in row.items():
                        if isinstance(val, datetime):
                            row[key] = val.isoformat()
                            
                    row["type"] = self.config.get('id', 'generic_db_batch')
                    row["source"] = f"DB_{self.query_config.get('db_alias')}"
                    row["captured_at"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                    records.append(row)

        except Exception as e:
            self.logger.error(f"Erro na execução da query ou conexão com o banco: {e}")
            
        finally:
            if connection:
                connection.close()
                self.logger.info("Conexão com o banco de dados encerrada de forma limpa.")

        # Ingestão unificada na fila do Message Broker
        if records:
            self.integrate(self.query_config.get('queue'), records)
            self.logger.info(f"Sucesso: {len(records)} registros extraídos e enviados para a esteira.")
        else:
            self.logger.warning("Nenhum registro novo localizado na janela incremental.")
