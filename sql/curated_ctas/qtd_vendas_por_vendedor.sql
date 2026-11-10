create table lakehouse_curated.qtd_vendas_por_vendedor
with (format = 'parquet', parquet_compression = 'snappy'
,external_location = 's3://pos-graduacao-lakehouse-sked/curated/qtd_vendas_por_vendedor/'
) as select vendedor
           ,count(distinct nfe) as qtd_vendas
       from trusted 
      group by vendedor;