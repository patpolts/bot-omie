# Bot Notas Omie

Bot de automação para o processo de **apuração de PIS/COFINS** sobre **notas fiscais eletrônicas de venda em marketplaces**, dentro do sistema **Omie**.  
Desenvolvido com **BotCity**, o bot acessa o Omie via navegador, identifica NF-es especificas, lê arquivo de xml em busca do valor da nota e processa os cálculos tributários automaticamente. Este bot foi desenvolvido em 2024 e utiliza sintaxe `xpath`, para uso atual com o sistema omie pode ser preciso atualizar caminhos e elementos buscados.
---  

## 🚀 Como rodar localmente  

### 1. Clonar o repositório
```bash
git clone https://github.com/patpolts/bot-omie.git
cd bot-omie  
```  

### 2. Configurar variáveis de ambiente  
```bash
Renomeie o arquivo .env_exemplo para .env  
Preencha os dados de login do Omie e da plataforma BotCity  
```

### 3. Instalar dependências  
```bash
pip install --upgrade -r requirements.txt
```  

### 4. Baixar o ChromeDriver e atualizar .env  
* Faça o download do driver mais recenete compatível com sua versão do Chrome:
https://googlechromelabs.github.io/chrome-for-testing/#stable  
* Extraia e copie o caminho do executável do ChromeDriver para a variavel no `.env`  

### 5. Executar o bot  
```bash
python bot.py
```  
> Ou use o modo Debug do VSCode com a configuração de ambiente Python.

## 🛠 Requisitos  
* Python
* Conta BotCity e projeto configurado  
* Acesso ao sistema Omie  
* Google Chrome instalado  

---  

## 👨‍💻 Autor  

> [Pati Poltts] – [me@poltts.com.br](mailto:me@poltts.com.br)  
> Desenvolvido como automação fiscal real para uma empresa do setor de e-commerce, utilizando BotCity e o sistema Omie.  