O PrePol (Predictive Policing Model) é um sistema de aprendizado de máquina projetado para estimar a probabilidade de ocorrência de crimes em áreas geográficas discretizadas e períodos de tempo regulares, buscando fornecer uma base analítica para decisões estratégicas de prevenção e policiamento inteligente. Sua concepção parte da premissa de que a criminalidade urbana não se distribui de forma aleatória, mas segue padrões espaço-temporais detectáveis — concentrações que emergem, persistem e se deslocam conforme variáveis sociais, urbanas e operacionais. Para capturar tais dinâmicas, o PrePol utiliza uma abordagem geoespacial baseada em células H3, que convertem coordenadas de latitude e longitude em unidades hexagonais de resolução controlada, permitindo observar o território como uma malha contínua de regiões equivalentes. Cada célula representa um setor urbano monitorado, e cada linha temporal corresponde a uma janela semanal de agregação de ocorrências, formando um painel espaço-temporal estruturado. Sobre essa base, o modelo utiliza o Random Forest Regressor para aprender relações não lineares entre o histórico de crimes, suas recorrências locais (lags temporais), o comportamento das áreas vizinhas e fatores sazonais — como mês, semana e tendência anual. O objetivo central do PrePol não é prever incidentes individuais, mas estimar o risco relativo de cada célula em um dado período futuro, de modo a priorizar recursos e direcionar ações preventivas de forma mais racional e empírica. O projeto, portanto, atua na interseção entre estatística aplicada, aprendizado de máquina e segurança pública, buscando transformar grandes volumes de registros históricos em inteligência territorial interpretável e operacionalmente útil.



Relatórios de Datasets usados.
============================================================
RELATÓRIO — RDO_1
============================================================

Linhas: 793,050 | Colunas: 31

Colunas:
 - ID_DELEGACIA
 - NOME_DEPARTAMENTO
 - NOME_SECCIONAL
 - NOME_DELEGACIA
 - CIDADE
 - ANO_BO
 - NUM_BO
 - NOME_DEPARTAMENTO_CIRC
 - NOME_SECCIONAL_CIRC
 - NOME_DELEGACIA_CIRC
 - NOME_MUNICIPIO_CIRC
 - DESCR_TIPO_BO
 - DATA_OCORRENCIA_BO
 - HORA_OCORRENCIA_BO
 - DATAHORA_COMUNICACAO_BO
 - FLAG_STATUS
 - RUBRICA
 - DESCR_CONDUTA
 - DESDOBRAMENTO
 - DESCR_TIPOLOCAL
 - DESCR_SUBTIPOLOCAL
 - LOGRADOURO
 - NUMERO_LOGRADOURO
 - LATITUDE
 - LONGITUDE
 - DESCR_TIPO_PESSOA
 - FLAG_VITIMA_FATAL
 - SEXO_PESSOA
 - IDADE_PESSOA
 - COR_CUTIS
 - UNNAMED: 30

Tipos de dados:
 - object: 27
 - int64: 3
 - float64: 1

Top 10 colunas com mais nulos (%):
 - DATAHORA_COMUNICACAO_BO: 100.00% nulos
 - UNNAMED: 30: 100.00% nulos
 - FLAG_VITIMA_FATAL: 95.53% nulos
 - DESDOBRAMENTO: 94.41% nulos
 - LONGITUDE: 41.50% nulos
 - LATITUDE: 41.50% nulos
 - DESCR_CONDUTA: 23.38% nulos
 - HORA_OCORRENCIA_BO: 10.20% nulos
 - NUMERO_LOGRADOURO: 6.78% nulos
 - IDADE_PESSOA: 1.29% nulos

Top 10 colunas com mais valores únicos:
 - DATAHORA_COMUNICACAO_BO: 100.00% nulos
 - UNNAMED: 30: 100.00% nulos
 - FLAG_VITIMA_FATAL: 95.53% nulos
 - DESDOBRAMENTO: 94.41% nulos
 - LONGITUDE: 41.50% nulos
 - LATITUDE: 41.50% nulos
 - DESCR_CONDUTA: 23.38% nulos
 - HORA_OCORRENCIA_BO: 10.20% nulos
 - NUMERO_LOGRADOURO: 6.78% nulos
 - IDADE_PESSOA: 1.29% nulos

Top 10 colunas com mais valores únicos:
 - LONGITUDE: 167858
 - LATITUDE: 167697
 - LOGRADOURO: 45662
 - NUM_BO: 15493
 - NUMERO_LOGRADOURO: 8275
 - HORA_OCORRENCIA_BO: 1440
 - ID_DELEGACIA: 910
 - NOME_DELEGACIA: 910
 - DESCR_SUBTIPOLOCAL: 824
 - DATA_OCORRENCIA_BO: 761

Estatísticas básicas (primeiras 5 colunas numéricas):
 - ID_DELEGACIA: média=18473.30, min=10004.00, max=900842.00, std=52778.59
 - ANO_BO: média=2010.59, min=2010.00, max=2017.00, std=0.60
 - NUM_BO: média=12964.72, min=1.00, max=1671520.00, std=90856.43
 - DATAHORA_COMUNICACAO_BO: média=nan, min=nan, max=nan, std=nan

Faixa temporal detectada: 2010-01-01 00:00:00  →  2012-12-01 00:00:00

============================================================
RELATÓRIO — RDO_2
============================================================

Linhas: 1,048,575 | Colunas: 31

Colunas:
 - ID_DELEGACIA
 - NOME_DEPARTAMENTO
 - NOME_SECCIONAL
 - NOME_DELEGACIA
 - CIDADE
 - ANO_BO
 - NUM_BO
 - NOME_DEPARTAMENTO_CIRC
 - NOME_SECCIONAL_CIRC
 - NOME_DELEGACIA_CIRC
 - NOME_MUNICIPIO_CIRC
 - DESCR_TIPO_BO
 - DATA_OCORRENCIA_BO
 - HORA_OCORRENCIA_BO
 - DATAHORA_COMUNICACAO_BO
 - FLAG_STATUS
 - RUBRICA
 - DESCR_CONDUTA
 - DESDOBRAMENTO
 - DESCR_TIPOLOCAL
 - DESCR_SUBTIPOLOCAL
 - LOGRADOURO
 - NUMERO_LOGRADOURO
 - LATITUDE
 - LONGITUDE
 - DESCR_TIPO_PESSOA
 - FLAG_VITIMA_FATAL
 - SEXO_PESSOA
 - IDADE_PESSOA
 - COR_CUTIS
 - UNNAMED: 30

Tipos de dados:
 - object: 27
 - int64: 3
 - float64: 1

Top 10 colunas com mais nulos (%):
 - DATAHORA_COMUNICACAO_BO: 100.00% nulos
 - UNNAMED: 30: 100.00% nulos
 - FLAG_VITIMA_FATAL: 96.31% nulos
 - DESDOBRAMENTO: 93.39% nulos
 - HORA_OCORRENCIA_BO: 25.14% nulos
 - COR_CUTIS: 23.62% nulos
 - DESCR_CONDUTA: 19.10% nulos
 - LONGITUDE: 9.73% nulos
 - LATITUDE: 9.72% nulos
 - NUMERO_LOGRADOURO: 1.92% nulos

Top 10 colunas com mais valores únicos:
 - DATAHORA_COMUNICACAO_BO: 100.00% nulos
 - UNNAMED: 30: 100.00% nulos
 - FLAG_VITIMA_FATAL: 96.31% nulos
 - DESDOBRAMENTO: 93.39% nulos
 - HORA_OCORRENCIA_BO: 25.14% nulos
 - COR_CUTIS: 23.62% nulos
 - DESCR_CONDUTA: 19.10% nulos
 - LONGITUDE: 9.73% nulos
 - LATITUDE: 9.72% nulos
 - NUMERO_LOGRADOURO: 1.92% nulos

Top 10 colunas com mais valores únicos:
 - LONGITUDE: 432871
 - LATITUDE: 431896
 - NUM_BO: 175389
 - LOGRADOURO: 113862
 - NUMERO_LOGRADOURO: 9681
 - HORA_OCORRENCIA_BO: 1441
 - DATA_OCORRENCIA_BO: 1095
 - ID_DELEGACIA: 866
 - NOME_DELEGACIA: 866
 - DESCR_SUBTIPOLOCAL: 854

Estatísticas básicas (primeiras 5 colunas numéricas):
 - ID_DELEGACIA: média=152337.08, min=10004.00, max=990900.00, std=320970.72
 - ANO_BO: média=2014.00, min=2013.00, max=2017.00, std=0.80
 - NUM_BO: média=133094.36, min=1.00, max=1625802.00, std=335739.37
 - DATAHORA_COMUNICACAO_BO: média=nan, min=nan, max=nan, std=nan

Faixa temporal detectada: 2013-01-01 00:00:00  →  2015-12-12 00:00:00

============================================================
RELATÓRIO TEXTUAL — RDO_3
============================================================

Linhas: 553,429 | Colunas: 31

Colunas:
 - ID_DELEGACIA
 - NOME_DEPARTAMENTO
 - NOME_SECCIONAL
 - NOME_DELEGACIA
 - CIDADE
 - ANO_BO
 - NUM_BO
 - NOME_DEPARTAMENTO_CIRC
 - NOME_SECCIONAL_CIRC
 - NOME_DELEGACIA_CIRC
 - NOME_MUNICIPIO_CIRC
 - DESCR_TIPO_BO
 - DATA_OCORRENCIA_BO
 - HORA_OCORRENCIA_BO
 - DATAHORA_COMUNICACAO_BO
 - FLAG_STATUS
 - RUBRICA
 - DESCR_CONDUTA
 - DESDOBRAMENTO
 - DESCR_TIPOLOCAL
 - DESCR_SUBTIPOLOCAL
 - LOGRADOURO
 - NUMERO_LOGRADOURO
 - LATITUDE
 - LONGITUDE
 - DESCR_TIPO_PESSOA
 - FLAG_VITIMA_FATAL
 - SEXO_PESSOA
 - IDADE_PESSOA
 - COR_CUTIS
 - UNNAMED: 30

Tipos de dados:
 - object: 27
 - int64: 3
 - float64: 1

Top 10 colunas com mais nulos (%):
 - DATAHORA_COMUNICACAO_BO: 100.00% nulos
 - UNNAMED: 30: 100.00% nulos
 - FLAG_VITIMA_FATAL: 96.85% nulos
 - DESDOBRAMENTO: 95.45% nulos
 - COR_CUTIS: 37.36% nulos
 - HORA_OCORRENCIA_BO: 31.17% nulos
 - DESCR_CONDUTA: 13.48% nulos
 - LONGITUDE: 2.01% nulos
 - LATITUDE: 2.01% nulos
 - IDADE_PESSOA: 0.55% nulos

Top 10 colunas com mais valores únicos:
 - DATAHORA_COMUNICACAO_BO: 100.00% nulos
 - UNNAMED: 30: 100.00% nulos
 - FLAG_VITIMA_FATAL: 96.85% nulos
 - DESDOBRAMENTO: 95.45% nulos
 - COR_CUTIS: 37.36% nulos
 - HORA_OCORRENCIA_BO: 31.17% nulos
 - DESCR_CONDUTA: 13.48% nulos
 - LONGITUDE: 2.01% nulos
 - LATITUDE: 2.01% nulos
 - IDADE_PESSOA: 0.55% nulos

Top 10 colunas com mais valores únicos:
 - LONGITUDE: 242847
 - LATITUDE: 242411
 - NUM_BO: 217309
 - LOGRADOURO: 48152
 - NUMERO_LOGRADOURO: 8049
 - HORA_OCORRENCIA_BO: 1442
 - ID_DELEGACIA: 749
 - NOME_DELEGACIA: 749
 - DESCR_SUBTIPOLOCAL: 702
 - DATA_OCORRENCIA_BO: 397

Estatísticas básicas (primeiras 5 colunas numéricas):
 - ID_DELEGACIA: média=347226.41, min=10004.00, max=990900.00, std=428001.38
 - ANO_BO: média=2016.08, min=2016.00, max=2017.00, std=0.27
 - NUM_BO: média=297990.54, min=1.00, max=1673679.00, std=486262.60
 - DATAHORA_COMUNICACAO_BO: média=nan, min=nan, max=nan, std=nan

Faixa temporal detectada: 2016-01-01 00:00:00  →  2017-12-01 00:00:00

==============================
RESUMO TEXTUAL GLOBAL
==============================
Total de linhas (somadas): 2,395,054
Total de colunas únicas entre datasets: 31

Intervalos temporais por dataset:
 - RDO_1: 2010-01-01 00:00:00  →  2012-12-01 00:00:00
 - LONGITUDE: 242847
 - LATITUDE: 242411
 - NUM_BO: 217309
 - LOGRADOURO: 48152
 - NUMERO_LOGRADOURO: 8049
 - HORA_OCORRENCIA_BO: 1442
 - ID_DELEGACIA: 749
 - NOME_DELEGACIA: 749
 - DESCR_SUBTIPOLOCAL: 702
 - DATA_OCORRENCIA_BO: 397

Estatísticas básicas (primeiras 5 colunas numéricas):
 - ID_DELEGACIA: média=347226.41, min=10004.00, max=990900.00, std=428001.38
 - ANO_BO: média=2016.08, min=2016.00, max=2017.00, std=0.27
 - NUM_BO: média=297990.54, min=1.00, max=1673679.00, std=486262.60
 - DATAHORA_COMUNICACAO_BO: média=nan, min=nan, max=nan, std=nan

Faixa temporal detectada: 2016-01-01 00:00:00  →  2017-12-01 00:00:00

Intervalos temporais por dataset:
 - RDO_1: 2010-01-01 00:00:00  →  2012-12-01 00:00:00
 - RDO_2: 2013-01-01 00:00:00  →  2015-12-12 00:00:00
 - RDO_3: 2016-01-01 00:00:00  →  2017-12-01 00:00:00
 - RDO_2: 2013-01-01 00:00:00  →  2015-12-12 00:00:00
 - RDO_3: 2016-01-01 00:00:00  →  2017-12-01 00:00:00