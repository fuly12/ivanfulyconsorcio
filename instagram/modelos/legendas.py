import json, os, sys
S = sys.argv[1]
B = "Me chama no WhatsApp pelo link na bio. 📲"
P = [
 ("2026-10-16T20:00", "v1_sex-16-out_20h_chave-da-sua-casa.mp4",
  "Todo mês, o aluguel vai embora. 🏠\n\nE se esse dinheiro virasse a SUA casa? Imagina a chave na sua mão, um lugar que é seu de verdade.\n\nCom consórcio você conquista sem juros, com parcela que cabe no seu mês e sem entrada obrigatória.\n\nMe conta o seu sonho que eu te mostro o caminho. 📲 Link na bio.\n\n#casapropria #consorcio #consorcioimobiliario #sonho #riodejaneiro #reels"),
 ("2026-10-17T12:00", "01_sab-17-out_12h_chave-da-casa.png",
  "Imagina a chave da SUA casa na mão. 🔑\n\nSem aluguel, sem dono batendo na porta. Um lugar pra chamar de seu, do seu jeito.\n\nEsse sonho tem caminho: consórcio imobiliário, sem juros e com parcela que cabe no seu mês.\n\nMe chama no WhatsApp pelo link na bio que eu te mostro como. 📲\n\n#casapropria #consorcioimobiliario #sonhodacasapropria #consorcio #riodejaneiro"),
 ("2026-10-17T19:00", "02_sab-17-out_19h_qual-seu-sonho.png",
  "Qual é o seu sonho? 👇\n\n🏠 A casa própria?\n🚗 O carro novo?\n🏍️ A moto dos sonhos?\n\nComenta aqui embaixo! Eu respondo cada um e te mostro o caminho pra chegar lá. 💬\n\n#sonho #consorcio #casapropria #carronovo #motonova #riodejaneiro"),
 ("2026-10-17T20:00", "v2_sab-17-out_20h_carro-novo.mp4",
  "Fecha os olhos e imagina… 🚗\n\nVocê pegando a chave do seu carro novo. Cheiro de carro novo, a família no banco de trás e a estrada pela frente.\n\nEsse sonho tem caminho: parcela sem juros e compra à vista quando você for contemplado.\n\nMe conta qual é o carro dos seus sonhos! 📲 Link na bio.\n\n#carronovo #consorciodeveiculos #consorcio #sonho #reels #rj"),
 ("2026-10-18T12:00", "03_dom-18-out_12h_carro-da-vitrine.png",
  "Aquele carro que você para pra olhar toda vez que passa… 👀🚗\n\nEle pode sair da vitrine e ir pra sua garagem. O segredo é ter um plano.\n\nCom consórcio: sem juros, sem entrada obrigatória e compra à vista quando for contemplado.\n\nQual é o carro? Me conta nos comentários! 👇\n\n#carronovo #consorciodeveiculos #consorcio #sonho #riodejaneiro"),
 ("2026-10-18T19:00", "04_dom-18-out_19h_parcela-sem-juros.png",
  "Seu sonho cabe numa parcela sem juros. ✅\n\nNo consórcio, você escolhe a parcela que cabe no seu mês e conquista sem pagar juros. É planejamento que respeita o seu bolso.\n\nQuer saber qual parcela cabe pra você? " + B + "\n\n#consorcio #semjuros #planejamentofinanceiro #educacaofinanceira #rj"),
 ("2026-10-18T20:00", "v3_dom-18-out_20h_moto.mp4",
  "Sabe aquela moto que não sai da sua cabeça? 🏍️\n\nEla pode ser sua. Com consórcio você compra à vista, e pagando à vista você negocia desconto.\n\nSem juros, sem entrada obrigatória e com sorteio e lance todo mês.\n\nMe conta qual é a moto dos seus sonhos! 📲 Link na bio.\n\n#motonova #consorciodemoto #consorcio #sonho #reels #rj"),
 ("2026-10-19T12:00", "05_seg-19-out_12h_moto.png",
  "A moto que você vê na loja e pensa: um dia vai ser minha. 🏍️\n\nQue tal começar esse plano hoje? Com consórcio, você conquista sem juros e com parcela que cabe no seu mês.\n\nMe chama pelo link na bio que eu te mostro o caminho. 📲\n\n#motonova #consorcio #sonho #planejamento #riodejaneiro"),
 ("2026-10-19T19:00", "06_seg-19-out_19h_precisa-de-um-plano.png",
  "Você não precisa ter o dinheiro todo hoje. Precisa de um plano. 💡\n\nO consórcio transforma o sonho em parcelas mensais, sem juros e sem entrada obrigatória. Você conquista no seu ritmo.\n\nBora montar o seu plano? " + B + "\n\n#planejamentofinanceiro #consorcio #educacaofinanceira #sonho #rj"),
 ("2026-10-19T20:00", "v4_seg-19-out_20h_qual-e-o-seu-sonho.mp4",
  "Qual é o seu sonho? 🏠🚗🏍️\n\nCasa própria, carro novo ou a moto dos sonhos: todo sonho tem um caminho.\n\nComenta aqui o seu! Eu respondo e te mostro como chegar lá. 👇\n\n#sonho #consorcio #casapropria #carronovo #motonova #reels"),
 ("2026-10-20T12:00", "07_ter-20-out_12h_quintal-da-sua-casa.png",
  "Seu filho correndo no quintal da sua casa. 🏡❤️\n\nTem sonho que é da família inteira. E ele começa com o primeiro passo.\n\nO consórcio imobiliário é um caminho sem juros, com parcela que cabe no seu mês e com a possibilidade de usar o FGTS.\n\n" + B + "\n\n#casapropria #familia #consorcioimobiliario #sonho #riodejaneiro"),
 ("2026-10-20T19:00", "08_ter-20-out_19h_aluguel.png",
  "Todo mês você já paga por um sonho. Só que é o de outra pessoa. 🤔\n\nNo aluguel, o dinheiro vai embora todo mês. No consórcio, a parcela te leva até a sua casa.\n\nBora mudar isso? " + B + "\n\n#aluguel #casapropria #consorcioimobiliario #consorcio #educacaofinanceira"),
 ("2026-10-20T20:00", "v5_ter-20-out_20h_aluguel.mp4",
  "Quanto você já pagou de aluguel? 🏠\n\nTodo mês o dinheiro vai embora… e a casa continua sendo de outra pessoa.\n\nE se a parcela te levasse até a sua casa? No consórcio: sem juros, pode usar o FGTS e a parcela cabe no mês.\n\nMe conta o seu sonho que eu te mostro o caminho. 📲 Link na bio.\n\n#aluguel #casapropria #consorcioimobiliario #fgts #reels #rj"),
 ("2026-10-21T12:00", "09_qua-21-out_12h_primeira-viagem.png",
  "A primeira viagem com o carro novo. 🚗🛣️\n\nFamília no banco de trás, estrada pela frente e aquela sensação de conquista. Esse momento pode ser seu.\n\nCom consórcio de veículo: sem juros e compra à vista quando for contemplado.\n\n" + B + "\n\n#carronovo #viagememfamilia #consorciodeveiculos #sonho #rj"),
 ("2026-10-21T19:00", "10_qua-21-out_19h_sem-atalho-magico.png",
  "Seu sonho tem caminho. Não tem atalho mágico. ✅\n\n✔️ Contemplação por sorteio ou por lance\n✔️ Fiscalizado pelo Banco Central\n✔️ Regras claras, todas no contrato\n\nDesconfie de quem promete data de contemplação. Comigo você recebe o caminho real, com transparência.\n\n#consorcio #transparencia #confianca #bancocentral #educacaofinanceira"),
 ("2026-10-21T20:00", "v6_qua-21-out_20h_sonho-sem-juros.mp4",
  "Seu sonho, sem juros. 💰\n\nNo financiamento, os juros fazem você pagar bem mais. No consórcio, você paga a taxa de administração e zero juros.\n\nO custo total geralmente fica menor, e você fica mais perto do seu sonho.\n\nQuer comparar no seu caso? " + B + "\n\n#semjuros #consorcio #financiamento #educacaofinanceira #reels"),
 ("2026-10-22T12:00", "11_qui-22-out_12h_dinheiro-trabalhando.png",
  "Sonho também é ver o seu dinheiro trabalhando por você. 📈\n\nDepois de contemplado, você pode vender a carta e receber o que pagou, mais o ágio da venda.\n\n⚠️ O lucro só existe depois da contemplação, que não tem data garantida.\n\nQuer ver exemplos com números reais? " + B + "\n\n#investimento #consorcio #cartacontemplada #educacaofinanceira #rj"),
 ("2026-10-22T19:00", "12_qui-22-out_19h_me-conta-seu-sonho.png",
  "Me conta o seu sonho. Eu te mostro o caminho. 🤝\n\nCasa, carro, moto ou investimento: meu trabalho é montar com você um plano que caiba no seu bolso, com cada regra explicada antes de assinar.\n\nAtendimento no Rio e online, sem compromisso.\n\n👉 ivanfulyconsorcios.com.br (link na bio)\n\n#consorcio #sonho #ademicon #riodejaneiro #consultor"),
 ("2026-10-22T20:00", "v7_qui-22-out_20h_dia-da-contemplacao.mp4",
  "Sabe qual é o dia mais feliz do consórcio? 🎉\n\nO dia da contemplação! É quando a carta vira a chave do seu sonho.\n\nEu quero te ajudar a chegar nesse dia. Sem promessa de data, com planejamento de verdade.\n\nMe conta o seu sonho! 📲 Link na bio.\n\n#contemplacao #consorcio #sonhorealizado #casapropria #carronovo #reels"),
]
dias = {"16": "Sexta 16/10", "17": "Sábado 17/10", "18": "Domingo 18/10", "19": "Segunda 19/10", "20": "Terça 20/10", "21": "Quarta 21/10", "22": "Quinta 22/10"}
agenda, linhas = [], ["SEMANA DO SONHO · 16 a 22 de outubro de 2026", "Instagram @ivan_fuly · todo dia: imagem às 12h e às 19h, vídeo às 20h", "Sexta 16/10: só o vídeo das 20h (as imagens das 12h e 19h você já agendou).", ""]
for k, (quando, arq, leg) in enumerate(P, 1):
    video = arq.endswith(".mp4")
    assert leg.count("#") <= 30 and len(leg) < 2200
    agenda.append({"quando": quando + ":00-03:00", "arquivo": arq, "tipo": "video" if video else "imagem", "legenda": leg})
    linhas += ["=" * 50, f"{dias[quando[8:10]]} · {quando[11:16]} · {'VÍDEO (Reels)' if video else 'IMAGEM'}", f"Arquivo: {arq}", "-" * 50, leg, "-" * 50, ""]
json.dump(agenda, open(os.path.join(S, "semana-sonho.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
open(os.path.join(S, "LEGENDAS.txt"), "w", encoding="utf-8-sig", newline="\r\n").write("\n".join(linhas))
print(len(agenda), "posts;", sum(a["tipo"] == "video" for a in agenda), "vídeos;", max(len(a["legenda"]) for a in agenda), "caracteres na maior legenda")
