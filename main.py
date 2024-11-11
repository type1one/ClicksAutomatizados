import tkinter as tk
from tkinter import simpledialog, scrolledtext
import pickle
import os
import pyautogui
import keyboard
import pynput.mouse as mouse
import time
import threading

DIR = "arquivos"

if not os.path.exists(DIR):
    os.makedirs(DIR)

hotkeys = []

def logar(mensagem, cor="black"):
    if mensagem not in mensagem_exibida:
        log_text.tag_configure("green", foreground="green")
        log_text.tag_configure("red", foreground="red")
        log_text.tag_configure("default", foreground="black")
        
        tag_cor = "default"
        if cor == "green":
            tag_cor = "green"
        elif cor == "red":
            tag_cor = "red"
        
        log_text.insert(tk.END, mensagem + "\n", tag_cor)
        log_text.yview(tk.END)
        mensagem_exibida.add(mensagem)

def centralizar_janela(root, largura_janela, altura_janela):
    largura_tela = root.winfo_screenwidth()
    altura_tela = root.winfo_screenheight()
    pos_x = int((largura_tela - largura_janela) / 2)
    pos_y = int((altura_tela - altura_janela) / 2)
    root.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")

def atualizar_status():
    status = "Ligado" if automacao_ativa else "Desligado"
    status_label.config(text=f"Status: {status}", fg="green" if automacao_ativa else "red")
    arquivo_atual_label.config(text=f"Arquivo atual: {arquivo_selecionado_atual}" if arquivo_selecionado_atual else "Arquivo atual: Nenhum")

def bloquear_botoes():
    btn_criar_novo.config(state=tk.DISABLED)
    btn_abrir_bd.config(state=tk.DISABLED)
    btn_iniciar.config(state=tk.DISABLED)

def desbloquear_botoes():
    btn_criar_novo.config(state=tk.NORMAL)
    btn_abrir_bd.config(state=tk.NORMAL)
    btn_iniciar.config(state=tk.NORMAL)
    btn_parar_automacao.grid_forget()

def remover_teclas():
    global hotkeys
    for hotkey in hotkeys:
        keyboard.remove_hotkey(hotkey)
    hotkeys.clear()

def resetar_interface():
    global automacao_ativa, precisa_reiniciar, mensagem_exibida, arquivo_selecionado_atual
    automacao_ativa = False
    precisa_reiniciar = False
    arquivo_selecionado_atual = None
    mensagem_exibida.clear()
    log_text.delete("1.0", tk.END)
    atualizar_status()
    inicializar_interface()
    logar("Programa reiniciado. Pronto para uso.", cor="green")
    remover_teclas()  

def inicializar_interface():
    desbloquear_botoes()
    atualizar_status()
    contador_button.config(text="Clicks: 0 de 0")
    logar("Olá! Arquivo iniciado com sucesso. Selecione uma das opções para dar continuidade com a automação.", cor="black")

def painel_principal():
    global btn_criar_novo, btn_abrir_bd, btn_iniciar, log_text, automacao_ativa, precisa_reiniciar, contador_button, status_label, btn_parar_automacao, mensagem_exibida, arquivo_selecionado_atual, arquivo_atual_label

    arquivo_selecionado_atual = None  

    def criar_novo():
        nome = simpledialog.askstring("Nome", "Coloque o nome que será salvo após realizar as coordenadas")
        if not nome:
            return

        logar("Pressione DEL para iniciar a monitoração de cliques e END para finalizar.")

        cliques = []
        running = False

        def start():
            nonlocal running
            running = True
            logar("Monitoração de cliques iniciada. Clique para capturar coordenadas.")

        def stop():
            nonlocal running
            running = False
            logar("Monitoração de cliques finalizada.")
            with open(os.path.join(DIR, nome + '.pkl'), 'wb') as f:
                pickle.dump(cliques, f)
            logar(f"Coordenadas salvas como {nome}!")

        def on_click(x, y, button, pressed):
            if running and pressed:
                logar(f"Coordenadas: x={x}, y={y}")
                cliques.append((x, y))

        keyboard.add_hotkey('del', start)
        keyboard.add_hotkey('end', stop)

        mouse_listener = mouse.Listener(on_click=on_click)
        mouse_listener.start()

    def abrir_bd():
        arquivos = os.listdir(DIR)
        if arquivos:
            logar("Arquivos salvos:")
            for arquivo in arquivos:
                logar(arquivo)
        else:
            logar("Nenhum arquivo encontrado.")

    def iniciar():
        global arquivo_selecionado_atual, automacao_ativa

        arquivos = os.listdir(DIR)
        if not arquivos:
            logar("Erro: Nenhum arquivo disponível para iniciar.")
            return

        selecionado = simpledialog.askstring("Seleção", f"Escolha um arquivo: {', '.join(arquivos)}")
        if not selecionado:
            return

        if not selecionado.endswith('.pkl'):
            selecionado += '.pkl'

        if not os.path.exists(os.path.join(DIR, selecionado)):
            logar("Erro: Arquivo inválido!")
            return

        if arquivo_selecionado_atual is not None and automacao_ativa:
            logar(f"Interrompendo {arquivo_selecionado_atual} para iniciar o novo arquivo.", cor="red")
            parar_automacao()  

        arquivo_selecionado_atual = selecionado
        atualizar_status()  

        with open(os.path.join(DIR, selecionado), 'rb') as f:
            coordenadas = pickle.load(f)

        logar(f"Arquivo {selecionado} carregado. Escolha a velocidade para iniciar os cliques.")

        global precisa_reiniciar
        automacao_ativa = False
        precisa_reiniciar = False

        def configurar_cliques(intervalo):
            global precisa_reiniciar
            precisa_reiniciar = False
            logar(f"Configuração concluída com intervalo de {intervalo} segundos. Pressione INSERT para iniciar e HOME para pausar.", cor="green")
            logar(f"AVISO: CADA VEZ QUE A TECLA INSERT FOR PRESSIONADA, CADA VEZ MAIS OS CLIQUES SERÃO MAIS RÁPIDOS..", cor="yellow")
            bloquear_botoes()
            btn_parar_automacao.grid(row=2, column=1, padx=5, pady=5)

            btn_rapida.grid_remove()
            btn_media.grid_remove()
            btn_lenta.grid_remove()

            def executar_cliques():
                global automacao_ativa, precisa_reiniciar
                automacao_ativa = True
                total_cliques = len(coordenadas)
                cliques_realizados = 0
                atualizar_status()

                while automacao_ativa:
                    for x, y in coordenadas:
                        if not automacao_ativa:
                            return
                        if keyboard.is_pressed('home'):
                            parar_automacao()
                            return
                        pyautogui.click(x, y)
                        cliques_realizados += 1
                        contador_button.config(text=f"Clicks: {cliques_realizados} de {total_cliques}")
                        time.sleep(intervalo)
                        if cliques_realizados >= total_cliques:
                            cliques_realizados = 0 

                logar("Execução de cliques finalizada.", cor="red")
                desbloquear_botoes()
                atualizar_status()

            remover_teclas()  
            hotkeys.append(keyboard.add_hotkey('insert', lambda: threading.Thread(target=executar_cliques, daemon=True).start()))
            hotkeys.append(keyboard.add_hotkey('home', parar_automacao))

        btn_rapida = tk.Button(root, text="Rápida", command=lambda: configurar_cliques(0.1))
        btn_media = tk.Button(root, text="Média", command=lambda: configurar_cliques(2.0))
        btn_lenta = tk.Button(root, text="Lenta", command=lambda: configurar_cliques(5.0))

        btn_rapida.grid(row=3, column=0, padx=5, pady=5)
        btn_media.grid(row=3, column=1, padx=5, pady=5)
        btn_lenta.grid(row=3, column=2, padx=5, pady=5)

    def parar_automacao():
        global automacao_ativa, precisa_reiniciar, arquivo_selecionado_atual
        automacao_ativa = False
        precisa_reiniciar = True
        arquivo_selecionado_atual = None
        logar("Automação interrompida pelo usuário.", cor="red")
        desbloquear_botoes()
        atualizar_status()
        remover_teclas()  

    root = tk.Tk()
    root.title("Cliques Automáticos")

    root.resizable(False, False)

    largura_janela = 500
    altura_janela = 400
    centralizar_janela(root, largura_janela, altura_janela)

    btn_frame = tk.Frame(root)
    btn_frame.grid(row=0, column=0, columnspan=3)

    btn_criar_novo = tk.Button(btn_frame, text="1 - Criar nova função de clique", command=criar_novo)
    btn_criar_novo.grid(row=0, column=0, padx=5, pady=10)

    btn_abrir_bd = tk.Button(btn_frame, text="2 - Abrir banco de dados", command=abrir_bd)
    btn_abrir_bd.grid(row=0, column=1, padx=5, pady=10)

    btn_iniciar = tk.Button(btn_frame, text="3 - Qual você vai iniciar?", command=iniciar)
    btn_iniciar.grid(row=0, column=2, padx=5, pady=10)

    mensagem_exibida = set()
    log_text = scrolledtext.ScrolledText(root, width=60, height=15, state=tk.NORMAL)
    log_text.grid(row=1, column=0, columnspan=3)

    automacao_ativa = False
    precisa_reiniciar = False
    status_label = tk.Label(root, text="Status: Desligado", fg="red")
    status_label.grid(row=2, column=0, padx=5, pady=5)

    arquivo_atual_label = tk.Label(root, text="Arquivo atual: Nenhum", fg="blue")
    arquivo_atual_label.grid(row=4, column=1, padx=5, pady=5)

    btn_parar_automacao = tk.Button(root, text="Parar Automação", command=parar_automacao)
    contador_button = tk.Label(root, text="Clicks: 0 de 0")
    contador_button.grid(row=2, column=2, padx=5, pady=5)

    inicializar_interface()
    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()

painel_principal()
