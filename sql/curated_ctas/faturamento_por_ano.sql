create table lakehouse_curated.faturamento_por_ano
with (format = 'parquet', parquet_compression = 'snappy'
,external_location = 's3://pos-graduacao-lakehouse-sked/curated/faturamento_por_ano/'
) as select ano, sum(qtditens * valorunitario) as faturamento from trusted group by ano;