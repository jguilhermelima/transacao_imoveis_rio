# Transação de Imóveis no Rio de Janeiro

Este repositório contém uma aplicação para análise de transações de imóveis no município do Rio de Janeiro, com base nos dados públicos do ITBI (Imposto sobre a Transmissão de Bens Imóveis).

# Fonte dos Dados
Os dados utilizados neste projeto foram obtidos a partir do portal [Data.Rio](https://www.data.rio/search?collection=dataset&groupIds=a6481110966e4559add86aa6c2b92b11&layout=grid), no conjunto de dados:

[ITBI - Transações por Logradouro e Mês - Imóveis Residenciais e Não Residenciais](https://www.data.rio/datasets/5e4dda4d33f44b1eb9246559b281d1b8_8/explore)

A extração dos dados foi realizada em 9 de novembro de 2026.

# Estrutura do Repositório
- dados/: Contém os arquivos de dados utilizados na aplicação.

- main.py: Código principal da aplicação (Streamlit).

- .streamlit/: Configurações da aplicação Streamlit.

# Como Executar
1. **Clone o repositório**
   ```bash
   git clone https://github.com/jguilhermelima/transacao_imoveis_rio.git   
2. **Instale as dependências necessárias**
    ```bash  
    pip install requirements.txt       
3. **Execute a aplicação**
    ```bash
   streamlit run main.py

# Observações
- Os dados refletem a situação das transações de imóveis no Rio de Janeiro conforme disponibilizados pelo portal Data.Rio na data de extração.

- Para mais informações sobre a metodologia e atualizações dos dados, consulte a página oficial do conjunto de dados no Data.Rio.

bash
streamlit run main.py
