import boto3
from datetime import datetime
import os
from botocore.exceptions import ClientError

#config iniciais
AWS_PROFILE = 'pos-eng-dados'
BUCKET_NAME = "pos-graduacao-lakehouse-sked"

LEGADO_PREFIX = 'legado'
RAW_PREFIX = 'raw/base_vendas'

FILE_NAME = "base_vendas.xlsx"

#FUNCOES
def get_s3_client():
    session = boto3.Session(profile_name=AWS_PROFILE)
    return session.client('s3')

def gerar_timestamp_execucao():
    return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

def copiar_legado_para_raw(s3_client, bucket, file_name):
    timestamp = gerar_timestamp_execucao()

    origem_key = f'{LEGADO_PREFIX}/{file_name}'
    destino_key = f'{RAW_PREFIX}/ingest_ts={timestamp}/{file_name}'


    print('[INFO] Iniciando copia legado para Raw')
    print(f"Origem: s3://{bucket}/{origem_key}")
    print(f"Destino: s3://{bucket}/{destino_key}")

    try:
        s3_client.copy_object(
            Bucket=bucket,
            CopySource={
                "Bucket": bucket,
                "Key": origem_key
            },
            Key=destino_key
        )

        print("[SUCCESS] Arquivo copiado com sucesso para a camada RAW")
        print(f"[INFO] Timestamp de ingestão: {timestamp}")

    except ClientError as e:
        print("[ERROR] Falha ao copiar arquivo da camada Legado para Raw")
        raise e


# ==================================================
# EXECUÇÃO
# ==================================================

if __name__ == "__main__":
    s3_client = get_s3_client()

    copiar_legado_para_raw(
        s3_client=s3_client,
        bucket=BUCKET_NAME,
        file_name=FILE_NAME
    )