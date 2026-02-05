📥 Importação de Estações e Medições via Excel

Este módulo adiciona ao sistema BDG a capacidade de importar estações gravimétricas e suas medições diretamente a partir de um arquivo Excel (.xlsx), permitindo o cadastro em lote de forma rápida e padronizada.

✅ Objetivo

A funcionalidade foi criada para facilitar:

Importação de várias medições de uma vez

Cadastro rápido de novas estações gravimétricas

Redução de erros manuais no preenchimento

Padronização do banco de dados

📌 Onde acessar no sistema

Após login como Operador ou Administrador, acesse:

http://127.0.0.1:8000/importar-excel/

⚙️ Como funciona

O usuário envia um arquivo .xlsx

O Django lê os dados usando pandas

Cada linha do Excel é transformada em um registro MedicaoGravimetrica

Ao final, o sistema exibe uma mensagem de sucesso ou erro

📂 Formato obrigatório do arquivo Excel

O arquivo deve conter uma planilha com as seguintes colunas exatamente com estes nomes:

Coluna	Obrigatória	Tipo esperado	Descrição
codigo_estacao	✅	texto	Código único da estação
nome_estacao	✅	texto	Nome identificador
latitude	✅	decimal	Latitude em graus decimais
longitude	✅	decimal	Longitude em graus decimais
valor_gravidade	✅	decimal	Valor gravimétrico medido
data_medicao	✅	data	Data no formato YYYY-MM-DD
🟡 Colunas opcionais suportadas

O sistema também aceita colunas extras, caso existam:

Coluna	Tipo	Descrição
altitude	decimal	Altitude da estação
incerteza	decimal	Incerteza associada à medição
operador	texto	Nome do operador
instrumento	texto	Instrumento utilizado
observacoes	texto	Observações gerais

Essas colunas são preenchidas automaticamente quando presentes.

📄 Exemplo de planilha válida

A planilha Excel deve conter dados como:

codigo_estacao,nome_estacao,latitude,longitude,valor_gravidade,data_medicao
STN-001,Base Planalto Central,-15.7942,-47.8822,978.0325,2026-01-10
STN-002,Encosta Litorânea,-23.5505,-46.6333,978.6512,2026-01-12
STN-003,Vale de Sedimentação,-3.1190,-60.0217,977.8456,2026-01-15

🧩 Dependências necessárias

Para que a importação funcione corretamente, o projeto precisa de:

pip install pandas openpyxl


No requirements.txt, garanta:

pandas
openpyxl
