import os
# Import for the Web Bot
from botcity.web import WebBot, Browser, By, PageLoadStrategy
from botcity.web.browsers.chrome import default_options

from botcity.web.parsers import table_to_dict
from botcity.maestro import *
from dotenv import load_dotenv
from google.cloud import bigquery

from bs4 import BeautifulSoup
from datetime import datetime
from lxml import etree
import xmltodict
import json
import re

load_dotenv()

# Disable errors if we are not connected to Maestro
BotMaestroSDK.RAISE_NOT_CONNECTED = False


def main():
    maestro = BotMaestroSDK()
    # If you are not using Maestro, you can comment the next line
    maestro.login(server=f"{os.environ.get('BOT_SERVER')}",login=f"{os.environ.get('BOT_LOGIN')}", key=f"{os.environ.get('BOT_KEY')}")
    maestro = BotMaestroSDK.from_sys_args()
    ## Fetch the BotExecution with details from the task, including parameters
    execution = maestro.get_execution()
    
    print(f">>> Task ID is: {execution.task_id}")
    print(f">>> Task Parameters are: {execution.parameters}")
    print(">>> Iniciando Bot <<<")

    bot = WebBot()
    # Configure whether or not to run on headless mode
    bot.headless = False
    
    def_options = default_options(
            headless=bot.headless,
            download_folder_path=bot.download_folder_path,
            user_data_dir=None,  # Informing None here will generate a temporary directory
            page_load_strategy=PageLoadStrategy.NORMAL
    )
    # Customized arguments
    def_options.add_argument("--disable-popup-blocking")
    def_options.add_argument("--disable-web-security")

    bot.options = def_options
    # Set the browser to use
    # You can use Browser.CHROME, Browser.FIREFOX, Browser.EDGE, Browser.SAFARI, Browser.OPERA, Browser.IE
    bot.browser = Browser.CHROME
    # Set the path to the ChromeDriver executable
    bot.driver_path = f'{os.environ.get("")}'

    print(">>> Iniciando Processos <<<")

    # Opens the omie website.
    bot.browse("https://app.omie.com.br/login/")

    #OMIE Login credentials
    login_email = os.environ.get('LOGIN_EMAIL')
    login_password = os.environ.get('LOGIN_PASSWORD')

    if not login_email or not login_password:
        raise Exception(f"Erro ao obter dados de login omie")

    bot.wait(500)

    #Search for the email input field and fill it with the login email 
    field_user_email = bot.find_element('//input[@placeholder = "Digite seu endereço de e-mail"]', By.XPATH)

    if not field_user_email:
        raise Exception(f"Erro ao localizar campo de email, o bot precisa ser atualizado para a nova versão do Omie")

    bot.wait(6000)
    # Fill the email input field with the login email
    field_user_email.send_keys(login_email)

    bot.wait(3000) 

    # Search for the continue button and click it
    btn_continue = bot.find_element('//button[@id="btn-continue"]', By.XPATH)
    
    if btn_continue:
        btn_continue.click()
    else:
        raise Exception(f"Erro ao localizar botão continuar, o bot precisa ser atualizado para a nova versão do Omie")
    
    bot.wait(3000)

    # Search for the password input field... 
    field_user_password = bot.find_element('//input[@type="password"]', By.XPATH)
    bot.wait(500)
    #fill it with the login password
    field_user_password.send_keys(login_password)

    bot.wait(3000)

    # Search for the login button and click it
    btn_login = bot.find_element('//button[@id="btn-login"]', By.XPATH)
    btn_login.click()
    
    print(">>> Login OK <<<")
    bot.wait(6000)

    #check if the user has a dialog box open an close it
    btn_indicacao = bot.find_element('//div[@aria-label="Fechar diálogo"]',By.XPATH)
    if btn_indicacao:
        btn_indicacao.click()
        bot.wait(1000)
    
    # Search for the button to access the system and click it
    btn_system = bot.find_element('//button[text()="Acessar"]', By.XPATH)
    bot.wait(3000)
    btn_system.click()
    
    print(">>> Acessando o sistema <<<")
    bot.wait(6000)

    #Get the current tabs opened and set the second tab as the active tab
    # This is necessary because the Omie system opens a new tab after login
    opened_tabs = bot.get_tabs()
    new_tab = opened_tabs[1]

    if new_tab:
        bot.activate_tab(new_tab)
    else:
        print("Erro inesperado")

    bot.wait(8000)

    # Check if the popup for notifications is open and close it
    btn_popup = bot.find_element('//button[@id="onesignal-slidedown-cancel-button"]',By.XPATH)
    btn_popup.click()

    bot.wait(3000)

    # Search for the button to access the "Gerenciando suas compras..." section and click it
    btn_compras = bot.find_element('//li[@data-desc="Gerenciando suas compras, estoque e suas ordens de produção"]//a',By.XPATH) 
    bot.wait(500)
    
    if not btn_compras:
        raise Exception(f"Erro ao localizar elemento, o bot precisa ser atualizado para a nova versão do Omie")

    btn_compras.click()
    bot.wait(4000)

    # Search for the button to access the "Cadastrar Compras e Receber" section and click it or raise a error
    btn_cadastrar_compras_receber = bot.find_element('//a[./descendant::h2[contains(text(),"Cadastrar Compras e Receber")]]',By.XPATH)
    bot.wait(500)
    
    if not btn_cadastrar_compras_receber:
        raise Exception(f"Erro ao localizar elemento, o bot precisa ser atualizado para a nova versão do Omie")

    btn_cadastrar_compras_receber.click()

    bot.wait(1000)

    # Search for the button to access the "CT-e Faturados" section and click it or raise a error
    lista_faturados_fornecedor = bot.find_element('//div[@data-list-id="2004"]//h3//div[contains(@class, "oLink")]',By.XPATH)
    bot.wait(1000)
    
    if lista_faturados_fornecedor:
        lista_faturados_fornecedor.click()
    else: 
        raise Exception(f"Click erro, elemento não clicavel, o bot precisa ser atualizado para a nova versão do Omie")
    
    bot.wait(3000)

    # Search for the input field to filter by operation and fill it with 'CT'
    # This is necessary to filter the results to only show CT-e Faturados
    field_operacao = bot.find_element('//td[contains(@class, "OPERACAO")]//input',By.XPATH)
    bot.wait(3000)
    field_operacao.clear()
    field_operacao.send_keys('CT')
    bot.enter()
    bot.wait(3000)

    #Find the table with the results of the CT-e Faturados
    tabela_resultado = bot.find_element('table#d50651c10000g', By.CSS_SELECTOR)

    if tabela_resultado:
        # Get the HTML content of the table
        html_tabela = tabela_resultado.get_attribute('outerHTML')

        # Use BeautifulSoup to parse the HTML content
        soup = BeautifulSoup(html_tabela, 'html.parser')

        # Find all rows in the table
        linhas_tabela = soup.find_all('tr')
       
        #Extract data from the table
        dados_tabela = []

        # Loop through each row and extract the data
        for linha in linhas_tabela:
            data_id = linha.get('data-id')

            colunas = linha.find_all(['th', 'td'])

            dados_linha = {
                'data_id': data_id,
                'dados': [coluna.text.strip() for coluna in colunas]
            }

            dados_tabela.append(dados_linha)

        bot.wait(1000)

        # Check if there are any results in the table
        for linha in dados_tabela:
            log_data = []
            operacao = ""
            emitente = ""
            valorTotal = 0
            cfop = ""
            situacao = ""
            calculoBase = ""
            aliquotas = ""
            
            print(">>> ... ",linha['dados'][1])

            #Find the note to be processed if status is "Aguardando Entrega"
            #And process it
            #If error occurs in this process th bopt needs to be updated to the latest version of Omie
            if linha['dados'][1] == "Aguardando Entrega":                
                print(">>> Nota a ser processada encontrada")
                elemento_id = linha['data_id']

                print("Linha: ", elemento_id)

                xpath_linha = f'//tr[@data-id="{elemento_id}"]'
                elemento_linha = bot.find_element(xpath_linha,By.XPATH)
                
                bot.set_current_element(elemento_linha)
                bot.wait(4000)
                if not elemento_linha:
                    continue
                else:
                    try:
                        elemento_linha.click()
                        bot.wait(1000)
                        bot.enter()
                    except:
                        continue
                bot.wait(3000)

                campo_situacao_tributaria = bot.find_element('//input[@tabindex="141"]',By.XPATH)
                valor_campo_situacao_tributaria = campo_situacao_tributaria.get_attribute('value')

                if valor_campo_situacao_tributaria:
                    check_valor_campo_situacao_tributaria = valor_campo_situacao_tributaria.split()[0]
                    #se situação for 00
                    if check_valor_campo_situacao_tributaria == "00":
                        operacao = linha['dados'][2]
                        emitente = linha['dados'][3]
                        valorTotal = linha['dados'][4]
                        situacao = valor_campo_situacao_tributaria

                        print(f'Passou nas condições: {valor_campo_situacao_tributaria}')

                        campo_cfop_cte = bot.find_element('//input[@id="d50651c197"]', By.XPATH)

                        if campo_cfop_cte: 
                            valor_campo_cfop_cte = campo_cfop_cte.get_attribute('value')

                            campo_cfop_entrada = bot.find_element('//input[@id="d50651c201"]',By.XPATH)
                            campo_cfop_entrada.clear()
                            btn_busca_campo_cfop_cte = bot.find_element('//div[@data-cid="201"]//span[@title="Mostrar lista"]',By.XPATH)
                            btn_busca_campo_cfop_cte.click()

                            bot.wait(1000)

                            campo_busca_cfop_cte = bot.find_element('//input[@id="dynamicSearchText"]',By.XPATH)

                            bot.wait(500)

                            check_campo_cfop_cte = valor_campo_cfop_cte.split()[0]

                            if check_campo_cfop_cte == "5.353":
                                campo_busca_cfop_cte.send_keys("1.353")
                                cfop = "1.353"
                                
                                bot.wait(1000)
                                bot.enter()
                                bot.wait(3000)

                                resultado_busca = bot.find_element('//a[contains(text(),"1.353")]',By.XPATH)

                                if not resultado_busca:
                                    print("resultado não encontrado")
                                    
                                resultado_busca.click()
                                bot.wait(1000)

                            elif check_campo_cfop_cte == "6.353":
                                campo_busca_cfop_cte.send_keys("2.353")
                                cfop = "2.353"

                                bot.wait(1000)
                                bot.enter()
                                bot.wait(1000)

                                resultado_busca = bot.find_element('//a[contains(text(),"2.353")]',By.XPATH)

                                if not resultado_busca:
                                    print("resultado não encontrado")
                                    
                                resultado_busca.click()
                                bot.wait(3000)

                            check_valor_campo_cfop_cte = campo_cfop_entrada.get_attribute('value')
                            # print(check_valor_campo_cfop_cte)
                            if check_valor_campo_cfop_cte:
                                print('>>> Campo CFOP CTE Preenchido <<<')
                                bot.wait(1000)

                            print('Confirmando não gerar uma conta a pagar para este recebimento...')
                            bot.wait(1000)

                            confirma_nao_gerar_conta_para_recebimento = bot.find_element('//a[@data-cid="225"]',By.XPATH)
                            bot.wait(500)
                            confirma_clicked = bot.find_element('//a[@data-cid="225"]/span[2]/div[@style="display: inline-block; color: rgb(255, 0, 0);"]',By.XPATH)
                            
                            if not confirma_clicked:
                                confirma_nao_gerar_conta_para_recebimento.click()
                                print('>>> Confirmado não gerar conta a pagar <<<')

                            bot.wait(1000)

                            print(">>> Informações Adicionais <<<")
                            link_informacoes_adicionais = bot.find_element('//a[text()="Informações Adicionais"]',By.XPATH)
                            bot.wait(1000)
                            link_informacoes_adicionais.click()

                            bot.wait(1000)
                            hoje = datetime.now()
                            hoje_formatado = hoje.strftime("%d/%m/%Y")
                            
                            print("...Definindo data de registro para hoje",hoje_formatado)
                        

                            campo_data_registro = bot.find_element('//input[@id="d50651c255"]',By.XPATH)
                            bot.wait(1000)
                            campo_data_registro.clear()
                            campo_data_registro.click()
                            campo_data_registro.send_keys(hoje_formatado)
                            bot.wait(3000)    
                            print(campo_data_registro.get_attribute('value'))
                            
                            print(">>> Concluido informações adicionais <<<")
                            print(">>> Voltando para CFOP <<<")

                            link_cfop_entrada = bot.find_element('//a[text()="CFOP de Entrada e Mais Detalhes"]',By.XPATH)
                            bot.wait(1000)
                            link_cfop_entrada.click()
                            bot.wait(3000)

                            print(">>> Indo para XML do CT-e <<<")
                            bot.wait(3000)
                            link_exibir_dacte = bot.find_element('//ul[@data-did="50651"]//a[./descendant::div[contains(text(),"XML")]]',By.XPATH)
                            link_exibir_dacte.click()

                            bot.wait(3000)
                            opened_tabs = bot.get_tabs()
                            new_tab_2 = opened_tabs[2]
                            bot.activate_tab(new_tab_2)

                            bot.wait(3000)
                            bot.control_a()
                            bot.wait(3000)
                            bot.control_c()
                            bot.wait(1000)

                            pagina_string = bot.get_clipboard()
                            bot.wait(1000)
                            xml_string = pagina_string.replace('This XML file does not appear to have any style information associated with it. The document tree is shown below.', '')
                            bot.wait(3000)
                            xml_data = get_xml_data(xml_string)
                            bot.wait(3000)
                            
                            if xml_data['valor_base'] and xml_data['valor_icms'] != 0 :
                                print(">>> Valores BAse Calculo e ICMS obtidos com sucesso <<<")
                                print("...Fechando Aba")
                                bot.close_page()
                                bot.wait(1000)                
                                bot.activate_tab(new_tab)
                            #Se os valores não forem obtidos fecha a aba, sai da nota e segue para a proxima linha
                            else: 
                                print(">>> Erro inesperado ocorreu, impossivel continuar com o processo <<<")
                                print("...Fechando Aba")
                                bot.close_page()
                                bot.wait(1000)                
                                bot.activate_tab(new_tab)
                                print(">>> Seguindo para a proxima linha <<<")
                        
                                bot.wait(1000)
                                btn_voltar = bot.find_element('//button[@title="Voltar"]',By.XPATH)
                                btn_voltar.click()
                                bot.wait(1000)
                                continue


                            
                            bot.wait(1000)
                            print(">>> Iniciando modificação de situação tributaria do CT-e <<<")
                            link_modificar_situacao_tributaria = bot.find_element('//a[@data-cid="216"]',By.XPATH)
                            link_modificar_situacao_tributaria.click()
                            bot.wait(1000)

                            campo_situacao_tributaria_pis = bot.find_element('//span[@title="Situação Tributária do PIS"]/span[1]/input',By.XPATH)
                            campo_situacao_tributaria_pis_btn = bot.find_element('//span[@title="Situação Tributária do PIS"]/span[1]/span[@title="Limpar valor"]',By.XPATH)

                            campo_situacao_tributaria_cofins = bot.find_element('//span[@title="Situação Tributária do COFINS"]/span[1]/input',By.XPATH)
                            campo_situacao_tributaria_cofins_btn = bot.find_element('//span[@title="Situação Tributária do COFINS"]/span[1]/span[@title="Limpar valor"]',By.XPATH)
                            
                            bot.wait(4000)
                            print(">>> Definindo situação tributaria PIS <<<")

                            campo_situacao_tributaria_pis_btn.click()
                            bot.wait(1000)
                            campo_situacao_tributaria_pis.send_keys("50")
                            bot.wait(1000)
                            bot.set_current_element(campo_situacao_tributaria_pis)
                            bot.enter()

                            bot.wait(4000)
                            print(">>> Definindo situação tributaria COFINS <<<")

                            campo_situacao_tributaria_cofins_btn.click()
                            bot.wait(1000)
                            campo_situacao_tributaria_cofins.send_keys("50")
                            bot.wait(1000)
                            bot.set_current_element(campo_situacao_tributaria_cofins)
                            bot.enter()

                            print(">>> PIS e COFINS definidos <<<")
                            print(">>> Seguindo para a base de calculo <<<")
                            bot.wait(1000)
                            base_calculo = xml_data['valor_base'] - xml_data['valor_icms']
                            base_calculo_formatado = str(base_calculo).replace(".",",")
                            calculoBase = base_calculo_formatado
                            
                            # print("Base calculo: ",base_calculo_formatado)
                            bot.wait(1000)
                            if base_calculo > 0:
                                aliquotas = "1,65/7,60"

                                campo_calculo_pis = bot.find_element('//input[@id="d51037c22"]',By.XPATH)
                                campo_calculo_cofins = bot.find_element('//input[@id="d51037c32"]',By.XPATH)
                                campo_aliquota_pis = bot.find_element('//input[@id="d51037c23"]',By.XPATH)
                                campo_aliquota_cofins = bot.find_element('//input[@id="d51037c33"]',By.XPATH)

                                bot.wait(1000)
                                # print(base_calculo)
                                print(">>> Definindo dados PIS <<<")
                                campo_calculo_pis.clear()
                                bot.wait(500)
                                campo_calculo_pis.send_keys(base_calculo_formatado)
                                bot.tab()
                                bot.wait(1000)

                                campo_aliquota_pis.send_keys("1,65")
                                bot.tab()
                                bot.wait(1000)

                                print(">>> Definindo dados COFINS <<<")
                                campo_calculo_cofins.clear()
                                bot.wait(500)
                                campo_calculo_cofins.send_keys(base_calculo_formatado)
                                bot.tab()
                                bot.wait(1000)

                                campo_aliquota_cofins.send_keys("7,60")
                                bot.tab()
                                bot.wait(1000)

                                print(">>> Base Calculo definidos <<<")
                                bot.wait(1000)

                                btn_salvar_fechar = bot.find_element('//button[@data-cid="36"]',By.XPATH)
                                btn_salvar_fechar.click()
                                bot.wait(3000)
                                print(">>> Modificação tributaria do CT-e concluida")
                                bot.wait(1000)
                                print(">>> pronto pra concluir")

                                link_concluir = bot.find_element('//ul[@data-did="50651"]//a[./descendant::div[contains(text(),"Concluir")]]',By.XPATH)
                                bot.wait(500)
                                link_concluir.click()

                                bot.wait(3000)

                                btn_confirma_concluir = bot.find_element('//button[contains(text(),"Sim")]',By.XPATH)
                                bot.wait(500)
                                btn_confirma_concluir.click()

                                bot.wait(3000)
                                btn_confirma_concluir_2 = bot.find_element('//button[contains(text(),"Sim")]',By.XPATH)
                                bot.wait(3000)
                                if btn_confirma_concluir_2:
                                    btn_confirma_concluir_2.click()

                                print(">>> Concluido")
                                print(">>> Seguindo para o proximo")

                        bot.wait(4000)
                    #se situação for 40
                    elif check_valor_campo_situacao_tributaria == "40":
                        operacao = linha['dados'][2]
                        emitente = linha['dados'][3]
                        valorTotal = linha['dados'][4]
                        situacao = valor_campo_situacao_tributaria
                                                
                        campo_cfop_cte = bot.find_element('//input[@id="d50651c197"]', By.XPATH)
                        if campo_cfop_cte: 
                            valor_campo_cfop_cte = campo_cfop_cte.get_attribute('value')

                            campo_cfop_entrada = bot.find_element('//input[@id="d50651c201"]',By.XPATH)
                            campo_cfop_entrada.clear()
                            btn_busca_campo_cfop_cte = bot.find_element('//div[@data-cid="201"]//span[@title="Mostrar lista"]',By.XPATH)
                            btn_busca_campo_cfop_cte.click()

                            bot.wait(1000)

                            campo_busca_cfop_cte = bot.find_element('//input[@id="dynamicSearchText"]',By.XPATH)

                            bot.wait(1000)

                            check_campo_cfop_cte = valor_campo_cfop_cte.split()[0]

                            if check_campo_cfop_cte == "5.353":
                                cfop = "1.353"
                                campo_busca_cfop_cte.send_keys("1.353")

                                bot.wait(1000)
                                bot.enter()
                                bot.wait(3000)

                                resultado_busca = bot.find_element('//a[contains(text(),"1.353")]',By.XPATH)

                                if not resultado_busca:
                                    print("resultado não encontrado")
                                    
                                resultado_busca.click()
                                bot.wait(1000)

                            elif check_campo_cfop_cte == "6.353":
                                cfop = "2.353"
                                campo_busca_cfop_cte.send_keys("2.353")

                                bot.wait(1000)
                                bot.enter()
                                bot.wait(1000)

                                resultado_busca = bot.find_element('//a[contains(text(),"2.353")]',By.XPATH)

                                if not resultado_busca:
                                    print("resultado não encontrado")
                                    
                                resultado_busca.click()
                                bot.wait(3000)

                            check_valor_campo_cfop_cte = campo_cfop_entrada.get_attribute('value')
                            # print(check_valor_campo_cfop_cte)
                            if check_valor_campo_cfop_cte:
                                print('>>> Campo CFOP CTE Preenchido <<<')
                                bot.wait(1000)
                        
                        bot.wait(3000)
                        confirma_nao_gerar_conta_para_recebimento = bot.find_element('//a[@data-cid="225"]',By.XPATH)
                        bot.wait(1000)
                        confirma_clicked = bot.find_element('//a[@data-cid="225"]/span[2]/div[@style="display: inline-block; color: rgb(255, 0, 0);"]',By.XPATH)
                        
                        if not confirma_clicked:
                            confirma_nao_gerar_conta_para_recebimento.click()
                            print('>>> Confirmado não gerar conta a pagar <<<')

                        bot.wait(3000)

                        print(">>> Informações Adicionais <<<")
                        link_informacoes_adicionais = bot.find_element('//a[text()="Informações Adicionais"]',By.XPATH)
                        bot.wait(1000)
                        link_informacoes_adicionais.click()
                        hoje = datetime.now()
                        hoje_formatado = hoje.strftime("%d/%m/%Y")
                        
                        print("...Definindo data de registro para hoje",hoje_formatado)

                        campo_data_registro = bot.find_element('//input[@id="d50651c255"]',By.XPATH)
                        bot.wait(1000)
                        campo_data_registro.clear()
                        campo_data_registro.click()
                        campo_data_registro.send_keys(hoje_formatado)
                        bot.wait(3000)    
                        print(campo_data_registro.get_attribute('value'))
                        
                        print(">>> Concluido informações adicionais <<<")
                        bot.wait(1000)

                        print(">>> pronto pra concluir")

                        link_concluir = bot.find_element('//ul[@data-did="50651"]//a[./descendant::div[contains(text(),"Concluir")]]',By.XPATH)
                        bot.wait(500)
                        link_concluir.click()

                        bot.wait(3000)

                        btn_confirma_concluir = bot.find_element('//button[contains(text(),"Sim")]',By.XPATH)
                        bot.wait(500)
                        if btn_confirma_concluir:
                            btn_confirma_concluir.click()

                        bot.wait(3000)

                        btn_confirma_concluir_2 = bot.find_element('//button[contains(text(),"Sim")]',By.XPATH)
                        bot.wait(3000)

                        if btn_confirma_concluir_2:
                            btn_confirma_concluir_2.click()

                        print(">>> Concluido")
                        print(">>> Seguindo para o proximo")
                        
                    else:
                        log_label="naoprocessados"

                        print('Não passou nas condições: ',valor_campo_situacao_tributaria)
                        print(">>> Seguir para a proxima linha <<<")
                        
                        operacao   = linha['dados'][2]
                        emitente   = linha['dados'][3]
                        valorTotal = linha['dados'][4]
                        situacao   = valor_campo_situacao_tributaria
                        
                        bot.wait(1000)
                        btn_voltar = bot.find_element('//button[@title="Voltar"]',By.XPATH)
                        
                        if btn_voltar:
                            btn_voltar.click()
                        
                        bot.wait(1000)

                        continue
                    #if using logs
                    # print(">>> Salvando Log <<<")
                    # v = re.sub(r'[^\d.]', '', valorTotal)
                    # log_data = [{
                    #     "Operacao": operacao,
                    #     "Emitente": emitente,
                    #     "ValorTotal": float(v),
                    #     "CFOP": cfop,
                    #     "Situacao": situacao,
                    #     "CalculoBase": calculoBase,
                    #     "Aliquotas": aliquotas,
                    #     "Data": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # }]
                    # errors = client.insert_rows_json(f"{project_id}.{dataset_id}.{table_id}", log_data)
                    # if errors == []:
                    #     print(">>> Log salvo")
                    # else:
                    #     print("Erros ao salvar log:")
                    #     for error in errors:
                    #         print(error)
                    # maestro.new_log_entry(activity_label=log_label,values = log_data)
                    
                else:
                    print(">>> Campo situação tributaria vazio")
                    print(">>> Seguir para a proxima linha")
                    
                    bot.wait(1000)
                    btn_voltar = bot.find_element('//button[@title="Voltar"]',By.XPATH)
                    
                    if btn_voltar:
                        btn_voltar.click()

                    bot.wait(1000)
                    continue
            # If the status is not "Aguardando Entrega", print a message and continue to the next row
            else:
                print(">>> ... Nada para fazer")
                
        print(">>> Finalizando... <<<")
        btn_voltar = bot.find_element('//button[@title="Voltar"]',By.XPATH)
        bot.wait(3000)

        if btn_voltar: 
            btn_voltar.click()
            bot.wait(3000)
    else:
        print("Nenhuma CT encontrada") 
        bot.wait(1000)
        btn_voltar = bot.find_element('//button[@title="Voltar"]',By.XPATH)
        if btn_voltar:
            btn_voltar.click()
    
    # Wait 3 seconds before closing
    print(">>> fechando browser...")
    bot.wait(3000)

    # Finish and clean up the Web Browser
    # You MUST invoke the stop_browser to avoid
    # leaving instances of the webdriver open
    bot.stop_browser()

    # Uncomment to mark this task as finished on BotMaestro
    maestro.finish_task(
        task_id=execution.task_id,
        status=AutomationTaskFinishStatus.SUCCESS,
        message="Task Finished OK."
    )


    bot.wait(500)

# Function to extract XML data from a note file 
def get_xml_data(xml_string):
    retorno = {}
    html_parser = etree.HTMLParser()
    root = etree.fromstring(xml_string,parser=html_parser)
    xml_dict = xmltodict.parse(etree.tostring(root))
    json_str = json.dumps(xml_dict, indent=2)
    json_data = json.loads(json_str)
    vbc_value = json_data["html"]["body"]["cteproc"]["cte"]["infcte"]["imp"]["icms"]["icms00"]["vbc"]
    vicms_value = json_data["html"]["body"]["cteproc"]["cte"]["infcte"]["imp"]["icms"]["icms00"]["vicms"]
    
    if vbc_value:
        retorno = {'valor_base': float(vbc_value)}
    else:
        print(">>> Elemento vBC não encontrado no XML <<<")

    if vicms_value:
        retorno.update({'valor_icms': float(vicms_value)})
    else:
        print(">>> Elemento vICMS não encontrado no XML <<")
    
    if retorno['valor_base'] and retorno['valor_icms']:
        print(retorno)
        return retorno
    else:
        return


def executa_rotina_fiscal_faturado_fornecedor(lista):
   print(lista)


def trata_tabela_resultados(elemento): 
    # Supondo que você tenha o conteúdo HTML da tabela
    html_tabela = elemento.get_attribute('outerHTML')

    # Use o BeautifulSoup para analisar o HTML
    soup = BeautifulSoup(html_tabela, 'html.parser')

    # Encontre todas as linhas da tabela
    linhas_tabela = soup.find_all('tr')

    # Extrair dados da tabela
    dados_tabela = []

    for linha in linhas_tabela:
        # Obtenha o atributo data-id da linha
        data_id = linha.get('data-id')

        # Encontre todas as colunas (th ou td) na linha
        colunas = linha.find_all(['th', 'td'])

        # Extrair texto de cada coluna
        dados_linha = {
            'data_id': data_id,
            'dados': [coluna.text.strip() for coluna in colunas]
        }

        dados_tabela.append(dados_linha)
        return dados_tabela

def not_found(label):
    print(f"Element not found: {label}")


if __name__ == '__main__':
    main()
