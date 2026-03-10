import turtle as t
import functools
import random


LARGURA_JANELA = 1024
ALTURA_JANELA = 600
METADE_ALTURA_JANELA = ALTURA_JANELA/2
METADE_LARGURA_JANELA = LARGURA_JANELA/2
DEFAULT_TURTLE_SIZE = 40
DEFAULT_TURTLE_SCALE = 3
RAIO_JOGADOR = DEFAULT_TURTLE_SIZE / DEFAULT_TURTLE_SCALE
RAIO_BOLA = DEFAULT_TURTLE_SIZE / 2
PIXEIS_MOVIMENTO = 90
LADO_MAIOR_AREA = ALTURA_JANELA / 3
LADO_MENOR_AREA = 50
RAIO_MEIO_CAMPO = LADO_MAIOR_AREA / 4
START_POS_BALIZAS = ALTURA_JANELA / 4 -50
POSTES = 100
BOLA_START_POS = (5,5)


# Funções responsáveis pelo movimento dos jogadores no ambiente. 
# O número de unidades que o jogador se pode movimentar é definida pela constante 
# PIXEIS_MOVIMENTO. As funções recebem um dicionário que contém o estado 
# do jogo e o jogador que se está a movimentar. 

def jogador_cima(estado_jogo, jogador):
    coordenadas = estado_jogo[jogador].ycor() + RAIO_JOGADOR
    if coordenadas < (METADE_ALTURA_JANELA - RAIO_JOGADOR) and coordenadas + PIXEIS_MOVIMENTO <= METADE_ALTURA_JANELA:
        estado_jogo[jogador].setheading(90)
        estado_jogo[jogador].fd(PIXEIS_MOVIMENTO)

def jogador_baixo(estado_jogo, jogador):
    coordenadas = estado_jogo[jogador].ycor() - RAIO_JOGADOR
    if coordenadas > -(METADE_ALTURA_JANELA - RAIO_JOGADOR) and coordenadas - PIXEIS_MOVIMENTO >= (-METADE_ALTURA_JANELA):
        estado_jogo[jogador].setheading(270)
        estado_jogo[jogador].fd(PIXEIS_MOVIMENTO)
    
def jogador_direita(estado_jogo, jogador):
    coordenadas = estado_jogo[jogador].xcor() + RAIO_JOGADOR
    if coordenadas < (METADE_LARGURA_JANELA - RAIO_JOGADOR) and  coordenadas + PIXEIS_MOVIMENTO <= (METADE_LARGURA_JANELA):
        estado_jogo[jogador].setheading(0)
        estado_jogo[jogador].fd(PIXEIS_MOVIMENTO)
    elif coordenadas + PIXEIS_MOVIMENTO > (METADE_LARGURA_JANELA):
        estado_jogo[jogador].fd(METADE_LARGURA_JANELA-coordenadas-RAIO_JOGADOR)

def jogador_esquerda(estado_jogo, jogador):
    coordenadas = estado_jogo[jogador].xcor() + RAIO_JOGADOR
    if coordenadas > -(METADE_LARGURA_JANELA - RAIO_JOGADOR) and coordenadas - PIXEIS_MOVIMENTO >= -(METADE_LARGURA_JANELA):
        estado_jogo[jogador].setheading(180)
        estado_jogo[jogador].fd(PIXEIS_MOVIMENTO)
    elif coordenadas - PIXEIS_MOVIMENTO < -(METADE_LARGURA_JANELA):
        estado_jogo[jogador].fd(METADE_LARGURA_JANELA+coordenadas-(2*RAIO_JOGADOR))

def movimenta_jogador_ia(estado_jogo):
    if estado_jogo["mover_ai"]:
        bola_x, bola_y = estado_jogo["bola"]["objeto"].pos()
        jogador_azul_x, jogador_azul_y = estado_jogo["jogador_azul"].pos()

        distancia_minima = 50
        velocidade_ia = 1.0

        limite_superior_ia = METADE_ALTURA_JANELA - RAIO_JOGADOR
        limite_inferior_ia = -METADE_ALTURA_JANELA + RAIO_JOGADOR

        if bola_x > 0:
            distancia = ((jogador_azul_x - bola_x)**2 + (jogador_azul_y - bola_y)**2)**0.5

            if distancia > distancia_minima:
                novo_y = jogador_azul_y + velocidade_ia * (bola_y - jogador_azul_y)
                novo_y = max(limite_inferior_ia, min(novo_y, limite_superior_ia))
                estado_jogo["jogador_azul"].sety(novo_y)

def desenha_linhas_campo():
    ''' Função responsável por desenhar as linhas do campo, 
    nomeadamente a linha de meio campo, o círculo central, e as balizas. '''

    def area():
        for _ in range(4):
            linhas.fd(LADO_MENOR_AREA)
            linhas.left(90)
            linhas.fd(LADO_MAIOR_AREA)
            linhas.left(90)

    linhas = t.Turtle()
    linhas.hideturtle()
    linhas.penup()
    linhas.speed(0)
    linhas.color("white")
    linhas.pensize(6)
    linhas.setpos(BOLA_START_POS)
    linhas.pendown()
    linhas.goto(5,ALTURA_JANELA)
    linhas.goto(5,-ALTURA_JANELA)
    linhas.goto(5,-RAIO_MEIO_CAMPO)
    linhas.circle(RAIO_MEIO_CAMPO)
    linhas.penup()
    linhas.goto(-METADE_LARGURA_JANELA,-100)
    linhas.pendown()
    area()
    linhas.penup()
    linhas.goto(METADE_LARGURA_JANELA, 100)
    linhas.setheading(180)
    linhas.pendown()
    area()
    

def criar_bola():
    '''
    Função responsável pela criação da bola. 
    Deverá considerar que esta tem uma forma redonda, é de cor preta, 
    começa na posição BOLA_START_POS com uma direção aleatória. 
    Deverá ter em conta que a velocidade da bola deverá ser superior à dos jogadores. 
    A função deverá devolver um dicionário contendo 4 elementos: o objeto bola, 
    a sua direção no eixo dos xx, a sua direção no eixo dos yy, 
    e um elemento inicialmente a None que corresponde à posição anterior da mesma.
    '''
    bola = t.Turtle()
    bola.speed(0)
    bola.shape("circle")
    bola.color("black")
    bola.penup()
    bola.setpos(BOLA_START_POS)
    bola.pensize(RAIO_BOLA)

    direcao_x = random.uniform(-0.5,0.3)
    direcao_y = random.uniform(-0.5,0.3)

    
    info = {"objeto": bola, "direcao_x": direcao_x, "direcao_y": direcao_y, "posicao": None}

    return info


def cria_jogador(x_pos_inicial, y_pos_inicial, cor):
    ''' Função responsável por criar e devolver o objeto que corresponde a um jogador (um objecto Turtle). 
    A função recebe 3 argumentos que correspondem às coordenadas da posição inicial 
    em xx e yy, e a cor do jogador. A forma dos jogadores deverá ser um círculo, 
    cujo seu tamanho deverá ser definido através da função shapesize
    do módulo \texttt{turtle}, usando os seguintes parâmetros: 
    stretch_wid=DEFAULT_TURTLE_SCALE, stretch_len=DEFAULT_TURTLE_SCALE. '''
    
    jogador = t.Turtle()
    jogador.penup()
    jogador.color(cor)
    jogador.shape("circle")
    jogador.shapesize(stretch_wid=DEFAULT_TURTLE_SCALE, stretch_len= DEFAULT_TURTLE_SCALE)
    jogador.setposition(x_pos_inicial, y_pos_inicial)


    return jogador


def init_state():
    estado_jogo = {}
    estado_jogo['bola'] = None
    estado_jogo['jogador_vermelho'] = None
    estado_jogo['jogador_azul'] = None
    estado_jogo['var'] = {
        'bola' : [],
        'jogador_vermelho' : [],
        'jogador_azul' : [],
    }
    estado_jogo['pontuacao_jogador_vermelho'] = 0
    estado_jogo['pontuacao_jogador_azul'] = 0
    return estado_jogo

def cria_janela():
    #create a window and declare a variable called window and call the screen()
    window=t.Screen()
    window.title("Foosball Game")
    window.bgcolor("green")
    window.setup(width = LARGURA_JANELA,height = ALTURA_JANELA)
    window.tracer(0)
    return window

def cria_quadro_resultados():
    #Code for creating pen for scorecard update
    quadro=t.Turtle()
    quadro.speed(0)
    quadro.color("Blue")
    quadro.penup()
    quadro.hideturtle()
    quadro.goto(0,260)
    quadro.write("BENFICA: 0\tPORTO: 0 ", align="center", font=('Monaco',16,"normal"))
    return quadro


def terminar_jogo(estado_jogo):
    '''
     Função responsável por terminar o jogo. Nesta função, deverá atualizar o ficheiro 
     ''historico_resultados.csv'' com o número total de jogos até ao momento, 
     e o resultado final do jogo. Caso o ficheiro não exista, 
     ele deverá ser criado com o seguinte cabeçalho: 
     NJogo,JogadorVermelho,JogadorAzul.
    '''
    with open("historico_resultados.csv", "a+") as terminar:
        terminar.seek(0)
        if terminar.readline() == "":
            terminar.write("NJogo\tJogadorVermelho\tJogadorAzul\n")
            terminar.write("%d\t\t%d\t\t\t\t%d\n" %(1, estado_jogo["pontuacao_jogador_vermelho"], estado_jogo["pontuacao_jogador_azul"]))
        elif terminar.readline != "":
            ultima = terminar.readlines()[-1]
            ultima_linha = ultima.strip()[0]
            terminar.write("%d\t\t%d\t\t\t\t%d\n" %(int(ultima_linha) + 1, estado_jogo["pontuacao_jogador_vermelho"], estado_jogo["pontuacao_jogador_azul"]))

    print("Adeus")
    estado_jogo['janela'].bye()

def setup(estado_jogo, jogar):
    janela = cria_janela()
    #Assign keys to play
    janela.listen()
    if jogar:
        janela.onkeypress(functools.partial(jogador_cima, estado_jogo, 'jogador_vermelho') ,'w')
        janela.onkeypress(functools.partial(jogador_baixo, estado_jogo, 'jogador_vermelho') ,'s')
        janela.onkeypress(functools.partial(jogador_esquerda, estado_jogo, 'jogador_vermelho') ,'a')
        janela.onkeypress(functools.partial(jogador_direita, estado_jogo, 'jogador_vermelho') ,'d')
        janela.onkeypress(functools.partial(jogador_cima, estado_jogo, 'jogador_azul') ,'Up')
        janela.onkeypress(functools.partial(jogador_baixo, estado_jogo, 'jogador_azul') ,'Down')
        janela.onkeypress(functools.partial(jogador_esquerda, estado_jogo, 'jogador_azul') ,'Left')
        janela.onkeypress(functools.partial(jogador_direita, estado_jogo, 'jogador_azul') ,'Right')
        janela.onkeypress(functools.partial(terminar_jogo, estado_jogo) ,'Escape')
        quadro = cria_quadro_resultados()
        estado_jogo['quadro'] = quadro
    desenha_linhas_campo()
    bola = criar_bola()
    jogador_vermelho = cria_jogador(-((ALTURA_JANELA / 2) + LADO_MENOR_AREA), 0, "red")
    jogador_azul = cria_jogador(((ALTURA_JANELA / 2) + LADO_MENOR_AREA), 0, "blue")
    estado_jogo['janela'] = janela
    estado_jogo['bola'] = bola
    estado_jogo['jogador_vermelho'] = jogador_vermelho
    estado_jogo['jogador_azul'] = jogador_azul


def update_board(estado_jogo):
    estado_jogo['quadro'].clear()
    estado_jogo['quadro'].write("BENFICA: {}\tPORTO: {} ".format(estado_jogo['pontuacao_jogador_vermelho'], estado_jogo['pontuacao_jogador_azul']),align="center",font=('Monaco',16,"normal"))

def movimenta_bola(estado_jogo):
    '''
    Função responsável pelo movimento da bola que deverá ser feito tendo em conta a
    posição atual da bola e a direção em xx e yy.
    '''
    dic = estado_jogo["bola"]
 
    dic["objeto"].goto(dic["objeto"].xcor() + estado_jogo["bola"]["direcao_x"], dic["objeto"].ycor() + estado_jogo["bola"]["direcao_y"])

    

def verifica_colisoes_ambiente(estado_jogo):
    '''
    Função responsável por verificar se há colisões com os limites do ambiente, 
    atualizando a direção da bola. Não se esqueça de considerar que nas laterais, 
    fora da zona das balizas, a bola deverá inverter a direção onde atingiu o limite.
    '''
    coordenadas_x = estado_jogo["bola"]["objeto"].xcor()
    coordenadas_y = estado_jogo["bola"]["objeto"].ycor()

    if coordenadas_x >= METADE_LARGURA_JANELA:
        estado_jogo["bola"]["direcao_x"] *= -1
    elif coordenadas_x <= -METADE_LARGURA_JANELA:
        estado_jogo["bola"]["direcao_x"] *= -1
    elif coordenadas_y >= METADE_ALTURA_JANELA:
        estado_jogo["bola"]["direcao_y"] *= -1
    elif coordenadas_y <= -METADE_ALTURA_JANELA:
        estado_jogo["bola"]["direcao_y"] *= -1


def verifica_golo_jogador_vermelho(estado_jogo):
    '''
    Função responsável por verificar se um determinado jogador marcou golo. 
    Para fazer esta verificação poderá fazer uso das constantes: 
    LADO_MAIOR_AREA e 
    START_POS_BALIZAS. 
    Note que sempre que há um golo, deverá atualizar a pontuação do jogador, 
    criar um ficheiro que permita fazer a análise da jogada pelo VAR, 
    e reiniciar o jogo com a bola ao centro. 
    O ficheiro para o VAR deverá conter todas as informações necessárias 
    para repetir a jogada, usando as informações disponíveis no objeto 
    estado_jogo['var']. O ficheiro deverá ter o nome 
    
    replay_golo_jv_[TotalGolosJogadorVermelho]_ja_[TotalGolosJogadorAzul].txt 
    
    onde [TotalGolosJogadorVermelho], [TotalGolosJogadorAzul] 
    deverão ser substituídos pelo número de golos marcados pelo jogador vermelho 
    e azul, respectivamente. Este ficheiro deverá conter 3 linhas, estruturadas 
    da seguinte forma:
    Linha 1 - coordenadas da bola;
    Linha 2 - coordenadas do jogador vermelho;
    Linha 3 - coordenadas do jogador azul;
    
    Em cada linha, os valores de xx e yy das coordenadas são separados por uma 
    ',', e cada coordenada é separada por um ';'.
    '''
    bola_x = estado_jogo["bola"]["objeto"].xcor()
    bola_y = estado_jogo["bola"]["objeto"].ycor()

    if (bola_y > -POSTES+10) and (bola_y < POSTES-10) and (bola_x > METADE_LARGURA_JANELA - LADO_MENOR_AREA + 10):
        estado_jogo["pontuacao_jogador_vermelho"] += 1
        estado_jogo["bola"]["objeto"].setpos(BOLA_START_POS)
        estado_jogo["bola"]["direcao_x"] = random.uniform(-0.5,0.3)
        estado_jogo["bola"]["direcao_y"] = random.uniform(-0.5,0.3)
        estado_jogo["jogador_vermelho"].setpos(-(METADE_ALTURA_JANELA + LADO_MENOR_AREA), 0)
        estado_jogo["jogador_azul"].setpos((METADE_ALTURA_JANELA + LADO_MENOR_AREA), 0)
        update_board(estado_jogo)
        criar_replay(estado_jogo)


def verifica_golo_jogador_azul(estado_jogo):
    '''
    Função responsável por verificar se um determinado jogador marcou golo. 
    Para fazer esta verificação poderá fazer uso das constantes: 
    LADO_MAIOR_AREA e 
    START_POS_BALIZAS. 
    Note que sempre que há um golo, deverá atualizar a pontuação do jogador, 
    criar um ficheiro que permita fazer a análise da jogada pelo VAR, 
    e reiniciar o jogo com a bola ao centro. 
    O ficheiro para o VAR deverá conter todas as informações necessárias 
    para repetir a jogada, usando as informações disponíveis no objeto 
    estado_jogo['var']. O ficheiro deverá ter o nome 
    
    replay_golo_jv_[TotalGolosJogadorVermelho]_ja_[TotalGolosJogadorAzul].txt 
    
    onde [TotalGolosJogadorVermelho], [TotalGolosJogadorAzul] 
    deverão ser substituídos pelo número de golos marcados pelo jogador vermelho 
    e azul, respectivamente. Este ficheiro deverá conter 3 linhas, estruturadas 
    da seguinte forma:
    Linha 1 - coordenadas da bola;
    Linha 2 - coordenadas do jogador vermelho;
    Linha 3 - coordenadas do jogador azul;
    
    Em cada linha, os valores de xx e yy das coordenadas são separados por uma 
    ',', e cada coordenada é separada por um ';'.
    '''
    bola_x = estado_jogo["bola"]["objeto"].xcor()
    bola_y = estado_jogo["bola"]["objeto"].ycor()

    if (bola_y > -POSTES+10) and (bola_y < POSTES-10) and (bola_x < -METADE_LARGURA_JANELA + LADO_MENOR_AREA - 10):
        estado_jogo["pontuacao_jogador_azul"]  += 1
        estado_jogo["bola"]["objeto"].setpos(BOLA_START_POS)
        estado_jogo["bola"]["direcao_x"] = random.uniform(-0.5,0.3)
        estado_jogo["bola"]["direcao_y"] = random.uniform(-0.5,0.3)
        estado_jogo["jogador_azul"].setpos((METADE_ALTURA_JANELA + LADO_MENOR_AREA), 0)
        estado_jogo["jogador_vermelho"].setpos(-(METADE_ALTURA_JANELA + LADO_MENOR_AREA), 0)
        update_board(estado_jogo)

        criar_replay(estado_jogo)
        

def verifica_golos(estado_jogo):
    verifica_golo_jogador_vermelho(estado_jogo)
    verifica_golo_jogador_azul(estado_jogo)


def verifica_toque_jogador_azul(estado_jogo):
    '''
    Função responsável por verificar se o jogador tocou na bola. 
    Sempre que um jogador toca na bola, deverá mudar a direção desta.
    '''
    x_cor = estado_jogo["jogador_azul"].xcor()
    y_cor = estado_jogo["jogador_azul"].ycor()
    bola_x = estado_jogo["bola"]["objeto"].xcor()
    bola_y = estado_jogo["bola"]["objeto"].ycor()

    distancia = ((x_cor - bola_x)**2 + (y_cor - bola_y)**2)**0.5
    raios = (RAIO_BOLA + RAIO_JOGADOR)

    if distancia <= raios and x_cor * estado_jogo["bola"]["direcao_x"] > bola_x * estado_jogo["bola"]["direcao_x"]:
        estado_jogo["bola"]["direcao_x"] *= -1
        estado_jogo["bola"]["direcao_y"] *= -1
    


def verifica_toque_jogador_vermelho(estado_jogo):
    '''
    Função responsável por verificar se o jogador tocou na bola. 
    Sempre que um jogador toca na bola, deverá mudar a direção desta.
    '''
    x_cor = estado_jogo["jogador_vermelho"].xcor()
    y_cor = estado_jogo["jogador_vermelho"].ycor()
    bola_x = estado_jogo["bola"]["objeto"].xcor()
    bola_y = estado_jogo["bola"]["objeto"].ycor()

    distancia = ((x_cor - bola_x)**2 + (y_cor - bola_y)**2)**0.5    
    raios = RAIO_BOLA + RAIO_JOGADOR

    if distancia <= raios and x_cor * estado_jogo["bola"]["direcao_x"] > bola_x * estado_jogo["bola"]["direcao_x"]:
        estado_jogo["bola"]["direcao_x"] *= -1
        estado_jogo["bola"]["direcao_y"] *= -1
    

def guarda_posicoes_para_var(estado_jogo):
    estado_jogo['var']['bola'].append(estado_jogo['bola']['objeto'].pos())
    estado_jogo['var']['jogador_vermelho'].append(estado_jogo['jogador_vermelho'].pos())
    estado_jogo['var']['jogador_azul'].append(estado_jogo['jogador_azul'].pos())


def criar_replay(estado_jogo):
    with open("replay_golo_jv_%d_ja_%d.txt" %(estado_jogo["pontuacao_jogador_vermelho"], estado_jogo["pontuacao_jogador_azul"]), "w") as ficheiro:
            ficheiro.write(";".join(str(coord) for coord in estado_jogo["var"]["bola"]).replace("(","").replace(")",""))
            ficheiro.write("\n")

            ficheiro.write(";".join(str(coord) for coord in estado_jogo["var"]["jogador_vermelho"]).replace("(","").replace(")",""))
            ficheiro.write("\n")

            ficheiro.write(";".join(str(coord) for coord in estado_jogo["var"]["jogador_azul"]).replace("(","").replace(")",""))
            ficheiro.write("\n")

    estado_jogo["var"]["bola"].clear()
    estado_jogo["var"]["jogador_vermelho"].clear()
    estado_jogo["var"]["jogador_azul"].clear()


def main():
    estado_jogo = init_state()
    setup(estado_jogo, True)
    estado_jogo["mover_ai"] = True
    while True:
        estado_jogo['janela'].update()
        if estado_jogo['bola'] is not None:
            movimenta_bola(estado_jogo)
            movimenta_jogador_ia(estado_jogo)
        verifica_colisoes_ambiente(estado_jogo)
        verifica_golos(estado_jogo)
        if estado_jogo['jogador_vermelho'] is not None:
            verifica_toque_jogador_azul(estado_jogo)
        if estado_jogo['jogador_azul'] is not None:
            verifica_toque_jogador_vermelho(estado_jogo)
        guarda_posicoes_para_var(estado_jogo)
        

if __name__ == '__main__':
    main()