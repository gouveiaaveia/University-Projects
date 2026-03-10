import foosball_alunos

def le_replay(nome_ficheiro):
    '''
    Função que recebe o nome de um ficheiro contendo um replay, e que deverá 
    retornar um dicionário com as seguintes chaves:
    bola - lista contendo tuplos com as coordenadas xx e yy da bola
    jogador_vermelho - lista contendo tuplos com as coordenadas xx e yy da do jogador\_vermelho
    jogador_azul - lista contendo tuplos com as coordenadas xx e yy da do jogador\_azul
    '''        
    try:
        with open(nome_ficheiro, "r") as ficheiro:
            dicionario = {"bola": [], "jogador_vermelho": [], "jogador_azul": []}

            ler = ficheiro.readline().strip().split(";")
            ler_2 = ficheiro.readline().strip().split(";")
            ler_3 = ficheiro.readline().strip().split(";")

            for cord in ler:
                cordenadas = tuple(cord.split(","))
                dicionario["bola"].append((float(cordenadas[0]), float(cordenadas[1])))   

            for cord in ler_2:
                cordenadas = tuple(cord.split(","))
                dicionario["jogador_vermelho"].append((float(cordenadas[0]), float(cordenadas[1])))  
            
            for cord in ler_3:
                cordenadas = tuple(cord.split(","))
                dicionario["jogador_azul"].append((float(cordenadas[0]), float(cordenadas[1])))

        return dicionario

    except Exception as e:
        print(f"Erro ao ler replay: {nome_ficheiro}")
        return None


def main():
    estado_jogo = foosball_alunos.init_state()
    foosball_alunos.setup(estado_jogo, False)
    replay = le_replay('replay_golo_jv_10_ja_1.txt')
    for i in range(len(replay['bola'])):
        estado_jogo['janela'].update()
        estado_jogo['jogador_vermelho'].setpos(replay['jogador_vermelho'][i])
        estado_jogo['jogador_azul'].setpos(replay['jogador_azul'][i])
        estado_jogo['bola']['objeto'].setpos(replay['bola'][i])
    estado_jogo['janela'].exitonclick()


if __name__ == '__main__':
    main()