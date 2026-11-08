import boto3
import time
from pathlib import Path

#==========
#configuracoes
#===========
AWS_PROFILE = 'pos-eng-dados'
AWS_REGION  = 'us-east-1'

ATHENA_DATABASE = 'lakehouse_curated'
ATHENA_OUTUPUT = 's3://pos-graduacao-lakehouse-sked/athena-query-results/'

CURATED_BUCKET = "pos-graduacao-lakehouse-sked"
CURATED_BASE_PREFIX = 'curated' 

POOL_INTERNAL_SECONDS = 2

#========
#resolver path do projeto
#=========
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_FOLDER = PROJECT_ROOT / 'sql' / 'curated_ctas'

#====
#sessao aws
#===
session = boto3.Session(
    profile_name=AWS_PROFILE
    ,region_name=AWS_REGION
)

athena = session.client('athena')
s3 = session.client('s3')

#====
# funcao: limpar prefix s3
#===
def limpar_s3_prefix(bucket: str, prefix: str):
    
    print(f'limpando s3: s3://{bucket}/{prefix}')

    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket,Prefix=prefix)

    objects_to_delete = []

    for page in pages:
        for obj in page.get('Contents',[]):
            objects_to_delete.append({'Key': obj['Key']})

    if objects_to_delete:
        s3.delete_objects(
            Bucket=bucket
            ,Delete={'Objects':objects_to_delete}
        )
        print('Dados antigos removidos')
    else:
        print('Nenhum dado antigo encontrado')

#===========
#funcao: executar 1 sql
#===========
def executar_sql_unico(query:str, descricao:str):

    response = athena.start_query_execution(
        QueryString = query
        ,QueryExecutionContext={
            'Database': ATHENA_DATABASE
        }
        ,ResultConfiguration={
            'OutputLocation':ATHENA_OUTUPUT
        }
    )

    execution_id = response('QueryExecutionId')
    print(f'{descricao} | QueryExecutionId: {execution_id}')

    while True:
        status_response = athena.get_query_execution(
            QueryExectionId=execution_id
        )

        status = status_response['QueryExecution']['Status']['State']

        if status in ['SUCCEEDED','FAILED','CANCELLED']:
            break

        time.sleep(POOL_INTERNAL_SECONDS)

        if status != 'SUCCEEDED':
            reason = status_response['QueryExection']['Status'].get(
                'StateChangeReason','Motivo não informado'
            )
            raise Exception(f'{descricao} falhou: {reason}')

#===========
#funcao executar ctas
#==========
def executar_ctas(sql_file: Path):

    table_name = sql_file.stem.replace('ctas_','')
    curated_prefix = f'{CURATED_BASE_PREFIX}/{table_name}/'

    print(f'\n Executando CTAs: {sql_file.name}')
    print(f'Tabela: lakehouse_curated.{table_name}')

    #limpar s3
    limpar_s3_prefix(
        bucket=CURATED_BUCKET
        ,prefix=curated_prefix
    )

    #drop table
    drop_query = f'Drop table if exists lakehouse_curated.{table_name};'
    executar_sql_unico(
        query=drop_query
        ,descricao=f'Drop {table_name}'
    )

    #create table as select
    with open(sql_file,'r', encoding='utf-8') as f:
        ctas_query = f.read().strip()

    executar_sql_unico(
        query=ctas_query
        ,descricao=f'CTAS {table_name}'        
    )

    print(f'CTAS concluida: {table_name}')

#==================
# execucao principal
#==================
if __name__ == '__main__':

    print('\n=========================')
    print('INICIO PIPELINE CURATED')
    print('===========================')

    if not SQL_FOLDER.exists():
        raise FileNotFoundError(f'Pasta SQL não encontrada: {SQL_FOLDER}')

    sql_files = sorted(SQL_FOLDER.glob('*.sql'))

    if not sql_files:
        raise Exception('Nenhum arquivo SQL encontrado')

    print(f'Pasta de SQL encontrada: \n {SQL_FOLDER}')
    print(f'CTAS encontradas: {len(sql_files)}')

    for sql_file in sql_files:
        executar_ctas(sql_file)

    print('\n PIPELINE CURATED FINALIZADO COM SUCESSO')