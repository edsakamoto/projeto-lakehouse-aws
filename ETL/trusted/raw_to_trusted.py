import os
import pandas as pd
import boto3
import tempfile
from datetime import datetime
import unicodedata

#=============
#configuracoes
#=============
AWS_PROFILE = "pos-eng-dados"
BUCKET_NAME = "pos-graduacao-lakehouse-sked"

RAW_PREFIX = 'raw/base_vendas/'
TRUSTED_PREFIX = 'trusted/base_vendas'

#=======================
#funcao normalizar colunas
#=======================
def normalize_column(col):
    col = col.strip().lower()
    col = unicodedata.normalize('NFKD',col)
    col = col.encode('ascii','ignore').decode('utf-8')
    col = col.replace(' ', '_')
    return col

#==============
#sessao aws
#==============
session = boto3.Session(profile_name=AWS_PROFILE)
s3 = session.client('s3')

#==================
#ultimo arquivo raw
#==================
objects = s3.list_objects_v2(
    Bucket=BUCKET_NAME
    ,Prefix=RAW_PREFIX
).get('Contents',[])

if not objects:
    raise Exception('Nenhum arquivo encontrado na camada RAW')

latest_object = max(objects, key=lambda x:x['LastModified'])
latest_key = latest_object['Key']

print('[INFO] último arquivo RAW encontrado')
print(f's3://{BUCKET_NAME}/{latest_key}')

#=================
#download do excel
#=================
tmp_excel = tempfile.NamedTemporaryFile(
    suffix='.xlsx'
    ,delete=False
).name

s3.download_file(BUCKET_NAME,latest_key,tmp_excel)

#==========
# leitura do excel
#===========
df = pd.read_excel(tmp_excel)
df = df.loc[:,~df.columns.str.contains('Unnamed')] 

#===============
#transformação robusta de colunas
#===============
df.columns = [normalize_column(c) for c in df.columns]

#==========================
#conversao de datas(segura)
#==========================
df['dataemissao_dt'] = pd.to_datetime(
    df['dataemissao']
    ,errors='coerce'
)

df['datavencimento_dt'] = pd.to_datetime(
    df['datavencimento']
    ,errors='coerce'
)

#data final como string (sem ambiguidade)
df['dataemissao'] = df['dataemissao_dt'].dt.strftime('%Y-%m-%d %H:%M:%S')
df['datavencimento'] =df['datavencimento_dt'].dt.strftime('%Y-%m-%d %H:%M:%S')

df = df.drop(columns=['dataemissao_dt','datavencimento_dt'])

#====================
#tipagem de dados
#====================
df['qtditens'] = pd.to_numeric(df['qtditens'],erros='coerce')
df['valorunitario'] = pd.to_numeric(df['valorunitatrio'],errors='coerce')
df['peso_liquido'] = pd.to_numeric(df['peso_liquido'],erros='coerce')

df['nfe'] = df['nfe'].astype(str)
df['cliente'] = df['cliente'].astype(str)
df['vendedor'] = df['vendedor'].astype(str)

#===========
#colunas tecnicas
#===========
df['data_ingestao'] = datetime.now().strftime('%Y-%m-%d %H:%M%S')

#==========
#particionamento (usando dataemissao_dt)
#==========
df['_ano'] = pd.to_datetime(df['dataemissao'],errors='coerce').dt.year
df['_mes'] = pd.to_datetime(df['dataemissao'],errors='coerce').dt.month
df['_dia'] = pd.to_datetime(df['dataemissao'],errors='coerce').dt.day

#======
# parquet + upload
#====
tmp_dir = tempfile
for (ano,mes,dia), part in df.groupby(['_ano','_mes','dia']):

    part = part.drop(columns=['_ano','_mes','dia'])

    local_parquet = os.path.join(
        tmp_dir
        ,f'base_vendas_{ano}{mes:02d}{dia:02d}.parquet'
    )

    part.to_parquet(
        local_parquet
        ,engine='pyarrow'
        ,compression='snappy'
        ,index=False
    )

    s3_key = (
        f'{TRUSTED_PREFIX}/'
        f'ano={ano}/mes={mes}/dia={dia}/base_vendas.parquet'
    )
    s3.upload_file(local_parquet,BUCKET_NAME,s3_key)

print('TRUSTED GERADA COM SUCESSO')
print(f's3://{BUCKET_NAME}/{TRUSTED_PREFIX}')